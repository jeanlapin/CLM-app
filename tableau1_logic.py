from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re

import numpy as np
import pandas as pd

DEFAULT_DATA_FILES = {
    "base": "01_Donnees_base_source.csv",
    "indicators": "02_Indicateurs_source.csv",
    "history": "03_Indicateurs_historique.csv",
}

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


def resolve_data_file(filename: str, search_root: Path | None = None) -> Path:
    here = search_root or Path(__file__).resolve().parent
    candidates = [
        here / filename,
        here / "data" / filename,
        here.parent / filename,
        here.parent / "data" / filename,
        Path.cwd() / filename,
        Path.cwd() / "data" / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    searched = "\n - ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"Impossible de trouver {filename}. Emplacements testés :\n - {searched}"
    )


def read_csv_semicolon(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    return df.dropna(how="all")


def normalize_siren(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )


def parse_percent(value: object) -> float:
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


def clean_text_column(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
        .astype("string")
    )


def load_source_data(search_root: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = read_csv_semicolon(resolve_data_file(DEFAULT_DATA_FILES["base"], search_root))
    indicators = read_csv_semicolon(resolve_data_file(DEFAULT_DATA_FILES["indicators"], search_root))
    history = read_csv_semicolon(resolve_data_file(DEFAULT_DATA_FILES["history"], search_root))

    for df in (base, indicators, history):
        df["SIREN"] = normalize_siren(df["SIREN"])
        df.dropna(subset=["SIREN"], inplace=True)

    base = base.drop_duplicates(subset=["SIREN"], keep="first").copy()
    indicators = indicators.drop_duplicates(subset=["SIREN"], keep="first").copy()

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
    cols = [c for c in indicators_df.columns if re.search(r"(?i)\bstatut\b", c)]
    return [c for c in cols if c != "Vigilance statut"]


def build_portfolio_dataset(search_root: Path | None = None) -> pd.DataFrame:
    base, indicators, history = load_source_data(search_root)

    ind_status_cols = status_columns(indicators)
    required_indicator_cols = [
        "SIREN",
        "Vigilance statut",
        "Vigilance valeur",
        "Vigilance Date de mise à jour",
        "Cash intensité Statut",
        *ind_status_cols,
    ]
    required_indicator_cols = list(dict.fromkeys(c for c in required_indicator_cols if c in indicators.columns))

    portfolio = base.merge(indicators[required_indicator_cols], how="left", on="SIREN")

    history_count = history.groupby("SIREN").size().rename("Nb historique")
    portfolio = portfolio.merge(history_count, how="left", left_on="SIREN", right_index=True)
    portfolio["Nb historique"] = portfolio["Nb historique"].fillna(0).astype(int)

    portfolio["Vigilance"] = portfolio.get("Vigilance statut")
    portfolio["Risque"] = portfolio.get("Statut de risque (import SaaS source)")

    for label in ["Risque avéré", "Risque potentiel", "Risque mitigé", "Risque levé", "Non calculable"]:
        portfolio[f"Nb {label}"] = portfolio[ind_status_cols].eq(label).sum(axis=1)

    today = pd.Timestamp.today().normalize()
    portfolio["Alerte justificatif incomplet"] = (
        (portfolio["Flag justificatif complet"] != "Oui")
        & (portfolio["Vigilance"].isin(CRITICAL_VIGILANCE))
    ).astype(int)
    portfolio["Alerte vigilance critique"] = (portfolio["Vigilance"] == "Vigilance Critique").astype(int)
    portfolio["Alerte revue trop ancienne"] = (
        portfolio["Vigilance"].isin(CRITICAL_VIGILANCE)
        & portfolio["Date dernière revue"].notna()
        & ((today - portfolio["Date dernière revue"]).dt.days > 90)
    ).astype(int)
    portfolio["Alerte sans prochaine revue"] = portfolio["Date prochaine revue"].isna().astype(int)
    portfolio["Alerte cross-border élevé"] = portfolio["Cross border"].ge(0.25).fillna(False).astype(int)
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


def non_empty_sorted(values: Iterable[object]) -> list[str]:
    return sorted({str(v).strip() for v in values if pd.notna(v) and str(v).strip()})


def apply_filters(df: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
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
        rows.append({"Libellé": item, "Nb": nb, "%": nb / total if total else 0.0})
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
        df.sort_values(["Score priorité", "SIREN"], ascending=[False, False], kind="stable")
        .head(top_n)
        .copy()
    )
    priority.insert(0, "#", range(1, len(priority) + 1))
    return priority[
        [
            "#",
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
    ].rename(
        columns={
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
