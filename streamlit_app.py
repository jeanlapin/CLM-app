from __future__ import annotations

from pathlib import Path
from html import escape
import base64
from io import BytesIO
from datetime import datetime, timezone
import json
import re
import hmac
import shutil

import numpy as np
import pandas as pd
import streamlit as st

PAGE_TITLE = "CLASSIFICATION MANAGEMENT"
APP_SUBTITLE = "Pilotage du portefeuille, gouvernance des risques et supervision multi-société"
PRIMARY_COLOR = "#163A59"
SECONDARY_COLOR = "#5E8FC7"
ACCENT_COLOR = "#DDEAF8"
CARD_BACKGROUND = "#F5F9FE"
LOGO_DATA_URI = "data:image/png;base64,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"
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



def inject_brand_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&family=Cormorant+Garamond:wght@500;600;700&display=swap');

        :root {{
            --cm-primary: {PRIMARY_COLOR};
            --cm-secondary: {SECONDARY_COLOR};
            --cm-accent: {ACCENT_COLOR};
            --cm-card: {CARD_BACKGROUND};
            --cm-text: #12263A;
            --cm-muted: #5B6B7F;
            --cm-white: #FFFFFF;
            --cm-border: rgba(22, 58, 89, 0.12);
        }}

        html, body, [class*="css"] {{
            font-family: 'Manrope', sans-serif;
            color: var(--cm-text);
        }}

        .stApp {{
            background:
                radial-gradient(circle at top right, rgba(94, 143, 199, 0.18), transparent 24%),
                linear-gradient(180deg, #f9fbff 0%, #eef5fd 45%, #f9fbff 100%);
        }}

        h1, h2, h3, .cm-heading, [data-testid="stMetricLabel"] {{
            font-family: 'Sora', sans-serif !important;
            letter-spacing: 0.01em;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #163A59 0%, #1E4C73 100%);
            color: white;
            border-right: 1px solid rgba(255,255,255,0.08);
        }}

        [data-testid="stSidebar"] * {{
            color: white;
        }}

        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stCaption {{
            color: rgba(255,255,255,0.88) !important;
        }}

        [data-testid="stSidebar"] .stMultiSelect label,
        [data-testid="stSidebar"] .stFileUploader label,
        [data-testid="stSidebar"] .stTextInput label {{
            color: white !important;
        }}

        .cm-sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            padding: 0.25rem 0 1rem 0;
        }}

        .cm-sidebar-brand img {
            width: 64px;
            height: 64px;
            border-radius: 0;
            box-shadow: none;
            background: transparent;
            object-fit: contain;
        }

        .cm-sidebar-brand-title {{
            font-family: 'Sora', sans-serif;
            font-size: 1.02rem;
            font-weight: 800;
            line-height: 1.05;
            letter-spacing: 0.04em;
        }}

        .cm-sidebar-brand-subtitle {{
            font-size: 0.82rem;
            opacity: 0.88;
            margin-top: 0.15rem;
        }}

        .cm-hero {{
            background:
                linear-gradient(135deg, rgba(22, 58, 89, 0.98), rgba(36, 87, 130, 0.94)),
                radial-gradient(circle at top right, rgba(255,255,255,0.14), transparent 28%);
            border: 1px solid rgba(255,255,255,0.08);
            color: white;
            border-radius: 28px;
            padding: 2rem 2rem 1.8rem 2rem;
            margin: 0 0 1.25rem 0;
            box-shadow: 0 18px 40px rgba(22, 58, 89, 0.18);
        }}

        .cm-hero-grid {{
            display: grid;
            grid-template-columns: 1.6fr 0.7fr;
            gap: 1.25rem;
            align-items: center;
        }}

        .cm-hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            border: 1px solid rgba(255,255,255,0.16);
            background: rgba(255,255,255,0.09);
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .cm-hero h1 {
            margin: 0.7rem 0 0.35rem 0;
            color: white;
            font-size: clamp(2.2rem, 3.4vw, 3.9rem);
            line-height: 0.96;
            letter-spacing: 0.02em;
        }

        .cm-hero-subtitle {
            margin: 0.25rem 0 0.45rem 0;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: clamp(1.45rem, 2.15vw, 2.15rem) !important;
            font-weight: 600;
            line-height: 1.15 !important;
            letter-spacing: 0.01em;
            color: rgba(255,255,255,0.96) !important;
            max-width: 950px;
        }

        .cm-hero-body {
            margin: 0.45rem 0 0 0;
            font-family: 'Manrope', sans-serif !important;
            font-size: 1.03rem !important;
            font-weight: 500;
            line-height: 1.65 !important;
            color: rgba(255,255,255,0.88) !important;
            max-width: 900px;
        }

        .cm-hero-note {
            font-size: 0.96rem !important;
            color: rgba(255,255,255,0.82) !important;
        }

        .cm-hero-logo-card {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 210px;
            background: transparent;
            border: none;
            border-radius: 0;
            backdrop-filter: none;
        }

        .cm-hero-logo-card img {
            width: min(210px, 100%);
            height: auto;
            filter: drop-shadow(0 18px 26px rgba(0,0,0,0.14));
        }

        .cm-section-title {{
            font-family: 'Montserrat', sans-serif;
            color: var(--cm-primary);
            letter-spacing: 0.02em;
        }}

        [data-testid="stMetric"] {{
            background: rgba(255,255,255,0.76);
            border: 1px solid var(--cm-border);
            border-radius: 20px;
            padding: 0.9rem 0.9rem 0.8rem 0.9rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        [data-testid="stMetricValue"] {{
            font-family: 'Montserrat', sans-serif;
            color: var(--cm-primary);
        }}

        .stButton > button, .stDownloadButton > button {{
            border-radius: 14px;
            border: 1px solid rgba(22, 58, 89, 0.10);
            font-weight: 700;
            padding: 0.55rem 1rem;
            box-shadow: 0 8px 20px rgba(22, 58, 89, 0.08);
        }}

        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: white;
            border: none;
        }}

        .stButton > button:hover, .stDownloadButton > button:hover {{
            border-color: rgba(22, 58, 89, 0.22);
        }}

        [data-testid="stDataFrame"], .stAlert, div[data-baseweb="select"], .stTextInput > div > div,
        .stMultiSelect > div > div {{
            border-radius: 16px !important;
        }}

        .stDataFrame {{
            border: 1px solid var(--cm-border);
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.05);
        }}

        .cm-block-caption {{
            color: var(--cm-muted);
            margin-top: -0.2rem;
        }}

        .cm-mini-table-wrap {
            background: rgba(255,255,255,0.8);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }

        .cm-mini-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.94rem;
        }

        .cm-mini-table thead th {
            background: var(--cm-primary);
            color: white;
            text-align: left;
            padding: 0.72rem 0.85rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .cm-mini-table td {
            padding: 0.72rem 0.85rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
        }

        .cm-mini-table tbody tr:nth-child(even) td {
            background: rgba(221, 234, 248, 0.3);
        }

        .cm-mini-table td.cm-number {
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }

        .cm-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1.1;
            white-space: nowrap;
        }

        @media (max-width: 900px) {{
            .cm-hero-grid {{
                grid-template-columns: 1fr;
            }}
            .cm-hero-logo-card {{
                min-height: 140px;
            }}
            .cm-sidebar-brand img {{
                width: 52px;
                height: 52px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand(user: dict | None = None) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="cm-sidebar-brand">
                <img src="{LOGO_DATA_URI}" alt="Logo Classification Management" />
                <div>
                    <div class="cm-sidebar-brand-title">CLASSIFICATION<br/>MANAGEMENT</div>
                    <div class="cm-sidebar-brand-subtitle">Portefeuille & gouvernance des risques</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if user is not None:
            st.caption(f"Connecté en tant que {user['display_name']}")


def render_home_hero(user: dict | None = None) -> None:
    welcome = f"Bienvenue {user['display_name']}" if user else "Application sécurisée"
    user_scope_text = (
        "Accédez à votre périmètre multi-société, chargez les jeux de données côté administration et pilotez le portefeuille en toute simplicité."
        if user
        else "Connectez-vous pour accéder à votre périmètre société, aux indicateurs clés et au tableau de pilotage."
    )
    st.markdown(
        f"""
        <section class="cm-hero">
            <div class="cm-hero-grid">
                <div>
                    <div class="cm-hero-badge">{welcome}</div>
                    <h1>CLASSIFICATION<br/>MANAGEMENT</h1>
                    <p class="cm-hero-subtitle">{APP_SUBTITLE}</p>
                    <p class="cm-hero-body cm-hero-note">{user_scope_text}</p>
                </div>
                <div class="cm-hero-logo-card">
                    <img src="{LOGO_DATA_URI}" alt="Logo Classification Management" />
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

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
    render_home_hero(None)
    st.markdown('<h3 class="cm-section-title">Connexion</h3>', unsafe_allow_html=True)
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




def status_palette(value: object, status_type: str) -> tuple[str, str]:
    val = str(value).strip() if pd.notna(value) else ""
    if status_type == "vigilance":
        mapping = {
            "Vigilance Critique": ("#D92D20", "#FFFFFF"),
            "Vigilance Élevée": ("#F79009", "#FFFFFF"),
            "Vigilance Modérée": ("#FEEFC6", "#8A4B00"),
            "Vigilance Allégée": ("#D1FADF", "#065F46"),
            "Vigilance Aucune": ("#EAF2FB", "#163A59"),
        }
        return mapping.get(val, ("#EEF2F7", "#334155"))
    mapping = {
        "Risque avéré": ("#D92D20", "#FFFFFF"),
        "Risque potentiel": ("#F79009", "#FFFFFF"),
        "Risque mitigé": ("#D1FADF", "#065F46"),
        "Risque levé": ("#E3F2E8", "#166534"),
        "Non calculable": ("#E5E7EB", "#475467"),
        "Aucun risque détecté": ("#EAF2FB", "#163A59"),
    }
    return mapping.get(val, ("#EEF2F7", "#334155"))


def render_status_badge(value: object, status_type: str) -> str:
    bg, fg = status_palette(value, status_type)
    return f'<span class="cm-badge" style="background:{bg}; color:{fg};">{escape(str(value))}</span>'


def render_small_table(df: pd.DataFrame, color_columns: dict[str, str] | None = None) -> None:
    color_columns = color_columns or {}
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    html = ["<div class='cm-mini-table-wrap'><table class='cm-mini-table'><thead><tr>"]
    for col in df.columns:
        html.append(f"<th>{escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in df.iterrows():
        html.append("<tr>")
        for col in df.columns:
            value = row[col]
            classes = []
            if pd.api.types.is_number(value) and not isinstance(value, bool):
                classes.append("cm-number")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            if pd.isna(value):
                rendered = ""
            elif col in color_columns:
                rendered = render_status_badge(value, color_columns[col])
            else:
                rendered = escape(str(value))
            html.append(f"<td{class_attr}>{rendered}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def dataframe_cell_style(value: object, status_type: str) -> str:
    if pd.isna(value):
        return ""
    bg, fg = status_palette(value, status_type)
    return f"background-color: {bg}; color: {fg}; font-weight: 700; border-radius: 999px;"


def style_dataframe(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%d/%m/%Y")
    styler = (
        out.style
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props": [("background-color", PRIMARY_COLOR), ("color", "white"), ("font-family", "Sora, sans-serif"), ("font-weight", "700")]},
            {"selector": "td", "props": [("border-color", "rgba(22, 58, 89, 0.08)")]},
        ])
    )
    if "Vigilance" in out.columns:
        styler = styler.map(lambda v: dataframe_cell_style(v, "vigilance"), subset=["Vigilance"])
    if "Risque" in out.columns:
        styler = styler.map(lambda v: dataframe_cell_style(v, "risk"), subset=["Risque"])
    if "Statut" in out.columns:
        styler = styler.map(lambda v: dataframe_cell_style(v, "risk"), subset=["Statut"])
    return styler


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
    color_columns = {index_col: "vigilance"} if index_col == "Vigilance" else ({index_col: "risk"} if index_col == "Statut" else {})
    render_small_table(format_percent_column(dist_df), color_columns=color_columns)


def render_top_block(title: str, df: pd.DataFrame) -> None:
    st.markdown("**{}**".format(title))
    render_small_table(df)


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
    inject_brand_theme()

    user = get_current_user()
    render_sidebar_brand(user)
    if user is None:
        login_form()
        return

    render_home_hero(user)
    st.caption("L’admin publie un jeu de données 01/02/03 ; tous les utilisateurs lisent ensuite ce jeu actif.")

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
        render_small_table(build_alert_table(filtered))

    st.divider()
    st.markdown('<h3 class="cm-section-title">Concentrations</h3>', unsafe_allow_html=True)
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
    st.markdown('<h3 class="cm-section-title">Dossiers prioritaires</h3>', unsafe_allow_html=True)
    st.dataframe(style_dataframe(build_priority_table(filtered, top_n=10)), use_container_width=True, height=420)

    export_columns = [c for c in DISPLAY_COLUMNS if c in filtered.columns]
    st.download_button(
        label="Exporter la vue filtrée (.csv)",
        data=dataframe_to_csv_bytes(filtered[export_columns]),
        file_name="tableau1_portefeuille_filtre.csv",
        mime="text/csv",
        type="primary",
    )

    with st.expander("Aperçu des données sous-jacentes filtrées"):
        st.dataframe(style_dataframe(filtered[export_columns]), use_container_width=True, height=420)


if __name__ == "__main__":
    main()
