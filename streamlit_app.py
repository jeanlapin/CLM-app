from __future__ import annotations

from pathlib import Path
from io import BytesIO
from datetime import datetime, timezone
import json
import re
import hmac
import shutil

import numpy as np
import pandas as pd
import streamlit as st

PAGE_TITLE = "Tableau 1 – Portefeuille multi-société"
SOC_COL = "societe_id"
USERS_FILE = "users.csv"
DATA_FILES = {
    "base": "01_Donnees_base_source.csv",
    "indicators": "02_Indicateurs_source.csv",
    "history": "03_Indicateurs_historique.csv",
}
KEY_COLUMNS = [SOC_COL, "SIREN"]
STORAGE_ROOT = ".app_storage"
ACTIVE_DATASET_DIR = "active_dataset"
MANIFEST_FILE = "manifest.json"

VIGILANCE_ORDER = [
    "Vigilance Critique",
    "Vigilance Élevée",
    "Vigilance Modérée",
    "Vigilance Allégée",
    "Vigilance Aucune",
]

RISK_ORDER = [
    "Risque avéré",
    "Risque potentiel",
    "Risque mitigé",
    "Risque levé",
    "Non calculable",
    "Aucun risque détecté",
]

CRITICAL_VIGILANCE = {"Vigilance Élevée", "Vigilance Critique"}
PRIORITY_RISK = {"Risque potentiel", "Risque avéré"}

FILTER_MAPPING = {
    "Segment": "Segment",
    "Pays": "Pays de résidence",
    "Produit": "Produit(service) principal",
    "Canal": "Canal d’opérations principal 12 mois",
    "Vigilance": "Vigilance",
    "Risque": "Risque",
    "EDD": "Statut EDD",
    "Analyste": "Analyste",
    "Valideur": "Valideur",
}

DISPLAY_COLUMNS = [
    SOC_COL,
    "SIREN",
    "Dénomination",
    "Pays de résidence",
    "Segment",
    "Produit(service) principal",
    "Canal d’opérations principal 12 mois",
    "Vigilance",
    "Risque",
    "Statut EDD",
    "Flag justificatif complet",
    "Analyste",
    "Valideur",
    "Date dernière revue",
    "Date prochaine revue",
    "Vigilance Date de mise à jour",
    "Nb historique",
    "Score priorité",
    "Motifs",
]

REQUIRED_COLUMNS = {
    "base": [SOC_COL, "SIREN", "Dénomination"],
    "indicators": [SOC_COL, "SIREN", "Vigilance statut", "Vigilance Date de mise à jour"],
    "history": [SOC_COL, "SIREN"],
    "users": ["username", "password", "role", "societes_autorisees", "enabled"],
}


class DataValidationError(ValueError):
    pass


class NoPublishedDatasetError(FileNotFoundError):
    pass


def app_root() -> Path:
    return Path(__file__).resolve().parent


def storage_root() -> Path:
    root = app_root() / STORAGE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


def active_dataset_path() -> Path:
    return storage_root() / ACTIVE_DATASET_DIR


def manifest_path() -> Path:
    return active_dataset_path() / MANIFEST_FILE


def find_file(filename: str) -> Path:
    here = app_root()
    candidates = [
        here / filename,
        here / "data" / filename,
        Path.cwd() / filename,
        Path.cwd() / "data" / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    searched = "\n - ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"Impossible de trouver {filename}. Emplacements testés :\n - {searched}")


def read_csv_semicolon(source) -> pd.DataFrame:
    return pd.read_csv(source, sep=";", encoding="utf-8-sig").dropna(how="all")


def normalize_siren(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\\.0$", "", regex=True)
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )


def normalize_societe_id(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.upper()
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )


def clean_text_column(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
        .astype("string")
    )


def parse_percent(value):
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "").replace(",", ".")
    if text == "":
        return np.nan
    try:
        return float(text) / 100.0
    except ValueError:
        return np.nan


def validate_required_columns(df: pd.DataFrame, label: str) -> None:
    missing = [col for col in REQUIRED_COLUMNS[label] if col not in df.columns]
    if missing:
        raise DataValidationError(
            f"Le fichier '{DATA_FILES.get(label, USERS_FILE)}' ne contient pas les colonnes obligatoires : {', '.join(missing)}. "
            f"Ajoutez notamment '{SOC_COL}' en première colonne dans 01, 02 et 03."
        )


@st.cache_data(show_spinner=False)
def load_users() -> pd.DataFrame:
    users = read_csv_semicolon(find_file(USERS_FILE))
    validate_required_columns(users, "users")
    users["username"] = users["username"].astype(str).str.strip().str.lower()
    users["password"] = users["password"].fillna("").astype(str)
    users["role"] = users["role"].astype(str).str.strip().str.lower()
    users["enabled"] = users["enabled"].astype(str).str.strip().str.lower().isin(["true", "1", "oui", "yes"])
    users["societes_autorisees"] = users["societes_autorisees"].fillna("").astype(str)
    if "display_name" not in users.columns:
        users["display_name"] = users["username"]
    else:
        users["display_name"] = users["display_name"].fillna(users["username"]).astype(str).str.strip()
        users.loc[users["display_name"].eq(""), "display_name"] = users["username"]
    return users


def parse_allowed_societies(raw_value: str) -> list[str]:
    raw = str(raw_value or "").strip()
    if not raw:
        return []
    if raw.upper() == "ALL":
        return ["ALL"]
    return sorted({item.strip().upper() for item in raw.split(",") if item.strip()})


def authenticate_user(username: str, password: str):
    users = load_users()
    username = str(username or "").strip().lower()
    row = users.loc[users["username"] == username]
    if row.empty:
        return None
    user = row.iloc[0]
    if not bool(user["enabled"]):
        return None
    if not hmac.compare_digest(str(password or ""), str(user["password"] or "")):
        return None
    return {
        "username": str(user["username"]),
        "display_name": str(user["display_name"]),
        "role": str(user["role"]),
        "societes_autorisees": parse_allowed_societies(user["societes_autorisees"]),
    }


def get_current_user():
    return st.session_state.get("authenticated_user")


def login_form() -> None:
    st.subheader("Connexion")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary")

    if submitted:
        user = authenticate_user(username, password)
        if user is None:
            st.error("Identifiants invalides ou compte désactivé.")
        else:
            st.session_state["authenticated_user"] = user
            st.rerun()

    st.info("Version simple : users.csv contient les mots de passe en clair. À utiliser sur un dépôt privé.")


def logout_button() -> None:
    if st.button("Se déconnecter"):
        st.session_state.pop("authenticated_user", None)
        st.rerun()


def parse_uploaded_dataset(uploaded_files: dict[str, object]) -> dict[str, pd.DataFrame]:
    parsed: dict[str, pd.DataFrame] = {}
    for label, expected_name in DATA_FILES.items():
        uploaded = uploaded_files.get(label)
        if uploaded is None:
            raise DataValidationError(f"Chargez le fichier {expected_name}.")
        df = read_csv_semicolon(BytesIO(uploaded.getvalue()))
        validate_required_columns(df, label)
        df[SOC_COL] = normalize_societe_id(df[SOC_COL])
        df["SIREN"] = normalize_siren(df["SIREN"])
        df = df.dropna(subset=KEY_COLUMNS).copy()
        if df.empty:
            raise DataValidationError(f"Le fichier {expected_name} ne contient aucune ligne exploitable après normalisation.")
        parsed[label] = df
    return parsed


def write_manifest(parsed: dict[str, pd.DataFrame], user: dict) -> dict:
    all_societies = sorted(
        {
            str(v).strip().upper()
            for df in parsed.values()
            for v in df[SOC_COL].dropna().astype(str)
            if str(v).strip()
        }
    )
    return {
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "published_by": user["username"],
        "published_by_name": user["display_name"],
        "files": {label: DATA_FILES[label] for label in DATA_FILES},
        "row_counts": {label: int(len(df)) for label, df in parsed.items()},
        "societes": all_societies,
        "societes_count": len(all_societies),
    }


def publish_uploaded_dataset(uploaded_files: dict[str, object], user: dict) -> None:
    parsed = parse_uploaded_dataset(uploaded_files)

    root = storage_root()
    temp_dir = root / f"_tmp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    current_dir = active_dataset_path()
    backup_dir = root / "_backup_active"

    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    temp_dir.mkdir(parents=True, exist_ok=False)

    try:
        for label, expected_name in DATA_FILES.items():
            uploaded = uploaded_files[label]
            (temp_dir / expected_name).write_bytes(uploaded.getvalue())

        manifest = write_manifest(parsed, user)
        (temp_dir / MANIFEST_FILE).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        if current_dir.exists():
            current_dir.replace(backup_dir)
        temp_dir.replace(current_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if backup_dir.exists() and not current_dir.exists():
            backup_dir.replace(current_dir)
        raise


def clear_published_dataset() -> None:
    current_dir = active_dataset_path()
    if current_dir.exists():
        shutil.rmtree(current_dir)


def load_manifest() -> dict | None:
    path = manifest_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    current_dir = active_dataset_path()
    if not current_dir.exists():
        raise NoPublishedDatasetError(
            "Aucun jeu de données publié. Connectez-vous avec un compte admin puis chargez les 3 fichiers CSV depuis la barre latérale."
        )

    def _read(label: str) -> pd.DataFrame:
        path = current_dir / DATA_FILES[label]
        if not path.exists():
            raise NoPublishedDatasetError(
                "Jeu de données incomplet côté serveur. Republiez les 3 fichiers 01, 02 et 03 depuis un compte admin."
            )
        return read_csv_semicolon(path)

    base = _read("base")
    indicators = _read("indicators")
    history = _read("history")

    validate_required_columns(base, "base")
    validate_required_columns(indicators, "indicators")
    validate_required_columns(history, "history")

    for df in (base, indicators, history):
        df[SOC_COL] = normalize_societe_id(df[SOC_COL])
        df["SIREN"] = normalize_siren(df["SIREN"])
        df.dropna(subset=KEY_COLUMNS, inplace=True)

    base = base.drop_duplicates(subset=KEY_COLUMNS, keep="first").copy()
    indicators = indicators.drop_duplicates(subset=KEY_COLUMNS, keep="first").copy()

    for col in [
        "Cross border",
        "Cash intensité",
        "Part des opérations à distance 12 mois",
        "Part des opérations avec produits(services) hauts risques 12 mois",
    ]:
        if col in base.columns:
            base[col] = base[col].apply(parse_percent)

    for col in ["Date dernière revue", "Date prochaine revue"]:
        if col in base.columns:
            base[col] = pd.to_datetime(base[col], errors="coerce")

    for col in indicators.columns:
        if "Date de mise à jour" in col:
            indicators[col] = pd.to_datetime(indicators[col], errors="coerce")

    for frame, columns in [
        (
            base,
            [
                "Dénomination",
                "Pays de résidence",
                "Segment",
                "Produit(service) principal",
                "Canal d’opérations principal 12 mois",
                "Statut EDD",
                "Flag justificatif complet",
                "Analyste",
                "Valideur",
                "Statut de risque (import SaaS source)",
            ],
        ),
        (indicators, ["Vigilance statut", "Cash intensité Statut"]),
    ]:
        for col in columns:
            if col in frame.columns:
                frame[col] = clean_text_column(frame[col])

    return base, indicators, history


def status_columns(indicators_df: pd.DataFrame) -> list[str]:
    cols = [c for c in indicators_df.columns if re.search(r"(?i)\\bstatut\\b", c)]
    return [c for c in cols if c != "Vigilance statut"]


def build_portfolio_dataset() -> pd.DataFrame:
    base, indicators, history = load_source_data()

    ind_status_cols = status_columns(indicators)
    indicator_cols = [
        SOC_COL,
        "SIREN",
        "Vigilance statut",
        "Vigilance valeur",
        "Vigilance Date de mise à jour",
        "Cash intensité Statut",
    ] + ind_status_cols
    indicator_cols = list(dict.fromkeys([c for c in indicator_cols if c in indicators.columns]))

    portfolio = base.merge(indicators[indicator_cols], how="left", on=KEY_COLUMNS)
    history_count = history.groupby(KEY_COLUMNS).size().rename("Nb historique").reset_index()
    portfolio = portfolio.merge(history_count, how="left", on=KEY_COLUMNS)
    portfolio["Nb historique"] = portfolio["Nb historique"].fillna(0).astype(int)

    portfolio["Vigilance"] = portfolio.get("Vigilance statut")
    portfolio["Risque"] = portfolio.get("Statut de risque (import SaaS source)")

    for label in ["Risque avéré", "Risque potentiel", "Risque mitigé", "Risque levé", "Non calculable"]:
        portfolio[f"Nb {label}"] = portfolio[ind_status_cols].eq(label).sum(axis=1) if ind_status_cols else 0

    today = pd.Timestamp.today().normalize()
    portfolio["Alerte justificatif incomplet"] = (
        (portfolio.get("Flag justificatif complet") != "Oui")
        & (portfolio["Vigilance"].isin(CRITICAL_VIGILANCE))
    ).astype(int)
    portfolio["Alerte vigilance critique"] = (portfolio["Vigilance"] == "Vigilance Critique").astype(int)
    portfolio["Alerte revue trop ancienne"] = (
        portfolio["Vigilance"].isin(CRITICAL_VIGILANCE)
        & portfolio.get("Date dernière revue", pd.Series(index=portfolio.index, dtype="datetime64[ns]")).notna()
        & ((today - portfolio["Date dernière revue"]).dt.days > 90)
    ).astype(int)
    portfolio["Alerte sans prochaine revue"] = portfolio.get(
        "Date prochaine revue", pd.Series(index=portfolio.index, dtype="datetime64[ns]")
    ).isna().astype(int)
    portfolio["Alerte cross-border élevé"] = portfolio.get(
        "Cross border", pd.Series(index=portfolio.index, dtype="float64")
    ).ge(0.25).fillna(False).astype(int)
    portfolio["Alerte cash intensité élevée"] = (
        portfolio.get("Cash intensité Statut", pd.Series(index=portfolio.index, dtype="string"))
        .isin(PRIORITY_RISK)
        .astype(int)
    )

    portfolio["Score priorité"] = (
        25 * (portfolio["Vigilance"] == "Vigilance Critique").astype(int)
        + 15 * (portfolio["Vigilance"] == "Vigilance Élevée").astype(int)
        + 20 * (portfolio["Risque"] == "Risque avéré").astype(int)
        + 10 * (portfolio["Risque"] == "Risque potentiel").astype(int)
        + 12 * portfolio["Alerte justificatif incomplet"]
        + 8 * portfolio["Alerte vigilance critique"]
        + 6 * portfolio["Alerte revue trop ancienne"]
        + 8 * portfolio["Alerte sans prochaine revue"]
        + 5 * portfolio["Alerte cross-border élevé"]
    )

    motifs = (
        np.where(portfolio["Alerte justificatif incomplet"].eq(1), "Justificatif incomplet ", "")
        + np.where(portfolio["Alerte vigilance critique"].eq(1), "Vigilance critique ", "")
        + np.where(portfolio["Alerte revue trop ancienne"].eq(1), "Revue trop ancienne ", "")
        + np.where(portfolio["Alerte sans prochaine revue"].eq(1), "Sans prochaine revue ", "")
        + np.where(portfolio["Alerte cross-border élevé"].eq(1), "Cross-border élevé ", "")
    )
    portfolio["Motifs"] = pd.Series(motifs, index=portfolio.index, dtype="string").str.strip()
    return portfolio


def non_empty_sorted(values) -> list[str]:
    return sorted({str(v).strip() for v in values if pd.notna(v) and str(v).strip()})


def available_societies(df: pd.DataFrame) -> list[str]:
    if SOC_COL not in df.columns:
        return []
    return non_empty_sorted(df[SOC_COL].unique())


def restrict_to_societies(df: pd.DataFrame, societies: list[str]) -> pd.DataFrame:
    normalized = {str(s).strip().upper() for s in societies if str(s).strip()}
    if not normalized:
        return df.iloc[0:0].copy()
    return df[df[SOC_COL].astype(str).str.upper().isin(normalized)].copy()


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = df.copy()
    for label, value in filters.items():
        if value == "Tous":
            continue
        result = result[result[FILTER_MAPPING[label]] == value]
    return result


def build_distribution(df: pd.DataFrame, column: str, order: list[str]) -> pd.DataFrame:
    counts = df[column].value_counts(dropna=False)
    total = len(df)
    rows = []
    for item in order:
        nb = int(counts.get(item, 0))
        rows.append({"Libellé": item, "Nb": nb, "%": (nb / total if total else 0.0)})
    return pd.DataFrame(rows)


def build_alert_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = [
        ("Justificatif incomplet", int(df["Alerte justificatif incomplet"].sum())),
        ("Vigilance critique", int(df["Alerte vigilance critique"].sum())),
        ("Revue trop ancienne", int(df["Alerte revue trop ancienne"].sum())),
        ("Sans prochaine revue", int(df["Alerte sans prochaine revue"].sum())),
        ("Cross-border élevé", int(df["Alerte cross-border élevé"].sum())),
        ("Cash intensité élevée", int(df["Alerte cash intensité élevée"].sum())),
    ]
    return pd.DataFrame(rows, columns=["Alerte", "Nb"])


def ranked_counts(df: pd.DataFrame, column: str, top_n: int = 5) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=["Libellé", "Nb"])
    series = df[column].dropna().astype(str).str.strip()
    series = series[series.ne("")]
    if series.empty:
        return pd.DataFrame(columns=["Libellé", "Nb"])
    return (
        series.value_counts()
        .rename_axis("Libellé")
        .reset_index(name="Nb")
        .sort_values(["Nb", "Libellé"], ascending=[False, True], kind="stable")
        .head(top_n)
        .reset_index(drop=True)
    )


def build_priority_table(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    priority = (
        df.sort_values(["Score priorité", SOC_COL, "SIREN"], ascending=[False, True, False], kind="stable")
        .head(top_n)
        .copy()
    )
    priority.insert(0, "#", range(1, len(priority) + 1))
    columns = [
        "#",
        SOC_COL,
        "Dénomination",
        "SIREN",
        "Pays de résidence",
        "Segment",
        "Vigilance",
        "Risque",
        "Statut EDD",
        "Analyste",
        "Motifs",
        "Score priorité",
    ]
    columns = [c for c in columns if c in priority.columns]
    return priority[columns].rename(
        columns={
            SOC_COL: "Société",
            "Dénomination": "Client",
            "Pays de résidence": "Pays",
            "Statut EDD": "EDD",
            "Score priorité": "Score",
        }
    )


def format_percent_column(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    if "%" in output.columns:
        output["%"] = output["%"].map(lambda x: f"{x:.1%}")
    return output


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    export = df.copy()
    for col in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[col]):
            export[col] = export[col].dt.strftime("%Y-%m-%d")
    return export.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")


def reset_filters() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("filter_"):
            st.session_state[key] = "Tous"


def format_manifest_date(value: str | None) -> str:
    if not value:
        return "inconnue"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(value)


def render_admin_data_manager(user: dict) -> None:
    if user["role"] != "admin":
        return

    manifest = load_manifest()
    with st.sidebar.expander("Administration des données", expanded=False):
        if manifest:
            st.success(
                "Jeu actif : publié le {} par {}.".format(
                    format_manifest_date(manifest.get("published_at_utc")),
                    manifest.get("published_by_name") or manifest.get("published_by") or "inconnu",
                )
            )
            st.caption(
                "Sociétés : {} | Lignes 01/02/03 : {}/{}/{}".format(
                    manifest.get("societes_count", 0),
                    manifest.get("row_counts", {}).get("base", 0),
                    manifest.get("row_counts", {}).get("indicators", 0),
                    manifest.get("row_counts", {}).get("history", 0),
                )
            )
        else:
            st.warning("Aucun jeu de données publié pour le moment.")

        st.markdown("**Publier un nouveau jeu de données**")
        upload_base = st.file_uploader(
            "01_Donnees_base_source.csv",
            type=["csv"],
            key="admin_upload_base",
        )
        upload_indicators = st.file_uploader(
            "02_Indicateurs_source.csv",
            type=["csv"],
            key="admin_upload_indicators",
        )
        upload_history = st.file_uploader(
            "03_Indicateurs_historique.csv",
            type=["csv"],
            key="admin_upload_history",
        )

        if st.button("Publier ces 3 fichiers", type="primary", key="publish_dataset"):
            try:
                publish_uploaded_dataset(
                    {
                        "base": upload_base,
                        "indicators": upload_indicators,
                        "history": upload_history,
                    },
                    user,
                )
                st.success("Le nouveau jeu de données est maintenant actif pour tous les utilisateurs.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        if manifest and st.button("Supprimer le jeu actif", type="secondary", key="clear_dataset"):
            clear_published_dataset()
            st.warning("Le jeu actif a été supprimé.")
            st.rerun()


def render_scope_selector(df: pd.DataFrame, user: dict):
    all_societies = available_societies(df)
    if user["role"] == "admin" or "ALL" in user["societes_autorisees"]:
        allowed = all_societies
    else:
        allowed = [s for s in all_societies if s in set(user["societes_autorisees"])]

    if not allowed:
        st.error("Votre compte ne possède aucun accès société correspondant aux données chargées.")
        st.stop()

    with st.sidebar:
        st.markdown("### Périmètre")
        selection = st.multiselect(
            "Sociétés visibles",
            options=allowed,
            default=allowed,
            key="selected_societies",
            help="Le tableau est calculé uniquement sur les sociétés sélectionnées parmi vos droits.",
        )

    if not selection:
        st.warning("Sélectionnez au moins une société pour afficher le tableau.")
        st.stop()

    return selection, allowed


def render_filters(df: pd.DataFrame) -> dict:
    st.subheader("Filtres")
    st.caption("Les filtres sont cumulatifs et recalculent tout le tableau.")

    if st.button("Réinitialiser les filtres", type="secondary"):
        reset_filters()

    row1 = st.columns(5)
    row2 = st.columns(4)
    labels = list(FILTER_MAPPING.keys())
    selections = {}

    for container, label in zip(row1 + row2, labels):
        column = FILTER_MAPPING[label]
        if column not in df.columns:
            options = ["Tous"]
        else:
            options = ["Tous"] + non_empty_sorted(df[column].unique())
        state_key = "filter_" + label
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with container:
            selections[label] = st.selectbox(label, options=options, key=state_key)
    return selections


def render_kpis(df: pd.DataFrame) -> None:
    st.subheader("Bandeau de synthèse")
    total = len(df)
    vigilance_renforcee = int(df["Vigilance"].isin(CRITICAL_VIGILANCE).sum()) if "Vigilance" in df.columns else 0
    risque_avere = int((df["Risque"] == "Risque avéré").sum()) if "Risque" in df.columns else 0
    justificatifs_incomplets = int(df["Alerte justificatif incomplet"].sum())
    sans_revue = int(df["Alerte sans prochaine revue"].sum())
    historique_disponible = int((df["Nb historique"] > 0).sum())

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Clients visibles", total)
    c2.metric("Vigilance renforcée", vigilance_renforcee)
    c3.metric("Risque avéré", risque_avere)
    c4.metric("Justificatifs incomplets", justificatifs_incomplets)
    c5.metric("Sans prochaine revue", sans_revue)
    c6.metric("Historique disponible", historique_disponible)

    if total and "Vigilance Date de mise à jour" in df.columns:
        last_update = df["Vigilance Date de mise à jour"].max()
        if pd.notna(last_update):
            st.caption("Fraîcheur visible : dernière mise à jour vigilance = {}.".format(last_update.strftime("%d/%m/%Y")))


def render_distribution_block(title: str, dist_df: pd.DataFrame, index_col: str) -> None:
    st.markdown("**{}**".format(title))
    st.bar_chart(dist_df.set_index(index_col)[["Nb"]], height=260)
    st.dataframe(format_percent_column(dist_df), hide_index=True, use_container_width=True)


def render_top_block(title: str, df: pd.DataFrame) -> None:
    st.markdown("**{}**".format(title))
    st.dataframe(df, hide_index=True, use_container_width=True)


def render_user_header(user: dict, selected_societies: list[str], total_societies: int) -> None:
    manifest = load_manifest()
    with st.sidebar:
        st.markdown("### Session")
        st.write("**Utilisateur :** {}".format(user["display_name"]))
        st.write("**Rôle :** {}".format(user["role"]))
        st.write("**Sociétés sélectionnées :** {} / {}".format(len(selected_societies), total_societies))
        if manifest:
            st.write(
                "**Jeu actif :** {}".format(
                    format_manifest_date(manifest.get("published_at_utc"))
                )
            )
        logout_button()


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.title(PAGE_TITLE)
    st.caption(
        "L’admin publie un jeu de données 01/02/03 ; tous les utilisateurs lisent ensuite ce jeu actif."
    )

    user = get_current_user()
    if user is None:
        login_form()
        return

    render_admin_data_manager(user)

    try:
        portfolio = build_portfolio_dataset()
    except NoPublishedDatasetError as exc:
        st.info(str(exc))
        return
    except (FileNotFoundError, DataValidationError, ValueError) as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error("Erreur inattendue au chargement des données : {}".format(exc))
        return

    selected_societies, allowed_societies = render_scope_selector(portfolio, user)
    scoped = restrict_to_societies(portfolio, selected_societies)
    render_user_header(user, selected_societies, len(allowed_societies))

    filters = render_filters(scoped)
    filtered = apply_filters(scoped, filters)

    if filtered.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    render_kpis(filtered)
    st.divider()

    col_left, col_mid, col_right = st.columns([1.15, 1.15, 1.0])
    with col_left:
        vigilance_df = build_distribution(filtered, "Vigilance", VIGILANCE_ORDER).rename(columns={"Libellé": "Vigilance"})
        render_distribution_block("Répartition par vigilance", vigilance_df, "Vigilance")

    with col_mid:
        risk_df = build_distribution(filtered, "Risque", RISK_ORDER).rename(columns={"Libellé": "Statut"})
        render_distribution_block("Répartition par statut de risque", risk_df, "Statut")

    with col_right:
        st.markdown("**Alertes de gouvernance**")
        st.dataframe(build_alert_table(filtered), hide_index=True, use_container_width=True, height=400)

    st.divider()
    st.subheader("Concentrations")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        render_top_block("Top segments", ranked_counts(filtered, "Segment"))
    with t2:
        render_top_block("Top pays", ranked_counts(filtered, "Pays de résidence"))
    with t3:
        render_top_block("Top produits", ranked_counts(filtered, "Produit(service) principal"))
    with t4:
        render_top_block("Top canaux", ranked_counts(filtered, "Canal d’opérations principal 12 mois"))

    st.divider()
    st.subheader("Dossiers prioritaires")
    st.dataframe(build_priority_table(filtered, top_n=10), hide_index=True, use_container_width=True, height=420)

    export_columns = [c for c in DISPLAY_COLUMNS if c in filtered.columns]
    st.download_button(
        label="Exporter la vue filtrée (.csv)",
        data=dataframe_to_csv_bytes(filtered[export_columns]),
        file_name="tableau1_portefeuille_filtre.csv",
        mime="text/csv",
        type="primary",
    )

    with st.expander("Aperçu des données sous-jacentes filtrées"):
        st.dataframe(filtered[export_columns], hide_index=True, use_container_width=True, height=420)


if __name__ == "__main__":
    main()
