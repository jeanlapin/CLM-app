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
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import altair as alt
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

REVIEW_FREQUENCY_DEFAULTS = {
    "Vigilance Critique": 3,
    "Vigilance Élevée": 6,
    "Vigilance Modérée": 12,
    "Vigilance Allégée": 24,
    "Vigilance Aucune": 36,
}

REVIEW_CAPACITY_DEFAULTS = {
    "Vigilance Critique": 5,
    "Vigilance Élevée": 8,
    "Vigilance Modérée": 10,
    "Vigilance Allégée": 12,
    "Vigilance Aucune": 15,
}

REVIEW_SIMULATION_FILE = "review_simulations.csv"

REVIEW_TYPE_BY_VIGILANCE = {
    "Vigilance Critique": "Revue critique immédiate",
    "Vigilance Élevée": "Revue renforcée",
    "Vigilance Modérée": "Revue ciblée",
    "Vigilance Allégée": "Revue allégée de mise à jour",
    "Vigilance Aucune": "Revue standard",
}

REVIEW_OBJECTIVES_BY_VIGILANCE = {
    "Vigilance Critique": (
        "Sécuriser immédiatement le dossier et confirmer ou infirmer les alertes majeures.",
        "Documenter une décision de remédiation prioritaire et fixer une revue rapprochée.",
    ),
    "Vigilance Élevée": (
        "Compléter rapidement l’analyse et consolider les zones de risque sensibles.",
        "Valider la cohérence du dossier, des flux et des justificatifs avant réévaluation.",
    ),
    "Vigilance Modérée": (
        "Traiter les anomalies ciblées et remettre le dossier à jour sans surmobiliser les équipes.",
        "Programmer une prochaine revue cohérente avec le niveau de risque résiduel.",
    ),
    "Vigilance Allégée": (
        "Régulariser les points mineurs de complétude ou de pilotage identifiés sur le dossier.",
        "Confirmer que le suivi peut rester allégé avec une prochaine revue planifiée.",
    ),
    "Vigilance Aucune": (
        "Vérifier l’hygiène documentaire et la cohérence générale du dossier sans signe d’alerte majeur.",
        "Maintenir un cycle de revue standard et des données de pilotage à jour.",
    ),
}

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
    "Vigilance",
    "Risque",
    SOC_COL,
    "Pays de résidence",
    "Segment",
    "Produit(service) principal",
    "Canal d’opérations principal 12 mois",
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
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Sora:wght@500;600;700;800&family=Montserrat:wght@600;700;800&family=Cormorant+Garamond:wght@500;600;700&display=swap');

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

        .cm-sidebar-brand img {{
            width: 64px;
            height: 64px;
            border-radius: 0;
            box-shadow: none;
            background: transparent;
            object-fit: contain;
        }}

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

        .cm-hero h1 {{
            margin: 0.7rem 0 0.35rem 0;
            color: white;
            font-size: clamp(2.2rem, 3.4vw, 3.9rem);
            line-height: 0.96;
            letter-spacing: 0.02em;
        }}

        .cm-hero-subtitle {{
            margin: 0.25rem 0 0.45rem 0;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: clamp(1.45rem, 2.15vw, 2.15rem) !important;
            font-weight: 600;
            line-height: 1.15 !important;
            letter-spacing: 0.01em;
            color: rgba(255,255,255,0.96) !important;
            max-width: 950px;
        }}

        .cm-hero-body {{
            margin: 0.45rem 0 0 0;
            font-family: 'Manrope', sans-serif !important;
            font-size: 1.03rem !important;
            font-weight: 500;
            line-height: 1.65 !important;
            color: rgba(255,255,255,0.88) !important;
            max-width: 900px;
        }}

        .cm-hero-note {{
            font-size: 0.96rem !important;
            color: rgba(255,255,255,0.82) !important;
        }}

        .cm-home-link {{
            margin-top: 0.55rem;
            text-align: center;
            font-family: 'Sora', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: var(--cm-primary);
        }}

        .cm-hero-logo-card {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 210px;
            background: transparent;
            border: none;
            border-radius: 0;
            backdrop-filter: none;
        }}

        .cm-hero-logo-card img {{
            width: min(210px, 100%);
            height: auto;
            filter: drop-shadow(0 18px 26px rgba(0,0,0,0.14));
        }}

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

        .cm-kpi-band {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.45rem 0 0.25rem 0;
        }}

        .cm-kpi-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,250,255,0.92));
            border: 1px solid rgba(22, 58, 89, 0.10);
            border-radius: 18px;
            padding: 0.7rem 0.85rem 0.72rem 0.85rem;
            box-shadow: 0 8px 20px rgba(22, 58, 89, 0.06);
            min-height: 84px;
        }}

        .cm-kpi-card.is-alert {{
            border-color: rgba(180, 42, 42, 0.16);
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,245,245,0.92));
        }}

        .cm-kpi-label {{
            font-family: 'Sora', sans-serif;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #65758A;
            margin-bottom: 0.22rem;
        }}

        .cm-kpi-value {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.62rem;
            font-weight: 800;
            line-height: 1.05;
            color: var(--cm-primary);
            margin-bottom: 0.08rem;
        }}

        .cm-kpi-card.is-alert .cm-kpi-value {{
            color: #A22828;
        }}

        .cm-kpi-sub {{
            font-size: 0.78rem;
            color: var(--cm-muted);
            line-height: 1.25;
        }}

        .cm-kpi-note {{
            margin-top: 0.35rem;
            font-size: 0.82rem;
            color: var(--cm-muted);
        }}

        .stButton > button, .stDownloadButton > button, .stFileUploader button {{
            border-radius: 14px;
            border: none !important;
            font-weight: 800;
            padding: 0.6rem 1rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.14);
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
        }}

        .stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, #245782, #2F6B9E) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        .stButton > button:hover, .stDownloadButton > button:hover, .stFileUploader button:hover {{
            color: #FFFFFF !important;
            filter: brightness(1.04);
            transform: translateY(-1px);
        }}

        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stDownloadButton > button,
        [data-testid="stSidebar"] .stFileUploader button {{
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        [data-testid="stSidebar"] .stButton > button[kind="secondary"],
        [data-testid="stSidebar"] .stDownloadButton > button[kind="secondary"] {{
            background: linear-gradient(135deg, #245782, #2F6B9E) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}

        [data-testid="stSidebar"] .stFileUploader button:hover,
        [data-testid="stSidebar"] .stButton > button:hover,
        [data-testid="stSidebar"] .stDownloadButton > button:hover {{
            color: #FFFFFF !important;
            filter: brightness(1.05);
        }}

        div[data-testid="stFileUploaderDropzone"] {{
            background: rgba(22, 58, 89, 0.05) !important;
            border: 1px dashed rgba(22, 58, 89, 0.25) !important;
            border-radius: 16px !important;
        }}

        div[data-testid="stFileUploaderDropzone"] * {{
            color: var(--cm-primary) !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] {{
            background: rgba(255,255,255,0.08) !important;
            border: 1px dashed rgba(255,255,255,0.30) !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"] * {{
            color: #FFFFFF !important;
        }}

        div[data-testid="stExpander"] {{
            border: none !important;
            background: transparent !important;
        }}

        div[data-testid="stExpander"] details {{
            border: none !important;
            background: transparent !important;
        }}

        div[data-testid="stExpander"] summary {{
            background: linear-gradient(135deg, var(--cm-primary), #245782) !important;
            color: #FFFFFF !important;
            border-radius: 14px !important;
            padding: 0.35rem 0.8rem !important;
            box-shadow: 0 10px 20px rgba(22, 58, 89, 0.12);
        }}

        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span,
        div[data-testid="stExpander"] summary svg {{
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
            font-weight: 800 !important;
        }}

        [data-testid="stDataFrame"], .stAlert, div[data-baseweb="select"], .stTextInput > div > div,
        .stMultiSelect > div > div {{
            border-radius: 16px !important;
        }}

        .stDataFrame {{
            border: 1px solid var(--cm-border);
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.05);
        }}

        [data-testid="stDataFrame"] [role="columnheader"] {{
            background: var(--cm-primary) !important;
            color: #FFFFFF !important;
            justify-content: center !important;
            text-align: center !important;
            font-family: 'Sora', sans-serif !important;
            font-size: 0.78rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.05em !important;
            font-variant-caps: all-small-caps !important;
            text-transform: none !important;
            border-bottom: 0 !important;
        }}

        [data-testid="stDataFrame"] [role="columnheader"] * {{
            color: #FFFFFF !important;
            text-align: center !important;
        }}

        [data-testid="stDataFrame"] [role="gridcell"] {{
            justify-content: center !important;
            text-align: center !important;
        }}

        [data-testid="stDataFrame"] [role="gridcell"] * {{
            text-align: center !important;
        }}

        .cm-block-caption {{
            color: var(--cm-muted);
            margin-top: -0.2rem;
        }}

        .cm-table-panel-title {{
            display: block;
            width: 100%;
            background: var(--cm-primary);
            color: #FFFFFF;
            border-radius: 16px 16px 0 0;
            padding: 0.78rem 0.95rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.84rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: none;
            font-variant-caps: all-small-caps;
            text-align: center;
            margin-bottom: 0;
        }}

        .cm-table-panel-caption {{
            margin: 0 0 0.45rem 0;
            padding: 0.42rem 0.8rem 0.2rem 0.8rem;
            border-left: 1px solid var(--cm-border);
            border-right: 1px solid var(--cm-border);
            border-bottom: 1px solid var(--cm-border);
            border-radius: 0 0 14px 14px;
            background: rgba(255,255,255,0.72);
            color: var(--cm-muted);
            font-size: 0.84rem;
        }}

        .cm-analysis-hint-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem;
            margin: 0.15rem 0 0.55rem 0;
        }}

        .cm-analysis-hint-text {{
            color: var(--cm-muted);
            font-size: 0.82rem;
            line-height: 1.35;
        }}

        .cm-analysis-jump-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
            background: var(--cm-primary);
            color: #FFFFFF !important;
            text-decoration: none !important;
            padding: 0.52rem 0.8rem;
            border-radius: 999px;
            font-family: 'Sora', sans-serif;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            font-variant-caps: all-small-caps;
            box-shadow: 0 10px 18px rgba(22, 58, 89, 0.18);
        }}

        .cm-mini-table-wrap {{
            background: rgba(255,255,255,0.8);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        .cm-mini-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.94rem;
        }}

        .cm-mini-table thead th {{
            background: var(--cm-primary);
            color: white;
            text-align: center;
            padding: 0.72rem 0.85rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: none;
            font-variant-caps: all-small-caps;
        }}

        .cm-mini-table td {{
            padding: 0.72rem 0.85rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
            text-align: center;
        }}

        .cm-mini-table tbody tr:nth-child(even) td {{
            background: rgba(221, 234, 248, 0.3);
        }}

        .cm-mini-table td.cm-number {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-mini-table td.cm-number-soft {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 500;
        }}

        .cm-analysis-main-wrap {{
            background: rgba(255,255,255,0.86);
            border: 1px solid var(--cm-border);
            border-radius: 20px;
            overflow: auto;
            box-shadow: 0 12px 28px rgba(22, 58, 89, 0.07);
        }}

        .cm-analysis-main-table {{
            width: max-content;
            min-width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.95rem;
        }}

        .cm-analysis-main-table thead th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: #FFFFFF;
            text-align: center;
            padding: 0.86rem 0.95rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.03em;
            text-transform: none;
            font-variant-caps: all-small-caps;
            white-space: nowrap;
        }}

        .cm-analysis-main-table tbody td {{
            padding: 0.82rem 0.95rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
            white-space: nowrap;
            background: rgba(255,255,255,0.98);
            text-align: center;
        }}

        .cm-analysis-main-table tbody tr:nth-child(even) td {{
            background: rgba(237, 244, 252, 0.92);
        }}

        .cm-analysis-main-table tbody tr:hover td {{
            background: rgba(226, 237, 249, 0.96);
        }}

        .cm-analysis-main-table tbody tr.cm-row-selected td {{
            background: rgba(221, 234, 248, 0.98) !important;
            color: var(--cm-primary);
            font-weight: 700;
        }}

        .cm-analysis-main-table tbody td.cm-number {{
            text-align: center;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-analysis-main-table tbody td.cm-first-col {{
            font-weight: 800;
            color: var(--cm-primary);
            text-align: center;
        }}


        .cm-analysis-main-table thead th.cm-calculated-col {{
            background: linear-gradient(135deg, #7A5A00, #A97610);
            color: #FFFFFF;
        }}

        .cm-analysis-main-table tbody td.cm-calculated-col {{
            background: rgba(255, 244, 214, 0.96);
            color: #7A5A00;
            font-weight: 600;
        }}

        .cm-analysis-params {{
            background: rgba(255,255,255,0.72);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            padding: 0.65rem 0.8rem 0.2rem 0.8rem;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.04);
            margin-bottom: 0.9rem;
        }}

        .cm-analysis-mode-shell {{
            margin: 0.2rem 0 0.35rem 0;
            padding: 0.85rem 1rem 0.15rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(22, 58, 89, 0.16);
            background: linear-gradient(180deg, rgba(221, 234, 248, 0.88), rgba(237, 244, 252, 0.78));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.65);
        }}

        .cm-analysis-mode-kicker {{
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #2F6B9E;
            margin-bottom: 0.12rem;
        }}

        .cm-analysis-mode-title {{
            font-family: 'Montserrat', sans-serif;
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--cm-primary);
            margin-bottom: 0.12rem;
        }}

        .cm-analysis-mode-note {{
            font-size: 0.92rem;
            color: var(--cm-muted);
            margin-bottom: 0.35rem;
        }}

        .cm-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1.1;
            white-space: nowrap;
        }}

        .cm-data-table-wrap {{
            background: rgba(255,255,255,0.88);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            overflow: auto;
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        .cm-data-table {{
            width: 100%;
            min-width: 980px;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.93rem;
        }}

        .cm-data-table thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: #FFFFFF;
            text-align: left;
            padding: 0.82rem 0.9rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            white-space: nowrap;
        }}

        .cm-data-table thead th:first-child {{
            border-top-left-radius: 16px;
        }}

        .cm-data-table thead th:last-child {{
            border-top-right-radius: 16px;
        }}

        .cm-data-table tbody td {{
            padding: 0.78rem 0.9rem;
            border-top: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            color: var(--cm-text);
            background: rgba(255,255,255,0.96);
            white-space: nowrap;
        }}

        .cm-data-table tbody tr:nth-child(even) td {{
            background: rgba(221, 234, 248, 0.28);
        }}

        .cm-data-table td.cm-number {{
            text-align: right;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-data-table td.cm-strong {{
            font-weight: 700;
            color: var(--cm-primary);
            white-space: normal;
            min-width: 240px;
        }}

        .cm-data-table td.cm-wrap {{
            white-space: normal;
        }}

        .cm-data-table td.cm-narrow {{
            width: 1%;
        }}

        .cm-siren-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-weight: 800;
            color: var(--cm-primary) !important;
            text-decoration: none;
            border-bottom: 2px solid rgba(22,58,89,0.18);
            padding-bottom: 0.05rem;
        }}

        .cm-siren-link:hover {{
            color: #245782 !important;
            border-bottom-color: #245782;
        }}

        .cm-siren-link span {{
            font-size: 0.85rem;
            opacity: 0.88;
        }}

        .cm-stream-note {{
            margin: 0.1rem 0 0.65rem 0;
            color: var(--cm-muted);
            font-size: 0.86rem;
            font-weight: 600;
        }}

        .cm-stream-head {{
            background: linear-gradient(135deg, var(--cm-primary), #245782);
            color: #FFFFFF;
            border-radius: 14px;
            padding: 0.72rem 0.8rem;
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            min-height: 48px;
            display: flex;
            align-items: center;
            box-shadow: 0 10px 18px rgba(22, 58, 89, 0.10);
        }}

        .cm-stream-cell {{
            background: rgba(255,255,255,0.90);
            border: 1px solid rgba(22, 58, 89, 0.09);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
            min-height: 52px;
            display: flex;
            align-items: center;
            color: var(--cm-text);
            box-shadow: 0 6px 14px rgba(22, 58, 89, 0.04);
            font-size: 0.93rem;
        }}

        .cm-stream-cell.cm-even {{
            background: rgba(238, 245, 253, 0.92);
        }}

        .cm-stream-cell.cm-number {{
            justify-content: flex-end;
            font-variant-numeric: tabular-nums;
            font-weight: 700;
        }}

        .cm-stream-cell.cm-text-strong {{
            font-weight: 700;
            color: var(--cm-primary);
        }}

        .cm-hero-pills {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1rem;
        }}

        .cm-hero-pill {{
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.16);
            color: rgba(255,255,255,0.95);
            font-size: 0.86rem;
            font-weight: 700;
        }}

        .cm-premium-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin: 1rem 0 1.2rem 0;
        }}

        .cm-premium-card {{
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 1.15rem 1.15rem 1rem 1.15rem;
            background: linear-gradient(160deg, rgba(22, 58, 89, 0.98), rgba(36, 87, 130, 0.92));
            border: 1px solid rgba(255,255,255,0.08);
            color: #FFFFFF;
            min-height: 190px;
            box-shadow: 0 14px 34px rgba(22, 58, 89, 0.16);
        }}

        .cm-premium-card::after {{
            content: "";
            position: absolute;
            right: -42px;
            top: -42px;
            width: 128px;
            height: 128px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.18), rgba(255,255,255,0));
        }}

        .cm-premium-kicker {{
            font-family: 'Sora', sans-serif;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.76);
        }}

        .cm-premium-title {{
            margin-top: 0.4rem;
            font-family: 'Sora', sans-serif;
            font-size: 1.12rem;
            font-weight: 800;
            line-height: 1.2;
            color: #FFFFFF;
        }}

        .cm-premium-value {{
            margin-top: 0.7rem;
            font-family: 'Montserrat', sans-serif;
            font-size: 1.72rem;
            font-weight: 800;
            color: #FFFFFF;
        }}

        .cm-premium-text {{
            margin-top: 0.45rem;
            font-size: 0.95rem;
            line-height: 1.55;
            color: rgba(255,255,255,0.84);
        }}

        .cm-page-hero {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 0 1.25rem 0;
            padding: 0.25rem 0 0.5rem 0;
        }}

        .cm-page-hero-inner {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            width: 100%;
        }}

        .cm-page-hero-logo {{
            width: 74px;
            height: 74px;
            object-fit: contain;
            filter: drop-shadow(0 10px 18px rgba(22, 58, 89, 0.16));
        }}

        .cm-page-hero-title {{
            margin: 0;
            font-family: 'Cormorant Garamond', serif !important;
            font-size: clamp(2.2rem, 4vw, 3.5rem);
            font-weight: 700;
            line-height: 1;
            letter-spacing: 0.01em;
            color: var(--cm-primary);
        }}

        @media (max-width: 900px) {{
            .cm-page-hero-inner {{
                flex-direction: column;
                gap: 0.55rem;
            }}
            .cm-page-hero-logo {{
                width: 58px;
                height: 58px;
            }}
            .cm-page-hero-title {{
                text-align: center;
            }}
            .cm-premium-grid {{
                grid-template-columns: 1fr;
            }}
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

        .cm-client-toolbar {{
            display: flex;
            align-items: end;
            gap: 0.8rem;
            flex-wrap: wrap;
            margin-bottom: 0.8rem;
        }}

        .cm-client-breadcrumb {{
            font-size: 0.88rem;
            color: var(--cm-muted);
            margin-bottom: 0.4rem;
        }}

        .cm-client-hero {{
            background: linear-gradient(145deg, rgba(22, 58, 89, 0.98), rgba(36, 87, 130, 0.93));
            border-radius: 24px;
            padding: 1.15rem 1.2rem 1rem 1.2rem;
            color: #FFFFFF;
            box-shadow: 0 16px 36px rgba(22, 58, 89, 0.16);
            margin-bottom: 1rem;
        }}

        .cm-client-title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        .cm-client-title {{
            font-family: 'Sora', sans-serif;
            font-size: 1.85rem;
            font-weight: 800;
            line-height: 1.1;
            color: #FFFFFF;
        }}

        .cm-client-subtitle {{
            margin-top: 0.35rem;
            color: rgba(255,255,255,0.86);
            font-size: 0.98rem;
            font-weight: 600;
        }}

        .cm-client-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 0.95rem;
        }}

        .cm-client-hero-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1rem;
        }}

        .cm-client-hero-card {{
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
            min-height: 92px;
        }}

        .cm-client-hero-label {{
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.72);
            margin-bottom: 0.4rem;
        }}

        .cm-client-hero-value {{
            font-family: 'Sora', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.28;
        }}

        .cm-client-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.35rem 0 1rem 0;
        }}

        .cm-client-field {{
            background: rgba(255,255,255,0.84);
            border: 1px solid var(--cm-border);
            border-radius: 18px;
            padding: 0.9rem 0.95rem;
            box-shadow: 0 10px 22px rgba(22, 58, 89, 0.05);
            min-height: 98px;
        }}

        .cm-client-field-label {{
            color: var(--cm-muted);
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }}

        .cm-client-field-value {{
            color: var(--cm-text);
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.35;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .cm-empty-note {{
            background: rgba(255,255,255,0.84);
            border: 1px dashed rgba(22, 58, 89, 0.22);
            border-radius: 18px;
            padding: 1rem 1rem;
            color: var(--cm-muted);
        }}

        .cm-click-table-wrap {{
            overflow: auto;
            border: 1px solid rgba(22, 58, 89, 0.12);
            border-radius: 18px;
            background: rgba(255,255,255,0.92);
            box-shadow: 0 10px 24px rgba(22, 58, 89, 0.06);
        }}

        .cm-click-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            min-width: 880px;
        }}

        .cm-click-table thead th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: var(--cm-primary);
            color: white;
            font-family: 'Sora', sans-serif;
            font-size: 0.86rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            padding: 0.78rem 0.9rem;
            text-align: center;
            text-transform: none;
            font-variant-caps: all-small-caps;
            white-space: nowrap;
        }}

        .cm-click-table tbody td {{
            padding: 0.72rem 0.9rem;
            border-bottom: 1px solid rgba(22, 58, 89, 0.08);
            vertical-align: middle;
            background: rgba(255,255,255,0.98);
            white-space: nowrap;
            text-align: center;
        }}

        .cm-click-table tbody tr:nth-child(even) td {{
            background: rgba(244, 249, 255, 0.96);
        }}

        .cm-click-table tbody tr:hover td {{
            background: rgba(231, 241, 252, 0.96);
        }}

        .cm-table-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            color: var(--cm-primary) !important;
            font-weight: 800;
            text-decoration: none;
            border-bottom: 1px solid rgba(22, 58, 89, 0.24);
            padding-bottom: 1px;
            cursor: pointer;
        }}

        .cm-table-link:hover {{
            color: var(--cm-secondary) !important;
            border-bottom-color: rgba(42, 108, 168, 0.42);
        }}

        .cm-table-link-icon {{
            font-size: 0.78rem;
            opacity: 0.8;
        }}

        @media (max-width: 1200px) {{
            .cm-client-hero-grid, .cm-client-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 780px) {{
            .cm-premium-grid, .cm-client-hero-grid, .cm-client-grid {{
                grid-template-columns: 1fr;
            }}
        }}


        div[data-testid="stRadio"] {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"] > div {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }}

        div[data-testid="stRadio"] fieldset {{
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            min-width: 0 !important;
        }}

        div[data-testid="stRadio"] hr {{
            display: none !important;
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



def render_home_hero(title: str) -> None:
    st.markdown(
        f'''
        <section class="cm-page-hero">
            <div class="cm-page-hero-inner">
                <img class="cm-page-hero-logo" src="{LOGO_DATA_URI}" alt="Logo Classification Management" />
                <h1 class="cm-page-hero-title">{escape(title)}</h1>
            </div>
        </section>
        ''',
        unsafe_allow_html=True,
    )


def render_home_showcase(user: dict | None = None) -> None:
    manifest = load_manifest() if user else None

    if user is None:
        cards = [
            {
                "kicker": "Supervision",
                "title": "Vision portefeuille",
                "value": "360°",
                "text": "Consolidez le portefeuille, visualisez les vigilances et priorisez les dossiers les plus sensibles.",
                "foot": "Tableau de bord unifié",
            },
            {
                "kicker": "Administration",
                "title": "Publication contrôlée",
                "value": "01 / 02 / 03",
                "text": "L’administrateur charge un jeu de données unique puis l’ensemble des utilisateurs travaille sur la même version active.",
                "foot": "Un seul jeu partagé",
            },
            {
                "kicker": "Multi-société",
                "title": "Accès cloisonnés",
                "value": "Users",
                "text": "Chaque utilisateur n’accède qu’à son périmètre autorisé, avec une expérience fluide et homogène.",
                "foot": "Gouvernance d’accès intégrée",
            },
        ]
    else:
        if user["role"] == "admin" or "ALL" in user["societes_autorisees"]:
            scope_value = "Toutes"
            scope_text = "Vous pouvez superviser l’ensemble des sociétés présentes dans le jeu actif."
        else:
            scope_value = str(len(user["societes_autorisees"]))
            scope_text = "Votre périmètre est limité aux sociétés autorisées sur votre compte."
        published_value = format_manifest_date(manifest.get("published_at_utc")) if manifest else "En attente"
        published_text = (
            "Jeu actif publié par {}.".format(manifest.get("published_by_name") or manifest.get("published_by") or "inconnu")
            if manifest else
            "Aucun jeu de données n’a encore été publié."
        )
        cards = [
            {
                "kicker": "Périmètre",
                "title": "Accès utilisateur",
                "value": scope_value,
                "text": scope_text,
                "foot": f"Rôle : {user['role']}",
            },
            {
                "kicker": "Jeu actif",
                "title": "Publication données",
                "value": published_value,
                "text": published_text,
                "foot": (
                    "Sociétés : {}".format(manifest.get("societes_count", 0))
                    if manifest else "Publication requise"
                ),
            },
            {
                "kicker": "Gouvernance",
                "title": "Cadre de pilotage",
                "value": "V / R",
                "text": "Le bleu structure la navigation, le rouge marque le critique ou le risque avéré, l’orange signale le niveau élevé.",
                "foot": "Lecture visuelle harmonisée",
            },
        ]

    html = ['<div class="cm-premium-grid">']
    for card in cards:
        html.append(
            (
                f'<div class="cm-premium-card">'
                f'<div class="cm-premium-kicker">{escape(card["kicker"])}</div>'
                f'<div class="cm-premium-title">{escape(card["title"])}</div>'
                f'<div class="cm-premium-value">{escape(card["value"])}</div>'
                f'<div class="cm-premium-text">{escape(card["text"])}</div>'
                f'<div class="cm-premium-foot">{escape(card["foot"])}</div>'
                f'</div>'
            )
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


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


def review_simulations_path() -> Path:
    return active_dataset_path() / REVIEW_SIMULATION_FILE


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
    render_home_hero("Classification Management")
    render_home_showcase(None)
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

    st.markdown('<div class="cm-home-link">www.beclm.com</div>', unsafe_allow_html=True)


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


def save_manifest(manifest: dict) -> None:
    manifest_path().write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def load_saved_review_planning_settings() -> tuple[dict[str, int], dict[str, int]]:
    manifest = load_manifest() or {}
    saved = manifest.get("review_planning_settings") or {}
    saved_freq = saved.get("frequencies_months") or {}
    saved_cap = saved.get("capacity_per_month") or {}

    freq_map: dict[str, int] = {}
    cap_map: dict[str, int] = {}
    for label in VIGILANCE_ORDER:
        try:
            freq_map[label] = max(int(saved_freq.get(label, REVIEW_FREQUENCY_DEFAULTS.get(label, 12))), 1)
        except Exception:
            freq_map[label] = int(REVIEW_FREQUENCY_DEFAULTS.get(label, 12))
        try:
            cap_map[label] = max(int(saved_cap.get(label, REVIEW_CAPACITY_DEFAULTS.get(label, 10))), 1)
        except Exception:
            cap_map[label] = int(REVIEW_CAPACITY_DEFAULTS.get(label, 10))
    return freq_map, cap_map


def persist_review_planning_settings(freq_map: dict[str, int], cap_map: dict[str, int], user: dict | None = None) -> None:
    manifest = load_manifest() or {}
    manifest["review_planning_settings"] = {
        "frequencies_months": {label: int(freq_map.get(label, REVIEW_FREQUENCY_DEFAULTS.get(label, 12))) for label in VIGILANCE_ORDER},
        "capacity_per_month": {label: int(cap_map.get(label, REVIEW_CAPACITY_DEFAULTS.get(label, 10))) for label in VIGILANCE_ORDER},
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "saved_by": (user or {}).get("username"),
        "saved_by_name": (user or {}).get("display_name"),
    }
    save_manifest(manifest)


def load_review_simulation_store() -> pd.DataFrame:
    path = review_simulations_path()
    columns = KEY_COLUMNS + [
        "Explique moi",
        "Statut de vigilance espéré après remédiation",
        "Dernier prompt",
        "updated_at_utc",
    ]
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = read_csv_semicolon(path)
    except Exception:
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df[SOC_COL] = normalize_societe_id(df[SOC_COL])
    df["SIREN"] = normalize_siren(df["SIREN"])
    for col in ["Explique moi", "Statut de vigilance espéré après remédiation", "Dernier prompt", "updated_at_utc"]:
        df[col] = df[col].fillna("").astype(str)
    return df[columns].dropna(subset=KEY_COLUMNS).drop_duplicates(subset=KEY_COLUMNS, keep="last")


def save_review_simulation_store(df: pd.DataFrame) -> None:
    path = review_simulations_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    save_df = df.copy()
    for col in KEY_COLUMNS + ["Explique moi", "Statut de vigilance espéré après remédiation", "Dernier prompt", "updated_at_utc"]:
        if col not in save_df.columns:
            save_df[col] = ""
    save_df[SOC_COL] = normalize_societe_id(save_df[SOC_COL])
    save_df["SIREN"] = normalize_siren(save_df["SIREN"])
    save_df = save_df.dropna(subset=KEY_COLUMNS).drop_duplicates(subset=KEY_COLUMNS, keep="last")
    save_df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")


def review_type_for_vigilance(vigilance: str) -> str:
    return REVIEW_TYPE_BY_VIGILANCE.get(str(vigilance or "").strip(), "Revue standard")


def review_objectives_for_vigilance(vigilance: str) -> tuple[str, str]:
    return REVIEW_OBJECTIVES_BY_VIGILANCE.get(
        str(vigilance or "").strip(),
        REVIEW_OBJECTIVES_BY_VIGILANCE["Vigilance Aucune"],
    )


def build_row_alert_labels(row: pd.Series) -> list[str]:
    labels: list[str] = []
    if int(row.get("Alerte justificatif incomplet", 0) or 0) == 1:
        labels.append("Justificatifs incomplets")
    if int(row.get("Alerte sans prochaine revue", 0) or 0) == 1:
        labels.append("Sans prochaine revue")
    if int(row.get("Alerte revue trop ancienne", 0) or 0) == 1:
        labels.append("Revue trop ancienne")
    if int(row.get("Alerte cross-border élevé", 0) or 0) == 1:
        labels.append("Cross-border élevé")
    if int(row.get("Alerte cash intensité élevée", 0) or 0) == 1:
        labels.append("Cash intensité élevée")
    risk = str(row.get("Risque", "") or "").strip()
    if risk == "Risque avéré":
        labels.append("Risque avéré")
    elif risk == "Risque potentiel":
        labels.append("Risque potentiel")
    edd = str(row.get("Statut EDD", "") or "").strip()
    if edd and edd not in {"Validée", "Non requise", "Aucun"}:
        labels.append(f"EDD {edd}")
    return labels


def build_generic_review_prompt(vigilance: str) -> str:
    review_type = review_type_for_vigilance(vigilance)
    objective_1, objective_2 = review_objectives_for_vigilance(vigilance)
    return (
        f"Tu es un analyste conformité. Prépare les consignes de revue pour un dossier classé '{vigilance}'.\n"
        f"Type de revue : {review_type}.\n"
        f"Objectifs : 1) {objective_1} 2) {objective_2}\n\n"
        "Pour le SIREN {SIREN}, à partir des informations suivantes : dénomination, vigilance, risque, EDD, "
        "date de prochaine revue, alertes calculées et motifs, rédige des consignes opérationnelles de revue.\n"
        "La réponse doit contenir : diagnostic bref, actions prioritaires, justificatifs à demander, points de contrôle, "
        "et statut de vigilance estimé après remédiation."
    )


def build_row_review_prompt(row: pd.Series) -> str:
    vigilance = str(row.get("Vigilance", "") or "").strip()
    review_type = review_type_for_vigilance(vigilance)
    objective_1, objective_2 = review_objectives_for_vigilance(vigilance)
    alerts = build_row_alert_labels(row)
    alert_text = ", ".join(alerts) if alerts else "Aucune alerte calculée active"
    next_review = format_date_fr(row.get("Date prochaine revue"))
    return (
        f"Tu es un analyste conformité. Prépare les consignes de revue du dossier SIREN {row.get('SIREN', '')}.\n"
        f"Type de revue : {review_type}. Régime de vigilance : {vigilance}.\n"
        f"Objectifs : 1) {objective_1} 2) {objective_2}\n"
        f"Contexte dossier : Dénomination = {row.get('Dénomination', 'Non renseigné')}, Risque = {row.get('Risque', 'Non renseigné')}, "
        f"EDD = {row.get('Statut EDD', 'Non renseigné')}, Date prochaine revue = {next_review}.\n"
        f"Alertes calculées : {alert_text}.\n"
        "Rédige des consignes de revue courtes, concrètes et priorisées. La sortie doit inclure : diagnostic, "
        "actions de remédiation, justificatifs à obtenir, et statut de vigilance estimé après remédiation."
    )


def build_simulated_review_explanation(row: pd.Series) -> str:
    vigilance = str(row.get("Vigilance", "") or "").strip()
    review_type = review_type_for_vigilance(vigilance)
    alerts = build_row_alert_labels(row)
    actions: list[str] = []
    if "Justificatifs incomplets" in alerts:
        actions.append("compléter et contrôler les justificatifs manquants")
    if "Sans prochaine revue" in alerts:
        actions.append("fixer immédiatement une prochaine revue")
    if "Revue trop ancienne" in alerts:
        actions.append("mettre à jour l’analyse et tracer la revue")
    if "Cross-border élevé" in alerts:
        actions.append("documenter les pays exposés et la logique économique des flux")
    if "Cash intensité élevée" in alerts:
        actions.append("vérifier la cohérence entre activité déclarée et flux cash")
    if "Risque avéré" in alerts:
        actions.append("escalader le dossier au valideur / conformité sans délai")
    elif "Risque potentiel" in alerts:
        actions.append("confirmer ou infirmer le signal de risque")
    if any(a.startswith("EDD ") for a in alerts):
        actions.append("finaliser l’EDD et valider les pièces de support")
    if not actions:
        actions.append("contrôler l’hygiène documentaire et confirmer le maintien du cycle normal de revue")
    actions = list(dict.fromkeys(actions))
    action_text = "; ".join(actions[:4])
    alerts_text = ", ".join(alerts) if alerts else "aucune alerte active"
    return (
        f"{review_type}. Dossier à revoir avec priorité adaptée au niveau {vigilance}. "
        f"Alertes à traiter : {alerts_text}. Actions recommandées : {action_text}."
    )


def build_review_simulation_working_table(df: pd.DataFrame, selected_vigilance: str) -> pd.DataFrame:
    scope = df.copy()
    if selected_vigilance:
        scope = scope[scope["Vigilance"].astype(str).eq(selected_vigilance)].copy()
    if scope.empty:
        return pd.DataFrame()

    store = load_review_simulation_store()
    scope = scope.sort_values(
        by=["Date prochaine revue", "Score priorité", "Dénomination"],
        ascending=[True, False, True],
        kind="stable",
        na_position="last",
    ).copy()
    scope["Type de revue"] = scope["Vigilance"].apply(review_type_for_vigilance)
    scope["Alertes actives"] = scope.apply(lambda row: ", ".join(build_row_alert_labels(row)) or "Aucune", axis=1)

    if not store.empty:
        scope = scope.merge(store, on=KEY_COLUMNS, how="left")
    else:
        scope["Explique moi"] = ""
        scope["Statut de vigilance espéré après remédiation"] = ""
        scope["Dernier prompt"] = ""
        scope["updated_at_utc"] = ""

    scope["Explique moi"] = scope.get("Explique moi", "").fillna("").astype(str)
    scope["Statut de vigilance espéré après remédiation"] = (
        scope.get("Statut de vigilance espéré après remédiation", "").fillna("").astype(str)
    )
    empty_expected = scope["Statut de vigilance espéré après remédiation"].str.strip().eq("")
    scope.loc[empty_expected, "Statut de vigilance espéré après remédiation"] = scope.loc[empty_expected, "Vigilance"].astype(str)

    table = pd.DataFrame({
        "Sélection": False,
        SOC_COL: scope[SOC_COL],
        "SIREN": scope["SIREN"],
        "Dénomination": scope.get("Dénomination", pd.Series("", index=scope.index)),
        "Régime de vigilance": scope.get("Vigilance", pd.Series("", index=scope.index)),
        "Type de revue": scope["Type de revue"],
        "Date prochaine revue": scope.get("Date prochaine revue", pd.Series(pd.NaT, index=scope.index)),
        "Alertes actives": scope["Alertes actives"],
        "Explique moi": scope["Explique moi"],
        "Statut de vigilance espéré après remédiation": scope["Statut de vigilance espéré après remédiation"],
        "Dernier prompt": scope.get("Dernier prompt", pd.Series("", index=scope.index)).fillna("").astype(str),
    })
    return table.reset_index(drop=True)


def persist_review_simulation_subset(edited_df: pd.DataFrame) -> None:
    store = load_review_simulation_store()
    if store.empty:
        store = pd.DataFrame(columns=KEY_COLUMNS + [
            "Explique moi",
            "Statut de vigilance espéré après remédiation",
            "Dernier prompt",
            "updated_at_utc",
        ])
    subset = edited_df[[SOC_COL, "SIREN", "Explique moi", "Statut de vigilance espéré après remédiation", "Dernier prompt"]].copy()
    subset[SOC_COL] = normalize_societe_id(subset[SOC_COL])
    subset["SIREN"] = normalize_siren(subset["SIREN"])
    subset["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    remaining = store.merge(subset[KEY_COLUMNS], on=KEY_COLUMNS, how="left", indicator=True)
    remaining = remaining[remaining["_merge"] == "left_only"].drop(columns=["_merge"])
    combined = pd.concat([remaining, subset], ignore_index=True)
    save_review_simulation_store(combined)


def apply_review_simulation_batch(edited_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    result = edited_df.copy()
    selected_idx = list(result.index[result["Sélection"].fillna(False).astype(bool)])
    batch_idx = selected_idx[:10]
    for idx in batch_idx:
        row = result.loc[idx]
        source_row = pd.Series({
            SOC_COL: row.get(SOC_COL, ""),
            "SIREN": row.get("SIREN", ""),
            "Dénomination": row.get("Dénomination", ""),
            "Vigilance": row.get("Régime de vigilance", ""),
            "Date prochaine revue": row.get("Date prochaine revue"),
            "Risque": row.get("Risque", ""),
            "Statut EDD": row.get("EDD", ""),
            "Alerte justificatif incomplet": row.get("Alerte justificatif incomplet", 0),
            "Alerte sans prochaine revue": row.get("Alerte sans prochaine revue", 0),
            "Alerte revue trop ancienne": row.get("Alerte revue trop ancienne", 0),
            "Alerte cross-border élevé": row.get("Alerte cross-border élevé", 0),
            "Alerte cash intensité élevée": row.get("Alerte cash intensité élevée", 0),
        })
        # enrich from hidden columns if available
        for hidden in [
            "Risque",
            "EDD",
            "Alerte justificatif incomplet",
            "Alerte sans prochaine revue",
            "Alerte revue trop ancienne",
            "Alerte cross-border élevé",
            "Alerte cash intensité élevée",
        ]:
            if hidden in result.columns:
                source_row[hidden if hidden != "EDD" else "Statut EDD"] = row.get(hidden)
        result.at[idx, "Explique moi"] = build_simulated_review_explanation(source_row)
        result.at[idx, "Dernier prompt"] = build_row_review_prompt(source_row)
        current_expected = str(result.at[idx, "Statut de vigilance espéré après remédiation"] or "").strip()
        if not current_expected:
            result.at[idx, "Statut de vigilance espéré après remédiation"] = str(row.get("Régime de vigilance", "") or "")
    return result, len(batch_idx)


def build_review_simulation_export_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    export_df = df.copy()
    if "Date prochaine revue" in export_df.columns:
        export_df["Date prochaine revue"] = export_df["Date prochaine revue"].apply(format_date_fr)
    keep_cols = [
        SOC_COL,
        "SIREN",
        "Dénomination",
        "Régime de vigilance",
        "Type de revue",
        "Date prochaine revue",
        "Alertes actives",
        "Explique moi",
        "Statut de vigilance espéré après remédiation",
    ]
    return export_df[[c for c in keep_cols if c in export_df.columns]].copy()


def render_review_simulation_editor(df: pd.DataFrame, key: str) -> pd.DataFrame:
    display_df = df.copy()
    display_df["Date prochaine revue"] = display_df["Date prochaine revue"].apply(format_date_fr)
    column_config = {
        "Sélection": st.column_config.CheckboxColumn("Sélection", width="small"),
        SOC_COL: st.column_config.TextColumn("Société", width="small"),
        "SIREN": st.column_config.TextColumn("SIREN", width="small"),
        "Dénomination": st.column_config.TextColumn("Dénomination", width="medium"),
        "Régime de vigilance": st.column_config.TextColumn("Régime de vigilance", width="medium"),
        "Type de revue": st.column_config.TextColumn("Type de revue", width="medium"),
        "Date prochaine revue": st.column_config.TextColumn("Date prochaine revue", width="small"),
        "Alertes actives": st.column_config.TextColumn("Alertes actives", width="large"),
        "Explique moi": st.column_config.TextColumn("Explique moi", width="large"),
        "Statut de vigilance espéré après remédiation": st.column_config.SelectboxColumn(
            "Statut de vigilance espéré après remédiation",
            options=VIGILANCE_ORDER,
            width="medium",
        ),
    }
    edited = st.data_editor(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=520,
        num_rows="fixed",
        column_config=column_config,
        column_order=[
            "Sélection",
            SOC_COL,
            "SIREN",
            "Dénomination",
            "Régime de vigilance",
            "Type de revue",
            "Date prochaine revue",
            "Alertes actives",
            "Explique moi",
            "Statut de vigilance espéré après remédiation",
        ],
        disabled=[SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Type de revue", "Date prochaine revue", "Alertes actives"],
        key=key,
    )
    edited["Date prochaine revue"] = pd.to_datetime(edited["Date prochaine revue"], errors="coerce", dayfirst=True)
    return edited


def render_review_simulations_screen(portfolio: pd.DataFrame, user: dict) -> None:
    render_home_hero("Revues & Simulations")
    nav = render_primary_navigation("review_simulations")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "analysis":
        open_analysis_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()
    if nav == "review_simulations":
        open_review_simulations_view()
        st.rerun()

    base_df = build_review_simulation_working_table(portfolio, "")
    if base_df.empty:
        st.info("Aucun SIREN disponible pour préparer une revue sur ce périmètre.")
        return

    review_types = ["Tous"] + list(dict.fromkeys(REVIEW_TYPE_BY_VIGILANCE.values()))
    type_to_vigilance = {v: k for k, v in REVIEW_TYPE_BY_VIGILANCE.items()}
    if st.session_state.get("review_sim_type") not in review_types:
        st.session_state["review_sim_type"] = "Tous"
    selected_review_type = st.selectbox(
        "Type de revue",
        options=review_types,
        key="review_sim_type",
        help="Le type de revue dépend du régime de vigilance. Choisissez un type pour préparer le lot correspondant.",
    )

    working_df = base_df.copy()
    if selected_review_type != "Tous":
        working_df = working_df[working_df["Type de revue"].astype(str).eq(selected_review_type)].copy()

    search_term = st.text_input(
        "Rechercher un SIREN ou une dénomination",
        key="review_sim_search",
        placeholder="Ex. 123456789 ou NOM CLIENT",
    ).strip()
    if search_term:
        mask = (
            working_df["SIREN"].astype(str).str.contains(search_term, case=False, na=False)
            | working_df["Dénomination"].astype(str).str.contains(search_term, case=False, na=False)
            | working_df["Alertes actives"].astype(str).str.contains(search_term, case=False, na=False)
        )
        working_df = working_df[mask].copy()

    if working_df.empty:
        st.info("Aucun SIREN n’est à traiter pour le type de revue retenu.")
        return

    selected_vigilance_for_prompt = type_to_vigilance.get(selected_review_type, "Vigilance Modérée")
    if selected_review_type == "Tous":
        objective_1 = "Préparer les consignes de revue adaptées au niveau de vigilance, aux alertes actives et à l’EDD."
        objective_2 = "Conserver pour chaque SIREN une synthèse exploitable et un niveau de vigilance espéré après remédiation."
        prompt_value = (
            "Tu es un analyste conformité. Pour chaque SIREN sélectionné, prépare les consignes de revue à partir du régime de vigilance, "
            "des alertes calculées actives, du risque, du statut EDD et de la date prochaine revue. La réponse doit contenir : "
            "diagnostic, actions prioritaires, justificatifs à demander, points de contrôle, et statut de vigilance estimé après remédiation."
        )
        kicker = "Tous les types"
    else:
        objective_1, objective_2 = review_objectives_for_vigilance(selected_vigilance_for_prompt)
        prompt_value = build_generic_review_prompt(selected_vigilance_for_prompt)
        kicker = selected_review_type

    top_left, top_right = st.columns([4.2, 2.4])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Revues &amp; Simulations</h3>', unsafe_allow_html=True)
        st.caption("Préparez un lot de 10 SIREN maximum, stockez les consignes de revue et exportez le résultat enrichi.")
    with top_right:
        if st.button("Réinitialiser l’écran", type="secondary", key="review_sim_reset", use_container_width=True):
            st.session_state.pop("review_sim_type", None)
            st.session_state.pop("review_sim_search", None)
            st.session_state.pop("review_sim_notice", None)
            st.rerun()

    info_col, prompt_col = st.columns([2.3, 3.7])
    with info_col:
        st.markdown(
            "<div class='cm-analysis-mode-shell'>"
            f"<div class='cm-analysis-mode-kicker'>{escape(kicker)}</div>"
            "<div class='cm-analysis-mode-title'>Objectifs de la revue</div>"
            f"<div class='cm-analysis-mode-note'>1. {escape(objective_1)}<br>2. {escape(objective_2)}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        due_count = int(pd.to_datetime(working_df["Date prochaine revue"], errors="coerce", dayfirst=True).notna().sum())
        missing_count = int(pd.to_datetime(working_df["Date prochaine revue"], errors="coerce", dayfirst=True).isna().sum())
        kpi_a, kpi_b, kpi_c = st.columns(3)
        kpi_a.metric("SIREN à traiter", format_int_fr(len(working_df)))
        kpi_b.metric("Avec date revue", format_int_fr(due_count))
        kpi_c.metric("Sans date revue", format_int_fr(missing_count))
    with prompt_col:
        st.text_area(
            "Prompt prêt à l’emploi",
            value=prompt_value,
            height=210,
            key="review_sim_prompt_preview",
        )

    metadata_cols = KEY_COLUMNS + [
        "Risque",
        "Statut EDD",
        "Alerte justificatif incomplet",
        "Alerte sans prochaine revue",
        "Alerte revue trop ancienne",
        "Alerte cross-border élevé",
        "Alerte cash intensité élevée",
        "Date prochaine revue",
    ]
    meta = portfolio[[c for c in metadata_cols if c in portfolio.columns]].copy()
    work_for_editor = working_df.merge(
        meta,
        on=KEY_COLUMNS + (["Date prochaine revue"] if "Date prochaine revue" in working_df.columns and "Date prochaine revue" in meta.columns else []),
        how="left",
    )
    if len(work_for_editor) != len(working_df):
        work_for_editor = working_df.merge(meta, on=KEY_COLUMNS, how="left")

    st.divider()
    st.caption(
        "Sélectionnez jusqu’à 10 SIREN dans la colonne ‘Sélection’. La colonne ‘Explique moi’ conserve le texte de préparation de revue."
    )
    edited_df = render_review_simulation_editor(work_for_editor, key=f"review_sim_editor_{selected_review_type}")
    persist_review_simulation_subset(edited_df)

    selected_count = int(edited_df["Sélection"].fillna(False).astype(bool).sum())
    action_col, export_col = st.columns([2.4, 1.2])
    with action_col:
        st.markdown(
            f"<div class='cm-analysis-mode-note'><strong>{selected_count}</strong> ligne(s) sélectionnée(s)</div>",
            unsafe_allow_html=True,
        )
        if st.button("Préparer le lot sélectionné (max 10)", type="primary", key="review_sim_generate_batch", use_container_width=True):
            updated_df, processed = apply_review_simulation_batch(edited_df)
            persist_review_simulation_subset(updated_df)
            if processed == 0:
                st.session_state["review_sim_notice"] = "Sélectionnez au moins un SIREN pour préparer un lot."
            elif selected_count > 10:
                st.session_state["review_sim_notice"] = "Seuls les 10 premiers SIREN sélectionnés ont été préparés."
            else:
                st.session_state["review_sim_notice"] = f"{processed} SIREN ont été préparés dans le lot courant."
            st.rerun()
    with export_col:
        st.download_button(
            label="Exporter (.csv)",
            data=dataframe_to_csv_bytes(build_review_simulation_export_dataframe(edited_df)),
            file_name="revues_et_simulations.csv",
            mime="text/csv",
            type="secondary",
            use_container_width=True,
            key="review_sim_export_csv",
        )

    if st.session_state.get("review_sim_notice"):
        st.success(str(st.session_state.pop("review_sim_notice")))

def build_dataset_cache_signature() -> str:
    manifest = load_manifest() or {}
    current_dir = active_dataset_path()
    parts = [str(manifest.get("published_at_utc", ""))]
    for filename in DATA_FILES.values():
        path = current_dir / filename
        if path.exists():
            stat = path.stat()
            parts.append(f"{filename}:{stat.st_mtime_ns}:{stat.st_size}")
        else:
            parts.append(f"{filename}:missing")
    return "|".join(parts)


@st.cache_data(show_spinner=False)
def get_app_datasets_cached(signature: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = load_source_data()
    portfolio = build_portfolio_dataset()
    return base[0], base[1], base[2], portfolio


def load_app_datasets() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signature = build_dataset_cache_signature()
    base, indicators, history, portfolio = get_app_datasets_cached(signature)
    return base.copy(), indicators.copy(), history.copy(), portfolio.copy()


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
            base[col] = pd.to_datetime(base[col], errors="coerce", dayfirst=True)

    for col in indicators.columns:
        if "Date de mise à jour" in col:
            indicators[col] = pd.to_datetime(indicators[col], errors="coerce", dayfirst=True)

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
    priority.insert(0, "Rang", range(1, len(priority) + 1))
    columns = [
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        SOC_COL,
        "Pays de résidence",
        "Segment",
        "Statut EDD",
        "Analyste",
        "Score priorité",
        "Motifs",
        "Rang",
    ]
    columns = [c for c in columns if c in priority.columns]
    return priority[columns].rename(
        columns={
            SOC_COL: "Société",
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


def reset_review_filters() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("review_filter_"):
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


def render_small_table(df: pd.DataFrame, color_columns: dict[str, str] | None = None, *, bold_numbers: bool = True) -> None:
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
                classes.append("cm-number" if bold_numbers else "cm-number-soft")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            if pd.isna(value):
                rendered = ""
            elif col in color_columns:
                status_type = color_columns[col]
                if status_type == "auto":
                    status_type = "vigilance" if str(value).strip().startswith("Vigilance") else "risk"
                rendered = render_status_badge(value, status_type)
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
    st.markdown(f'<h3 class="cm-section-title">{escape(title)}</h3>', unsafe_allow_html=True)
    color_columns = {index_col: "vigilance"} if index_col == "Vigilance" else ({index_col: "risk"} if index_col == "Statut" else {})
    render_small_table(format_percent_column(dist_df), color_columns=color_columns)


def render_top_block(title: str, df: pd.DataFrame) -> None:
    st.markdown(f'<h3 class="cm-section-title">{escape(title)}</h3>', unsafe_allow_html=True)
    render_small_table(df)


def render_alert_block(title: str, df: pd.DataFrame) -> None:
    st.markdown(f'<h3 class="cm-section-title">{escape(title)}</h3>', unsafe_allow_html=True)
    render_small_table(df)




def display_value(value: object, kind: str | None = None) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return "Non renseigné"
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return "Non renseigné"
        return value.strftime("%d/%m/%Y")
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return "Non renseigné"
    if kind == "percent":
        if isinstance(value, (int, float, np.number)):
            return f"{float(value):.1%}".replace(".", ",")
    return text


def sync_view_state_from_query_params() -> None:
    query_params = st.query_params
    view = str(query_params.get("view", "")).strip().lower()
    societe_id = str(query_params.get("societe", "")).strip()
    siren = str(query_params.get("siren", "")).strip()

    if view == "analyse":
        st.session_state["cm_view"] = "analysis"
    elif view in {"dates-revue", "dates_revue", "datesrevue", "planning"}:
        st.session_state["cm_view"] = "review_dates"

    if view == "client" and societe_id and siren:
        st.session_state["cm_view"] = "client"
        st.session_state["cm_client_societe"] = societe_id
        st.session_state["cm_client_siren"] = siren


def siren_society_column(df: pd.DataFrame) -> str | None:
    if df is None or df.empty:
        return None
    if SOC_COL in df.columns:
        return SOC_COL
    if "Société" in df.columns:
        return "Société"
    return None


def reorder_table_columns_for_ui(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    columns = list(df.columns)
    preferred: list[str] = []
    for candidate in ["SIREN", "Dénomination", "Client", "Vigilance", "Risque", SOC_COL, "Société"]:
        if candidate in columns and candidate not in preferred:
            preferred.append(candidate)

    remaining = [col for col in columns if col not in preferred]
    return df[preferred + remaining]


def table_column_weight(column_name: str) -> float:
    if column_name in {"SIREN", "#", "Rang", "Nb", "%"}:
        return 0.95
    if column_name in {"Dénomination", "Client"}:
        return 1.8
    if column_name in {"Vigilance", "Risque", SOC_COL, "Société", "Statut EDD", "EDD"}:
        return 1.25
    if column_name in {"Motifs", "Commentaire"}:
        return 2.25
    return 1.1



def status_emoji(value: object, palette: str = "generic") -> str:
    text = display_value(value)
    lower = text.lower()
    if text == "-":
        return "⚪"
    if palette == "vigilance":
        if "critique" in lower:
            return "🔴"
        if "élev" in lower:
            return "🟠"
        if "modér" in lower:
            return "🟡"
        if "allég" in lower:
            return "🟢"
        if "aucune" in lower:
            return "🟢"
    if palette == "risk":
        if "avéré" in lower or "critique" in lower:
            return "🔴"
        if "élev" in lower or "fort" in lower:
            return "🟠"
        if "modér" in lower or "surveillance" in lower:
            return "🟡"
        if any(token in lower for token in ["faible", "levé", "aucun", "mitig", "clos", "normal"]):
            return "🟢"
    return "🔵"


def format_table_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    display_df = reorder_table_columns_for_ui(df.copy())
    for col in display_df.columns:
        series = display_df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            display_df[col] = pd.to_datetime(series, errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
            continue
        if col.startswith("%") or "%" in col:
            display_df[col] = series.map(lambda x: "" if pd.isna(x) else f"{float(x) * 100:.1f} %".replace('.', ','))
            continue
        if col == "SIREN":
            display_df[col] = series.apply(lambda x: f"↗ {display_value(x)}")
            continue
        if col == "Vigilance":
            display_df[col] = series.apply(lambda x: f"{status_emoji(x, 'vigilance')} {display_value(x)}")
            continue
        if col in {"Risque", "Statut"}:
            display_df[col] = series.apply(lambda x: f"{status_emoji(x, 'risk')} {display_value(x)}")
            continue
        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if non_null.empty:
                display_df[col] = series.map(lambda x: "" if pd.isna(x) else str(x))
            elif np.allclose(non_null.astype(float) % 1, 0):
                display_df[col] = series.map(lambda x: "" if pd.isna(x) else f"{int(round(float(x))):,}".replace(",", " "))
            else:
                display_df[col] = series.map(lambda x: "" if pd.isna(x) else f"{float(x):,.1f}".replace(",", " ").replace(".", ","))
            continue
        display_df[col] = series.apply(display_value)
    return display_df


def style_interactive_table(display_df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def style_cell(column_name: str, value: object) -> str:
        base = "padding: 0.42rem 0.55rem; text-align: center; vertical-align: middle; border-bottom: 1px solid rgba(22,58,89,0.08);"
        text = str(value)
        if column_name == "SIREN":
            return base + "color: #163A59; font-weight: 800; text-decoration: underline;"
        if column_name in {"Dénomination", "Client"}:
            return base + "text-align: center; font-weight: 700; color: #163A59;"
        if column_name == "Vigilance":
            if "🔴" in text:
                return base + "background-color: rgba(191, 36, 36, 0.10); color: #8A1F1F; font-weight: 700; border-radius: 999px;"
            if "🟠" in text:
                return base + "background-color: rgba(209, 98, 0, 0.10); color: #9A4D00; font-weight: 700; border-radius: 999px;"
            if "🟡" in text:
                return base + "background-color: rgba(184, 134, 11, 0.12); color: #7A5A00; font-weight: 700; border-radius: 999px;"
            if "🟢" in text:
                return base + "background-color: rgba(31, 122, 74, 0.10); color: #1F7A4A; font-weight: 700; border-radius: 999px;"
        if column_name in {"Risque", "Statut"}:
            if "🔴" in text:
                return base + "background-color: rgba(191, 36, 36, 0.10); color: #8A1F1F; font-weight: 700; border-radius: 999px;"
            if "🟠" in text:
                return base + "background-color: rgba(209, 98, 0, 0.10); color: #9A4D00; font-weight: 700; border-radius: 999px;"
            if "🟡" in text:
                return base + "background-color: rgba(184, 134, 11, 0.12); color: #7A5A00; font-weight: 700; border-radius: 999px;"
            if "🟢" in text:
                return base + "background-color: rgba(31, 122, 74, 0.10); color: #1F7A4A; font-weight: 700; border-radius: 999px;"
        if column_name.startswith("%") or "%" in column_name:
            return base + "font-variant-numeric: tabular-nums; font-weight: 700;"
        if column_name in {"Clients", "Vigilances critiques", "Risques avérés", "Nb", "#", "Rang", "Score", "Score priorité"}:
            return base + "font-variant-numeric: tabular-nums; font-weight: 700;"
        return base

    zebra = pd.DataFrame("", index=display_df.index, columns=display_df.columns)
    zebra.iloc[1::2, :] = "background-color: rgba(22,58,89,0.025);"

    styled = display_df.style
    styled = styled.set_table_styles([
        {"selector": "thead th", "props": [("background-color", "#163A59"), ("color", "white"), ("font-weight", "700"), ("text-transform", "uppercase"), ("font-size", "0.76rem"), ("letter-spacing", "0.08em"), ("text-align", "center"), ("border-bottom", "0")]},
        {"selector": "thead th.col_heading.level0", "props": [("background-color", "#163A59"), ("color", "white"), ("text-align", "center")]},
        {"selector": "thead tr", "props": [("background-color", "#163A59")]},
        {"selector": "tbody td", "props": [("background-color", "#ffffff"), ("text-align", "center")]},
    ])
    styled = styled.apply(lambda _: zebra, axis=None)
    styled = styled.apply(lambda s: [style_cell(s.name, v) for v in s], axis=0)
    return styled



def render_clickable_streamlit_table(
    df: pd.DataFrame,
    *,
    height: int | None = None,
    key_prefix: str = "table",
) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée disponible.")
        return

    raw_df = reorder_table_columns_for_ui(df.copy()).reset_index(drop=True)
    if len(raw_df) > 300:
        st.caption("Aperçu limité aux 300 premières lignes pour conserver une navigation fluide.")
        raw_df = raw_df.head(300).copy().reset_index(drop=True)

    display_df = format_table_display_dataframe(raw_df)
    society_col = siren_society_column(raw_df)

    if "SIREN" in raw_df.columns and society_col is not None:
        st.markdown(
            "<div class='cm-stream-note'><strong>↗ Cliquez directement sur une cellule de la colonne SIREN</strong> pour ouvrir la fiche client.</div>",
            unsafe_allow_html=True,
        )

    column_config: dict[str, object] = {}
    for col in display_df.columns:
        if col == "SIREN":
            column_config[col] = st.column_config.TextColumn("SIREN", width="small")
        elif col in {"Dénomination", "Client"}:
            column_config[col] = st.column_config.TextColumn(col, width="large")
        elif col in {"Vigilance", "Risque", "Statut", SOC_COL, "Société"}:
            column_config[col] = st.column_config.TextColumn(col, width="medium")
        elif col in {"Nb", "%", "#", "Rang", "Score", "Score priorité"}:
            column_config[col] = st.column_config.TextColumn(col, width="small")
        else:
            column_config[col] = st.column_config.TextColumn(col, width="medium")

    event = st.dataframe(
        style_interactive_table(display_df, raw_df),
        width="stretch",
        height=height if height is not None else "auto",
        hide_index=True,
        column_order=list(display_df.columns),
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-cell",
        row_height=40,
        key=f"cm_df_{key_prefix}",
    )

    cells = []
    if event is not None:
        try:
            cells = list(event.selection.get("cells", []))
        except Exception:
            cells = []

    if cells and society_col is not None and "SIREN" in raw_df.columns:
        row_idx, col_name = cells[0]
        if col_name == "SIREN" and 0 <= int(row_idx) < len(raw_df):
            row = raw_df.iloc[int(row_idx)]
            open_client_detail(str(row.get(society_col, "")), str(row.get("SIREN", "")))
            st.rerun()


def render_clickable_dataframe(
    df: pd.DataFrame,
    *,
    use_container_width: bool = True,
    height: int | None = None,
    hide_index: bool = True,
    key_prefix: str = "table",
) -> None:
    render_clickable_streamlit_table(df, height=height, key_prefix=key_prefix)


def render_clickable_styled_dataframe(
    styler: pd.io.formats.style.Styler,
    source_df: pd.DataFrame,
    *,
    use_container_width: bool = True,
    height: int | None = None,
    hide_index: bool = True,
    key_prefix: str = "table",
) -> None:
    render_clickable_streamlit_table(source_df, height=height, key_prefix=key_prefix)


def client_label(row: pd.Series) -> str:
    return f"{row.get('Dénomination', 'Client')} · {row.get('SIREN', '')} · {row.get(SOC_COL, '')}"


def open_client_detail(societe_id: str, siren: str) -> None:
    current_view = st.session_state.get("cm_view", "portfolio")
    if current_view == "client":
        current_view = st.session_state.get("cm_previous_view", "portfolio")
    st.session_state["cm_previous_view"] = current_view or "portfolio"
    st.session_state["cm_view"] = "client"
    st.session_state["cm_client_societe"] = societe_id
    st.session_state["cm_client_siren"] = siren


def return_from_client() -> None:
    st.session_state["cm_view"] = st.session_state.get("cm_previous_view", "portfolio") or "portfolio"
    st.session_state.pop("cm_client_societe", None)
    st.session_state.pop("cm_client_siren", None)
    st.query_params.clear()


def render_client_launcher(df: pd.DataFrame, key_prefix: str = "portfolio") -> None:
    clients = (
        df[[SOC_COL, "SIREN", "Dénomination"]]
        .drop_duplicates()
        .sort_values(["Dénomination", SOC_COL, "SIREN"], na_position="last")
        .reset_index(drop=True)
    )
    if clients.empty:
        return

    labels = clients.apply(client_label, axis=1).tolist()
    st.markdown('<h3 class="cm-section-title">Accès direct à la fiche client</h3>', unsafe_allow_html=True)
    col_a, col_b = st.columns([5, 1])
    with col_a:
        selected_label = st.selectbox(
            "Choisir un client",
            options=labels,
            key=f"{key_prefix}_client_selector",
            help="Recherchez un client par dénomination, SIREN ou société puis ouvrez sa fiche détaillée.",
        )
    with col_b:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        if st.button("Ouvrir", type="primary", key=f"{key_prefix}_open_client_btn"):
            row = clients.loc[labels.index(selected_label)]
            open_client_detail(str(row[SOC_COL]), str(row["SIREN"]))
            st.rerun()


INDICATOR_SUFFIXES = [
    ("Date de dernière mise à jour", "Date de mise à jour"),
    ("Date de mise à jour", "Date de mise à jour"),
    ("Date de création", "Date de création"),
    ("Référence dossier source", "Référence du dossier source"),
    ("Pièce associée", "Pièce associée"),
    ("Justificatif", "Justificatif"),
    ("Commentaire", "Commentaire"),
    ("Analyste", "Analyste"),
    ("Valideur", "Valideur"),
    ("Valeur", "Valeur"),
    ("valeur", "Valeur"),
    ("Statut", "Statut"),
    ("statut", "Statut"),
]


def indicator_group_map(columns: list[str]) -> dict[str, dict[str, str]]:
    groups: dict[str, dict[str, str]] = {}
    for raw_col in columns:
        col = " ".join(str(raw_col).replace("\ufeff", "").split())
        if col in {SOC_COL, "SIREN", "Dénomination"}:
            continue
        for suffix, field_name in INDICATOR_SUFFIXES:
            if col.endswith(suffix):
                indicator_name = col[: -len(suffix)].strip()
                if indicator_name:
                    groups.setdefault(indicator_name, {})[field_name] = raw_col
                break
    return groups


def build_indicator_table_from_series(row: pd.Series) -> pd.DataFrame:
    groups = indicator_group_map(list(row.index))
    output_rows = []
    for indicator_name, mapping in groups.items():
        item = {
            "Indicateur": indicator_name,
            "Valeur": row.get(mapping.get("Valeur"), pd.NA),
            "Statut": row.get(mapping.get("Statut"), pd.NA),
            "Date de création": row.get(mapping.get("Date de création"), pd.NA),
            "Date de mise à jour": row.get(mapping.get("Date de mise à jour"), pd.NA),
            "Commentaire": row.get(mapping.get("Commentaire"), pd.NA),
            "Justificatif": row.get(mapping.get("Justificatif"), pd.NA),
            "Analyste": row.get(mapping.get("Analyste"), pd.NA),
            "Valideur": row.get(mapping.get("Valideur"), pd.NA),
            "Pièce associée": row.get(mapping.get("Pièce associée"), pd.NA),
            "Référence du dossier source": row.get(mapping.get("Référence du dossier source"), pd.NA),
        }
        non_key_values = [item[k] for k in item if k != "Indicateur"]
        if all(pd.isna(v) or not str(v).strip() for v in non_key_values):
            continue
        output_rows.append(item)

    table = pd.DataFrame(output_rows)
    if table.empty:
        return table

    for date_col in ["Date de création", "Date de mise à jour"]:
        table[date_col] = pd.to_datetime(table[date_col], errors="coerce")

    table = table.sort_values(["Date de mise à jour", "Indicateur"], ascending=[False, True], na_position="last")
    return table.reset_index(drop=True)


def render_info_cards(items: list[tuple[str, object, str | None]]) -> None:
    html = ["<div class='cm-client-grid'>"]
    for label, value, kind in items:
        html.append(
            "<div class='cm-client-field'>"
            f"<div class='cm-client-field-label'>{escape(str(label))}</div>"
            f"<div class='cm-client-field-value'>{escape(display_value(value, kind))}</div>"
            "</div>"
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_indicator_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Aucun indicateur disponible pour ce client.")
        return

    formatted = df.copy()
    for date_col in ["Date de création", "Date de mise à jour"]:
        if date_col in formatted.columns:
            formatted[date_col] = formatted[date_col].apply(display_value)
    for col in formatted.columns:
        if col not in {"Indicateur", "Valeur", "Statut"}:
            formatted[col] = formatted[col].apply(lambda v: display_value(v))
    render_small_table(formatted, color_columns={"Statut": "auto"})


def render_client_header(client_row: pd.Series) -> None:
    st.markdown('<div class="cm-client-breadcrumb">Portefeuille &gt; Client &gt; Fiche client</div>', unsafe_allow_html=True)
    header_cards = [
        ("Date calcul du risque", client_row.get("Date calcul du risque"), None),
        ("Dernière mise à jour vigilance", client_row.get("Vigilance Date de mise à jour"), None),
        ("Dernière revue", client_row.get("Date dernière revue"), None),
        ("Prochaine revue", client_row.get("Date prochaine revue"), None),
    ]
    badges = [
        render_status_badge(display_value(client_row.get("Vigilance")), "vigilance"),
        render_status_badge(display_value(client_row.get("Risque")), "risk"),
        render_status_badge(display_value(client_row.get("Statut EDD")), "edd"),
    ]
    cards_html = []
    for label, value, kind in header_cards:
        cards_html.append(
            "<div class='cm-client-hero-card'>"
            f"<div class='cm-client-hero-label'>{escape(label)}</div>"
            f"<div class='cm-client-hero-value'>{escape(display_value(value, kind))}</div>"
            "</div>"
        )
    st.markdown(
        "<div class='cm-client-hero'>"
        "<div class='cm-client-title-row'>"
        "<div>"
        f"<div class='cm-client-title'>{escape(display_value(client_row.get('Dénomination')))}</div>"
        f"<div class='cm-client-subtitle'>SIREN : {escape(display_value(client_row.get('SIREN')))} · Société : {escape(display_value(client_row.get(SOC_COL)))}</div>"
        "</div>"
        "</div>"
        f"<div class='cm-client-badges'>{''.join(badges)}</div>"
        f"<div class='cm-client-hero-grid'>{''.join(cards_html)}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_client_base_tab(client_row: pd.Series) -> None:
    base_items = [
        ("Identifiant client / SIREN", client_row.get("SIREN"), None),
        ("Dénomination", client_row.get("Dénomination"), None),
        ("Segment", client_row.get("Segment"), None),
        ("Pays de résidence", client_row.get("Pays de résidence"), None),
        ("Produit principal", client_row.get("Produit(service) principal"), None),
        ("Canal principal", client_row.get("Canal d’opérations principal 12 mois"), None),
        ("Score importé", client_row.get("Vigilance valeur"), "percent"),
        ("Niveau de vigilance", client_row.get("Vigilance"), None),
        ("Statut de risque", client_row.get("Risque"), None),
        ("Date calcul du risque", client_row.get("Date calcul du risque"), None),
        ("Date et heure de synchronisation", client_row.get("Vigilance Date de mise à jour"), None),
        ("Identifiant / référence source", client_row.get("Référence du dossier source"), None),
        ("Code NAF", client_row.get("Code NAF (nomenclature INSEE)"), None),
        ("Catégorie juridique", client_row.get("Catégorie Juridique"), None),
        ("Nationalité", client_row.get("Nationalité"), None),
        ("Canal onboarding", client_row.get("Canal distribution On boarding"), None),
        ("Cross border", client_row.get("Cross border"), "percent"),
        ("Cash intensité", client_row.get("Cash intensité"), "percent"),
        ("Analyste", client_row.get("Analyste"), None),
        ("Valideur", client_row.get("Valideur"), None),
        ("Date dernière revue", client_row.get("Date dernière revue"), None),
        ("Date prochaine revue", client_row.get("Date prochaine revue"), None),
        ("Justificatif complet", client_row.get("Flag justificatif complet"), None),
    ]
    render_info_cards(base_items)


def apply_indicator_local_filters(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    if df.empty:
        return df
    c1, c2, c3 = st.columns(3)
    statuses = ["Tous"] + non_empty_sorted(df["Statut"].dropna().unique()) if "Statut" in df.columns else ["Tous"]
    with c1:
        selected_status = st.selectbox("Statut", statuses, key=f"{key_prefix}_status")
    with c2:
        comment_filter = st.selectbox(
            "Commentaire",
            ["Tous", "Avec commentaire", "Sans commentaire"],
            key=f"{key_prefix}_comment",
        )
    with c3:
        evidence_filter = st.selectbox(
            "Justificatif",
            ["Tous", "Avec justificatif", "Sans justificatif"],
            key=f"{key_prefix}_evidence",
        )

    filtered = df.copy()
    if selected_status != "Tous":
        filtered = filtered[filtered["Statut"] == selected_status]
    if comment_filter == "Avec commentaire":
        filtered = filtered[filtered["Commentaire"].astype(str).str.strip().ne("") & filtered["Commentaire"].notna()]
    elif comment_filter == "Sans commentaire":
        filtered = filtered[filtered["Commentaire"].isna() | filtered["Commentaire"].astype(str).str.strip().eq("")]
    if evidence_filter == "Avec justificatif":
        filtered = filtered[filtered["Justificatif"].astype(str).str.strip().ne("") & filtered["Justificatif"].notna()]
    elif evidence_filter == "Sans justificatif":
        filtered = filtered[filtered["Justificatif"].isna() | filtered["Justificatif"].astype(str).str.strip().eq("")]
    return filtered.reset_index(drop=True)


def render_client_indicators_tab(indicators_row: pd.Series) -> None:
    indicator_table = build_indicator_table_from_series(indicators_row)
    indicator_table = apply_indicator_local_filters(indicator_table, "client_current_indicators")
    render_indicator_table(indicator_table)
    if not indicator_table.empty:
        st.download_button(
            label="Exporter les indicateurs courants (.csv)",
            data=dataframe_to_csv_bytes(indicator_table),
            file_name="fiche_client_indicateurs.csv",
            mime="text/csv",
            type="secondary",
            key="export_current_indicators",
        )


def render_client_history_tab(history_rows: pd.DataFrame) -> None:
    if history_rows.empty:
        st.info("Aucun état historique n'est disponible pour ce client.")
        return

    rows = history_rows.copy()
    date_cols = [c for c in rows.columns if "Date de mise à jour" in c]
    if date_cols:
        for col in date_cols:
            rows[col] = pd.to_datetime(rows[col], errors="coerce")
        rows["_latest_history_date"] = rows[date_cols].max(axis=1)
        rows = rows.sort_values("_latest_history_date", ascending=False, na_position="last").drop(columns=["_latest_history_date"])
    else:
        rows = rows.copy()

    st.caption("Les états antérieurs sont présentés séparément, du plus récent au plus ancien, avec la même structure que l'état courant.")
    for idx, (_, hist_row) in enumerate(rows.iterrows(), start=1):
        hist_table = build_indicator_table_from_series(hist_row)
        if hist_table.empty:
            continue
        latest = hist_table["Date de mise à jour"].max() if "Date de mise à jour" in hist_table.columns else pd.NaT
        suffix = f" · dernière mise à jour max {display_value(latest)}" if pd.notna(latest) else ""
        with st.expander(f"État historique {idx}{suffix}", expanded=(idx == 1)):
            render_indicator_table(hist_table)


def render_client_edd_tab(client_row: pd.Series, history_rows: pd.DataFrame) -> None:
    left, right = st.columns([1.3, 1.0])
    with left:
        st.markdown('<h3 class="cm-section-title">EDD courant</h3>', unsafe_allow_html=True)
        edd_items = [
            ("Statut EDD", client_row.get("Statut EDD"), None),
            ("Analyste", client_row.get("Analyste"), None),
            ("Valideur", client_row.get("Valideur"), None),
            ("Date dernière revue", client_row.get("Date dernière revue"), None),
            ("Date prochaine revue", client_row.get("Date prochaine revue"), None),
            ("Justificatif complet", client_row.get("Flag justificatif complet"), None),
            ("Conclusion synthétique", client_row.get("Motifs"), None),
        ]
        render_info_cards(edd_items)
    with right:
        st.markdown('<h3 class="cm-section-title">Pilotage synthétique</h3>', unsafe_allow_html=True)
        pilotage = pd.DataFrame(
            [
                ["Score priorité", display_value(client_row.get("Score priorité"))],
                ["Nb historique", display_value(client_row.get("Nb historique"))],
                ["Nb risque avéré", display_value(client_row.get("Nb Risque avéré"))],
                ["Nb risque potentiel", display_value(client_row.get("Nb Risque potentiel"))],
                ["Nb risque mitigé", display_value(client_row.get("Nb Risque mitigé"))],
                ["Nb risque levé", display_value(client_row.get("Nb Risque levé"))],
                ["Nb non calculable", display_value(client_row.get("Nb Non calculable"))],
                ["Motifs / alertes", display_value(client_row.get("Motifs"))],
            ],
            columns=["Indicateur", "Valeur"],
        )
        render_small_table(pilotage)

    st.markdown('<h3 class="cm-section-title">Historique des validations et audit trail</h3>', unsafe_allow_html=True)
    if history_rows.empty:
        st.markdown(
            "<div class='cm-empty-note'>Le jeu 01 / 02 / 03 publié ne contient pas de journal d'événements de gouvernance distinct. "
            "Cette zone affichera l'audit trail consolidé dès qu'un flux dédié sera disponible.</div>",
            unsafe_allow_html=True,
        )
    else:
        latest_dates = []
        date_cols = [c for c in history_rows.columns if "Date de mise à jour" in c]
        if date_cols:
            tmp = history_rows.copy()
            for col in date_cols:
                tmp[col] = pd.to_datetime(tmp[col], errors="coerce")
            latest_dates = tmp[date_cols].max(axis=1).sort_values(ascending=False).tolist()
        audit_rows = pd.DataFrame(
            [
                ["Historique indicateurs disponible", len(history_rows)],
                ["Dernier état historique le plus récent", display_value(latest_dates[0]) if latest_dates else "Non renseigné"],
                ["Observation", "Le flux publié ne fournit pas encore le détail des validations, actions, motifs et justificatifs de gouvernance."],
            ],
            columns=["Élément", "Valeur"],
        )
        render_small_table(audit_rows)


def render_client_screen(
    portfolio: pd.DataFrame,
    indicators: pd.DataFrame,
    history: pd.DataFrame,
    selected_societies: list[str],
    allowed_societies: list[str],
) -> None:
    societe_id = st.session_state.get("cm_client_societe")
    siren = st.session_state.get("cm_client_siren")
    if not societe_id or not siren:
        return_from_client()
        st.rerun()

    allowed_set = {str(s).strip().upper() for s in allowed_societies}
    if str(societe_id).strip().upper() not in allowed_set:
        st.error("Cette fiche client n'appartient pas à votre périmètre autorisé.")
        if st.button("Retour", key="btn_back_unauthorized"):
            return_from_client()
            st.rerun()
        return

    client_rows = portfolio[(portfolio[SOC_COL] == societe_id) & (portfolio["SIREN"] == siren)]
    if client_rows.empty:
        st.warning("Le client demandé n'est plus disponible dans le jeu actif.")
        if st.button("Retour", key="btn_back_missing"):
            return_from_client()
            st.rerun()
        return

    client_row = client_rows.iloc[0]
    indicator_rows = indicators[(indicators[SOC_COL] == societe_id) & (indicators["SIREN"] == siren)]
    history_rows = history[(history[SOC_COL] == societe_id) & (history["SIREN"] == siren)]

    top_left, top_right = st.columns([6, 1])
    with top_left:
        render_client_header(client_row)
    with top_right:
        st.markdown("<div style='height: 0.3rem'></div>", unsafe_allow_html=True)
        if st.button("← Retour", type="secondary", key="back_to_portfolio_top"):
            return_from_client()
            st.rerun()

    tabs = st.tabs(["Données de base", "Indicateurs", "Historique des indicateurs", "EDD et historique"])
    with tabs[0]:
        render_client_base_tab(client_row)
    with tabs[1]:
        if indicator_rows.empty:
            st.info("Aucun indicateur courant n'est disponible pour ce client.")
        else:
            render_client_indicators_tab(indicator_rows.iloc[0])
    with tabs[2]:
        render_client_history_tab(history_rows)
    with tabs[3]:
        render_client_edd_tab(client_row, history_rows)



def render_primary_navigation(current_view: str) -> str:
    label_map = {
        "portfolio": "Portefeuille",
        "analysis": "Analyse",
        "review_dates": "Planification des revues",
        "review_simulations": "Revues & Simulations",
    }
    options = ["Portefeuille", "Analyse", "Planification des revues", "Revues & Simulations"]
    current_label = label_map.get(current_view, "Portefeuille")
    selection = st.radio(
        "Navigation principale",
        options=options,
        horizontal=True,
        label_visibility="collapsed",
        index=options.index(current_label),
        key="cm_main_nav_radio",
    )
    if selection == "Analyse":
        return "analysis"
    if selection == "Planification des revues":
        return "review_dates"
    if selection == "Revues & Simulations":
        return "review_simulations"
    return "portfolio"


def open_analysis_view() -> None:
    st.session_state["cm_view"] = "analysis"
    st.query_params.clear()


def open_review_dates_view() -> None:
    st.session_state["cm_view"] = "review_dates"
    st.query_params.clear()


def open_review_simulations_view() -> None:
    st.session_state["cm_view"] = "review_simulations"
    st.query_params.clear()


def open_portfolio_view() -> None:
    st.session_state["cm_view"] = "portfolio"
    st.query_params.clear()


def analysis_dimension_mapping(df: pd.DataFrame) -> dict[str, str]:
    candidates = {
        "Société": SOC_COL,
        "Segment": "Segment",
        "Pays": "Pays de résidence",
        "Produit": "Produit(service) principal",
        "Canal": "Canal d’opérations principal 12 mois",
        "Vigilance": "Vigilance",
        "Risque": "Risque",
        "Statut EDD": "Statut EDD",
        "Analyste": "Analyste",
        "Valideur": "Valideur",
        "Nationalité": "Nationalité",
        "Catégorie juridique": "Catégorie Juridique",
        "Cash intensité": "Cash intensité Statut",
        "Cross-border": "Cross border",
    }
    return {label: column for label, column in candidates.items() if column in df.columns}



def analysis_measure_mapping(df: pd.DataFrame) -> dict[str, str]:
    return {
        "Clients": "clients",
        "Part du portefeuille": "share",
        "Justificatifs incomplets": "missing_docs",
        "Sans prochaine revue": "without_next_review",
        "Revue trop ancienne": "stale_review",
        "Cross-border élevé": "cross_border_high",
        "Cash intensité élevée": "cash_intensity_high",
    }


def compute_measure_series(df: pd.DataFrame, measure_key: str) -> pd.Series:
    if df.empty:
        return pd.Series(dtype="float64")
    if measure_key == "clients":
        return pd.Series(1, index=df.index, dtype="int64")
    if measure_key == "critical_vigilance":
        return df.get("Vigilance", pd.Series(index=df.index, dtype="string")).isin(CRITICAL_VIGILANCE).astype(int)
    if measure_key == "confirmed_risk":
        return df.get("Risque", pd.Series(index=df.index, dtype="string")).eq("Risque avéré").astype(int)
    if measure_key == "edd_open":
        edd = df.get("Statut EDD", pd.Series(index=df.index, dtype="string")).astype("string").fillna("")
        return edd.str.lower().str.contains("ouvrir|ouverte|ouvert|cours", regex=True).astype(int)
    if measure_key == "missing_docs":
        return df.get("Flag justificatif complet", pd.Series(index=df.index, dtype="string")).ne("Oui").astype(int)
    if measure_key == "without_next_review":
        return df.get("Date prochaine revue", pd.Series(index=df.index, dtype="datetime64[ns]")).isna().astype(int)
    if measure_key == "cross_border":
        return df.get("Cross border", pd.Series(index=df.index, dtype="float64")).ge(0.25).fillna(False).astype(int)
    if measure_key == "history_cases":
        return df.get("Nb historique", pd.Series(index=df.index, dtype="float64")).fillna(0).gt(0).astype(int)
    return pd.Series(1, index=df.index, dtype="int64")


def build_analysis_main_table(
    df: pd.DataFrame,
    line_col: str,
    line_label: str,
    measure_key: str,
    measure_label: str,
    sort_desc: bool = True,
) -> tuple[pd.DataFrame, str]:
    if df.empty:
        return pd.DataFrame(columns=[line_label, "Clients", "% portefeuille"]), ""

    work = df.copy()
    work[line_col] = work.get(line_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    work["cm_measure"] = compute_measure_series(work, measure_key).astype(float)
    work["cm_edd_open"] = work.get("Statut EDD", pd.Series(index=work.index, dtype="string")).astype("string").fillna("").str.lower().str.contains("ouvrir|ouverte|ouvert|cours", regex=True).astype(int)
    work["cm_without_next_review"] = work.get("Date prochaine revue", pd.Series(index=work.index, dtype="datetime64[ns]")).isna().astype(int)
    work["cm_missing_docs"] = work.get("Flag justificatif complet", pd.Series(index=work.index, dtype="string")).astype("string").fillna("").ne("Oui").astype(int)
    work["cm_gov_gap"] = (
        work.get("Alerte justificatif incomplet", pd.Series(0, index=work.index)).fillna(0).astype(int)
        + work.get("Alerte revue trop ancienne", pd.Series(0, index=work.index)).fillna(0).astype(int)
        + work.get("Alerte sans prochaine revue", pd.Series(0, index=work.index)).fillna(0).astype(int)
    )

    total_clients = max(int(work["cm_client_key"].nunique()), 1)
    total_measure = float(work["cm_measure"].sum())

    grouped = (
        work.groupby(line_col, dropna=False)
        .agg(
            Clients=("cm_client_key", "nunique"),
            Mesure=("cm_measure", "sum"),
            Vigilance_renforcee=("Vigilance", lambda s: s.isin(CRITICAL_VIGILANCE).sum()),
            Risques_averes=("Risque", lambda s: s.eq("Risque avéré").sum()),
            EDD_ouvertes=("cm_edd_open", "sum"),
            Sans_prochaine_revue=("cm_without_next_review", "sum"),
            Justificatifs_incomplets=("cm_missing_docs", "sum"),
            Ecarts_gouvernance=("cm_gov_gap", "sum"),
        )
        .reset_index()
        .rename(columns={line_col: line_label})
    )
    grouped["% portefeuille"] = grouped["Clients"].div(total_clients).fillna(0)
    grouped["% indicateur"] = grouped["Mesure"].div(total_measure).fillna(0) if total_measure else 0.0

    grouped = grouped.rename(columns={
        "Vigilance_renforcee": "Vigilance renforcée",
        "Risques_averes": "Risques avérés",
        "EDD_ouvertes": "EDD ouvertes",
        "Sans_prochaine_revue": "Sans prochaine revue",
        "Justificatifs_incomplets": "Justificatifs incomplets",
        "Ecarts_gouvernance": "Alertes de gouvernance (calculé)",
    })

    if measure_key in {"clients", "share"}:
        result = grouped[[
            line_label,
            "Clients",
            "% portefeuille",
            "Vigilance renforcée",
            "Risques avérés",
            "EDD ouvertes",
            "Sans prochaine revue",
            "Justificatifs incomplets",
            "Alertes de gouvernance (calculé)",
        ]].copy()
        sort_col = "Clients" if sort_desc else line_label
        ascending = False if sort_desc else True
        result = result.sort_values(sort_col, ascending=ascending, kind="stable")
        return result.reset_index(drop=True), f"Lecture du portefeuille par {line_label.lower()} sur le périmètre filtré."

    safe_measure_label = measure_label if measure_label not in grouped.columns else f"{measure_label} (indicateur)"
    grouped = grouped.rename(columns={"Mesure": safe_measure_label})
    result = grouped[[
        line_label,
        "Clients",
        "% portefeuille",
        safe_measure_label,
        "% indicateur",
        "Vigilance renforcée",
        "Risques avérés",
        "EDD ouvertes",
        "Sans prochaine revue",
        "Justificatifs incomplets",
        "Alertes de gouvernance (calculé)",
    ]].copy()
    sort_col = safe_measure_label if sort_desc else line_label
    ascending = False if sort_desc else True
    result = result.sort_values(sort_col, ascending=ascending, kind="stable")
    return result.reset_index(drop=True), f"Lecture du portefeuille par {line_label.lower()} avec l’indicateur « {measure_label} »."


def build_analysis_trend_table(df: pd.DataFrame) -> pd.DataFrame:
    def monthly_count(series: pd.Series, label: str) -> pd.Series:
        if series is None or series.empty:
            return pd.Series(dtype="int64", name=label)
        clean = pd.to_datetime(series, errors="coerce").dropna()
        if clean.empty:
            return pd.Series(dtype="int64", name=label)
        month = clean.dt.to_period("M").dt.to_timestamp()
        return month.value_counts().sort_index().rename(label)

    frames = [
        monthly_count(df.get("Vigilance Date de mise à jour"), "Mises à jour vigilance"),
        monthly_count(df.get("Date dernière revue"), "Dernières revues"),
        monthly_count(df.get("Date prochaine revue"), "Prochaines revues"),
    ]
    combined = pd.concat(frames, axis=1).fillna(0).sort_index()
    if combined.empty:
        return pd.DataFrame(columns=["Mois", "Mises à jour vigilance", "Dernières revues", "Prochaines revues", "% clients revus"])
    combined = combined.tail(6)
    combined["% clients revus"] = combined["Dernières revues"].div(max(len(df), 1))
    combined = combined.reset_index().rename(columns={"index": "Mois"})
    combined["Mois"] = pd.to_datetime(combined["Mois"]).dt.strftime("%Y-%m")
    return combined


def build_analysis_group_table(
    df: pd.DataFrame,
    group_col: str,
    group_label: str,
    measure_key: str,
    measure_label: str,
    *,
    sort_desc: bool = True,
    top_n: int = 12,
) -> tuple[pd.DataFrame, str]:
    if df.empty:
        return pd.DataFrame(columns=[group_label, "Clients", "% portf."]), ""
    work = df.copy()
    work[group_col] = work.get(group_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    work["cm_measure"] = compute_measure_series(work, measure_key).astype(float)

    total_clients = max(int(work["cm_client_key"].nunique()), 1)
    total_measure = float(work["cm_measure"].sum())

    grouped = (
        work.groupby(group_col, dropna=False)
        .agg(
            Clients=("cm_client_key", "nunique"),
            Mesure=("cm_measure", "sum"),
            Vigilance=("Vigilance", lambda s: s.isin(CRITICAL_VIGILANCE).sum()),
            Risque=("Risque", lambda s: s.eq("Risque avéré").sum()),
        )
        .reset_index()
        .rename(columns={group_col: group_label, "Vigilance": "Vigilances critiques", "Risque": "Risques avérés"})
    )
    grouped["% portf."] = grouped["Clients"].div(total_clients).fillna(0)

    if measure_key in {"share", "clients"}:
        grouped = grouped[[group_label, "Clients", "% portf.", "Vigilances critiques", "Risques avérés"]]
        sort_col = "Clients" if sort_desc else group_label
        ascending = False if sort_desc else True
        grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
        return grouped.head(top_n).reset_index(drop=True), f"Répartition simple par {group_label.lower()} sur le périmètre filtré."

    safe_measure_label = measure_label if measure_label not in grouped.columns else f"{measure_label} (mesure)"
    grouped[safe_measure_label] = grouped["Mesure"]
    grouped["% mesure"] = grouped["Mesure"].div(total_measure).fillna(0) if total_measure else 0.0
    grouped = grouped[[group_label, "Clients", "% portf.", safe_measure_label, "% mesure", "Vigilances critiques", "Risques avérés"]]
    sort_col = safe_measure_label if sort_desc else group_label
    ascending = False if sort_desc else True
    grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
    return grouped.head(top_n).reset_index(drop=True), f"Répartition simple par {group_label.lower()} ; la mesure choisie est affichée séparément."


def build_analysis_cross_table(
    df: pd.DataFrame,
    row_col: str,
    row_label: str,
    col_col: str,
    col_label: str,
    measure_key: str,
    measure_label: str,
    *,
    sort_desc: bool = True,
    top_n: int = 14,
    focus_row_value: str | None = None,
    focus_col_value: str | None = None,
) -> tuple[pd.DataFrame, str]:
    if df.empty:
        return pd.DataFrame(columns=[row_label, col_label, "Clients"]), ""
    work = df.copy()
    work[row_col] = work.get(row_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work[col_col] = work.get(col_col).fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})
    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    work["cm_measure"] = compute_measure_series(work, measure_key).astype(float)
    total_clients = max(int(work["cm_client_key"].nunique()), 1)
    total_measure = float(work["cm_measure"].sum())

    grouped = (
        work.groupby([row_col, col_col], dropna=False)
        .agg(
            Clients=("cm_client_key", "nunique"),
            Mesure=("cm_measure", "sum"),
            Vigilance=("Vigilance", lambda s: s.isin(CRITICAL_VIGILANCE).sum()),
            Risque=("Risque", lambda s: s.eq("Risque avéré").sum()),
        )
        .reset_index()
        .rename(columns={row_col: row_label, col_col: col_label, "Vigilance": "Vigilances critiques", "Risque": "Risques avérés"})
    )
    grouped["% portf."] = grouped["Clients"].div(total_clients).fillna(0)
    focus_active = focus_row_value not in {None, "", "Tous"} and focus_col_value not in {None, "", "Tous"}
    focus_mask = None
    if focus_active:
        focus_mask = (
            grouped[row_label].astype(str).eq(str(focus_row_value))
            & grouped[col_label].astype(str).eq(str(focus_col_value))
        )

    if measure_key in {"share", "clients"}:
        grouped = grouped[[row_label, col_label, "Clients", "% portf.", "Vigilances critiques", "Risques avérés"]]
        sort_col = "Clients" if sort_desc else row_label
        ascending = False if sort_desc else True
        grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
        if focus_active:
            focused = grouped.loc[focus_mask].reset_index(drop=True)
            caption = f"Croisement sélectionné : {row_label} = {focus_row_value} | {col_label} = {focus_col_value}."
            return focused, caption
        return grouped.head(top_n).reset_index(drop=True), f"Croisements majeurs entre {row_label.lower()} et {col_label.lower()}."

    safe_measure_label = measure_label if measure_label not in grouped.columns else f"{measure_label} (mesure)"
    grouped[safe_measure_label] = grouped["Mesure"]
    grouped["% mesure"] = grouped["Mesure"].div(total_measure).fillna(0) if total_measure else 0.0
    grouped = grouped[[row_label, col_label, "Clients", "% portf.", safe_measure_label, "% mesure", "Vigilances critiques", "Risques avérés"]]
    sort_col = safe_measure_label if sort_desc else row_label
    ascending = False if sort_desc else True
    grouped = grouped.sort_values(sort_col, ascending=ascending, kind="stable")
    if focus_active:
        focused = grouped.loc[focus_mask].reset_index(drop=True)
        caption = f"Croisement sélectionné : {row_label} = {focus_row_value} | {col_label} = {focus_col_value}."
        return focused, caption
    return grouped.head(top_n).reset_index(drop=True), f"Croisements majeurs entre {row_label.lower()} et {col_label.lower()} avec la mesure sélectionnée."


def render_analysis_panel_header(title: str, caption: str | None = None) -> None:
    st.markdown(f"<div class='cm-table-panel-title'>{escape(title)}</div>", unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='cm-table-panel-caption'>{escape(caption)}</div>", unsafe_allow_html=True)



def render_selectable_analysis_table(
    df: pd.DataFrame,
    *,
    key_prefix: str,
    height: int = 420,
) -> tuple[str, list[dict[str, object]] | None]:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return "empty", None

    raw_df = df.copy().reset_index(drop=True)
    display_df = format_table_display_dataframe(raw_df)

    hint_left, hint_right, hint_clear = st.columns([6.0, 2.3, 1.5])
    with hint_left:
        st.markdown(
            "<div class='cm-analysis-hint-text'>Cliquez directement sur une ou plusieurs lignes du tableau pour définir le focus analytique et mettre à jour les clients sous-jacents.</div>",
            unsafe_allow_html=True,
        )
    with hint_right:
        st.markdown(
            "<div class='cm-analysis-hint-action'><a class='cm-analysis-jump-btn' href='#clients-sous-jacents'>Voir les clients sous-jacents</a></div>",
            unsafe_allow_html=True,
        )
    reset_counter_key = f"analysis_table_reset_counter_{key_prefix}"
    with hint_clear:
        st.markdown("<div style='height:0.15rem'></div>", unsafe_allow_html=True)
        if st.button("Effacer le focus", key=f"analysis_clear_{key_prefix}", type="secondary"):
            st.session_state[reset_counter_key] = int(st.session_state.get(reset_counter_key, 0)) + 1
            return "cleared", None

    column_config: dict[str, object] = {}
    for col in display_df.columns:
        if col in {"Vigilance", "Risque"}:
            column_config[col] = st.column_config.TextColumn(col, width="medium")
        elif col in {"EDD", "Segment", "Produit", "Analyste", "Valideur"}:
            column_config[col] = st.column_config.TextColumn(col, width="medium")
        elif col in {"Pays", "Canal"}:
            column_config[col] = st.column_config.TextColumn(col, width="small")
        else:
            column_config[col] = st.column_config.TextColumn(col, width="medium")

    table_version = int(st.session_state.get(reset_counter_key, 0))
    event = st.dataframe(
        style_interactive_table(display_df, raw_df),
        width="stretch",
        height=height,
        hide_index=True,
        column_order=list(display_df.columns),
        column_config=column_config,
        on_select="rerun",
        selection_mode="multi-row",
        row_height=40,
        key=f"cm_analysis_select_{key_prefix}_{table_version}",
    )

    selected_rows: list[int] = []
    if event is not None:
        try:
            selected_rows = [int(i) for i in event.selection.get("rows", [])]
        except Exception:
            selected_rows = []

    if selected_rows:
        valid_rows = [i for i in selected_rows if 0 <= i < len(raw_df)]
        if valid_rows:
            selected_records = raw_df.iloc[valid_rows].to_dict(orient="records")
            return "selected", selected_records

    if event is not None and "analysis_focus_selection" in st.session_state:
        return "cleared", None
    return "unchanged", None



def render_analysis_simple_table(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return
    display_df = format_table_for_display(df)
    render_small_table(display_df)

def apply_analysis_table_controls(
    df: pd.DataFrame,
    *,
    line_label: str,
    default_sort_label: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    if df is None or df.empty:
        return df, {"sort_by": default_sort_label, "ascending": False, "search": "", "selected_labels": []}

    work = df.copy().reset_index(drop=True)
    control_cols = st.columns([1.4, 1.8, 1.1, 1.0, 0.9])
    with control_cols[0]:
        search_value = st.text_input(
            "Recherche",
            value=st.session_state.get("analysis_table_search", ""),
            key="analysis_table_search",
            placeholder=f"Filtrer {line_label.lower()}…",
        )
    with control_cols[1]:
        available_labels = non_empty_sorted(work[line_label].astype(str).unique())
        selected_labels = st.multiselect(
            f"{line_label}",
            options=available_labels,
            default=st.session_state.get("analysis_table_values", []),
            key="analysis_table_values",
            placeholder="Toutes les valeurs",
        )
    sort_options = [c for c in work.columns if c != line_label]
    if default_sort_label not in sort_options:
        default_sort_label = sort_options[0] if sort_options else line_label
    if st.session_state.get("analysis_table_sort_by") not in sort_options:
        st.session_state["analysis_table_sort_by"] = default_sort_label
    with control_cols[2]:
        sort_by = st.selectbox(
            "Trier par",
            options=sort_options,
            index=sort_options.index(st.session_state.get("analysis_table_sort_by", default_sort_label)) if sort_options else 0,
            key="analysis_table_sort_by",
        ) if sort_options else default_sort_label
    order_options = ["Décroissant", "Croissant"]
    if st.session_state.get("analysis_table_sort_order") not in order_options:
        st.session_state["analysis_table_sort_order"] = "Décroissant"
    with control_cols[3]:
        sort_order = st.selectbox(
            "Ordre",
            options=order_options,
            index=order_options.index(st.session_state.get("analysis_table_sort_order", "Décroissant")),
            key="analysis_table_sort_order",
        )
    with control_cols[4]:
        top_n = st.number_input(
            "Top N",
            min_value=0,
            max_value=max(len(work), 1),
            value=min(int(st.session_state.get("analysis_table_top_n", min(len(work), 12))), max(len(work), 1)),
            step=1,
            key="analysis_table_top_n",
            help="0 = toutes les lignes",
        )

    if search_value:
        mask = work[line_label].astype(str).str.contains(str(search_value), case=False, na=False)
        work = work[mask]
    if selected_labels:
        work = work[work[line_label].astype(str).isin([str(v) for v in selected_labels])]

    ascending = sort_order == "Croissant"
    if sort_by in work.columns:
        work = work.sort_values(sort_by, ascending=ascending, kind="stable")
    if int(top_n) > 0:
        work = work.head(int(top_n))
    work = work.reset_index(drop=True)
    return work, {
        "sort_by": sort_by,
        "ascending": ascending,
        "search": search_value,
        "selected_labels": selected_labels,
        "top_n": int(top_n),
    }


def normalize_indicators_current(indicators_df: pd.DataFrame) -> pd.DataFrame:
    if indicators_df is None or indicators_df.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Dénomination", "Indicateur", "Statut", "Valeur", "Date de mise à jour", "Commentaire"])

    groups = indicator_group_map(list(indicators_df.columns))
    rows: list[dict[str, object]] = []
    for _, row in indicators_df.iterrows():
        base_info = {
            SOC_COL: row.get(SOC_COL),
            "SIREN": row.get("SIREN"),
            "Dénomination": row.get("Dénomination"),
        }
        for indicator_name, mapping in groups.items():
            if indicator_name == "Vigilance":
                continue
            statut = row.get(mapping.get("Statut", ""), None)
            valeur = row.get(mapping.get("Valeur", ""), None)
            commentaire = row.get(mapping.get("Commentaire", ""), None)
            date_maj = row.get(mapping.get("Date de mise à jour", ""), None)
            if pd.isna(statut) and pd.isna(valeur) and pd.isna(commentaire) and pd.isna(date_maj):
                continue
            rows.append({
                **base_info,
                "Indicateur": indicator_name,
                "Statut": clean_text_column(pd.Series([statut])).iloc[0],
                "Valeur": clean_text_column(pd.Series([valeur])).iloc[0],
                "Date de mise à jour": pd.to_datetime(pd.Series([date_maj]), errors="coerce").iloc[0],
                "Commentaire": clean_text_column(pd.Series([commentaire])).iloc[0],
            })
    return pd.DataFrame(rows)


def build_indicator_analysis_table(filtered_portfolio: pd.DataFrame, indicators_df: pd.DataFrame) -> pd.DataFrame:
    normalized = normalize_indicators_current(indicators_df)
    columns = ["Indicateur", "Risque avéré", "Risque potentiel", "Risque mitigé", "Non calculable", "Total cas"]
    if normalized.empty:
        return pd.DataFrame(columns=columns)
    keys = filtered_portfolio[[SOC_COL, "SIREN"]].drop_duplicates()
    normalized = normalized.merge(keys, how="inner", on=[SOC_COL, "SIREN"])
    if normalized.empty:
        return pd.DataFrame(columns=columns)
    crosstab = pd.crosstab(normalized["Indicateur"], normalized["Statut"])
    for status in ["Risque avéré", "Risque potentiel", "Risque mitigé", "Non calculable"]:
        if status not in crosstab.columns:
            crosstab[status] = 0
    crosstab["Total cas"] = crosstab[["Risque avéré", "Risque potentiel", "Risque mitigé", "Non calculable"]].sum(axis=1)
    result = crosstab.reset_index().sort_values(["Total cas", "Indicateur"], ascending=[False, True], kind="stable")
    return result[columns].head(10).reset_index(drop=True)


def render_indicator_contribution_chart(indicator_table: pd.DataFrame) -> None:
    if indicator_table is None or indicator_table.empty:
        st.info("Aucun indicateur exploitable n'est disponible sur le périmètre filtré.")
        return

    df = indicator_table.copy().head(10).reset_index(drop=True)
    numeric_cols = ["Risque avéré", "Risque potentiel", "Risque mitigé", "Non calculable", "Total cas"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    max_total = int(df["Total cas"].max()) if "Total cas" in df.columns and not df.empty else 0
    if max_total <= 0:
        max_total = 1

    rows: list[str] = []
    for rank, row in enumerate(df.to_dict("records"), start=1):
        total = int(row.get("Total cas", 0))
        width = max(6.0, round((total / max_total) * 100, 1))
        rank_bg = PRIMARY_COLOR if rank == 1 else (SECONDARY_COLOR if rank <= 3 else "#E9F1FA")
        rank_fg = "#FFFFFF" if rank <= 3 else PRIMARY_COLOR
        label = escape(str(row.get("Indicateur", "")))
        breakdown = [
            ("Avéré", int(row.get("Risque avéré", 0)), "#B42318"),
            ("Potentiel", int(row.get("Risque potentiel", 0)), "#175CD3"),
            ("Mitigé", int(row.get("Risque mitigé", 0)), "#027A48"),
            ("Non calc.", int(row.get("Non calculable", 0)), "#667085"),
        ]
        chips = []
        for chip_label, chip_value, chip_color in breakdown:
            chips.append(
                f"<span style='display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border-radius:999px;background:#F5F8FC;border:1px solid rgba(22,58,89,0.08);font-size:11px;color:#445469;'>"
                f"<span style='width:8px;height:8px;border-radius:999px;background:{chip_color};display:inline-block;'></span>"
                f"{escape(chip_label)} : <strong style='color:#163A59;font-weight:700;'>{chip_value}</strong>"
                f"</span>"
            )
        rows.append(
            f"<div style='display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid rgba(22,58,89,0.08);'>"
            f"<div style='min-width:34px;width:34px;height:34px;border-radius:999px;background:{rank_bg};color:{rank_fg};display:flex;align-items:center;justify-content:center;font-family:Sora,sans-serif;font-weight:800;font-size:14px;'>{rank}</div>"
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;gap:16px;'>"
            f"<div style='font-family:Sora,sans-serif;font-weight:700;font-size:15px;line-height:1.35;color:#163A59;'>{label}</div>"
            f"<div style='white-space:nowrap;font-family:Sora,sans-serif;font-weight:800;font-size:16px;color:#163A59;'>{total} cas</div>"
            f"</div>"
            f"<div style='margin-top:8px;height:14px;border-radius:999px;background:#E8EFF7;overflow:hidden;'>"
            f"<div style='width:{width}%;height:100%;border-radius:999px;background:linear-gradient(90deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%);'></div>"
            f"</div>"
            f"<div style='display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;'>{''.join(chips)}</div>"
            f"</div>"
            f"</div>"
        )

    html = (
        "<div style='background:#FFFFFF;border:1px solid rgba(22,58,89,0.08);border-radius:20px;padding:18px 20px 10px 20px;box-shadow:0 12px 30px rgba(15,23,42,0.06);'>"
        "<div style='display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:6px;'>"
        "<div>"
        "<div style='font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:800;color:#5E8FC7;'>Top 10</div>"
        "<div style='font-family:Sora,sans-serif;font-weight:800;font-size:20px;color:#163A59;'>Indicateurs les plus contributifs</div>"
        "</div>"
        "<div style='font-size:12px;color:#526273;text-align:right;'>Classement établi sur le <strong style='color:#163A59;'>total de cas</strong>.</div>"
        "</div>"
        + ''.join(rows)
        + "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_analysis_trend_chart(trend_df: pd.DataFrame) -> None:
    if trend_df is None or trend_df.empty:
        st.info("Aucune date exploitable n'est disponible sur le périmètre filtré.")
        return

    chart_df = trend_df.copy()
    metric_cols = ["Mises à jour vigilance", "Dernières revues", "Prochaines revues"]
    for col in metric_cols:
        if col in chart_df.columns:
            chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0).round(0).astype(int)

    month_order = chart_df["Mois"].astype(str).tolist()
    melted = chart_df.melt(
        id_vars=["Mois"],
        value_vars=metric_cols,
        var_name="Jalon",
        value_name="Cas",
    )
    melted["Mois"] = melted["Mois"].astype(str)
    melted["Cas"] = pd.to_numeric(melted["Cas"], errors="coerce").fillna(0).astype(int)

    color_scale = alt.Scale(
        domain=metric_cols,
        range=["#0F4C81", "#F28C28", "#2E8B57"],
    )

    base = alt.Chart(melted).encode(
        x=alt.X(
            "Mois:N",
            sort=month_order,
            title=None,
            axis=alt.Axis(labelAngle=0, labelPadding=10, labelFontSize=12, labelColor="#163A59"),
        ),
        xOffset=alt.XOffset("Jalon:N", sort=metric_cols),
        y=alt.Y(
            "Cas:Q",
            title=None,
            axis=alt.Axis(grid=True, tickMinStep=1, labelFontSize=12, labelColor="#526273"),
            scale=alt.Scale(nice=True, zero=True),
        ),
        color=alt.Color(
            "Jalon:N",
            sort=metric_cols,
            scale=color_scale,
            legend=alt.Legend(title=None, orient="top", direction="horizontal", labelFontSize=12, symbolType="square"),
        ),
        tooltip=[
            alt.Tooltip("Mois:N", title="Mois"),
            alt.Tooltip("Jalon:N", title="Jalon"),
            alt.Tooltip("Cas:Q", title="Cas", format=".0f"),
        ],
    )

    bars = base.mark_bar(size=22, cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
    labels = base.mark_text(
        dy=-10,
        font="Sora",
        fontSize=11,
        fontWeight="bold",
        color="#163A59",
    ).encode(text=alt.Text("Cas:Q", format=".0f"))

    chart = (
        (bars + labels)
        .properties(height=320)
        .configure_view(strokeOpacity=0)
        .configure_axis(domain=False, gridColor="#E6EEF6", tickColor="#E6EEF6", titleColor="#163A59")
        .configure_legend(labelColor="#163A59")
    )

    st.altair_chart(chart, use_container_width=True)
    st.caption("Lecture mensuelle : bleu = mises à jour vigilance, orange = dernières revues, vert = prochaines revues.")


def normalize_analysis_category(series: pd.Series) -> pd.Series:
    return series.fillna("Non renseigné").astype(str).replace({"": "Non renseigné"})


def clear_analysis_focus() -> None:
    for key in [
        "analysis_focus_row_label",
        "analysis_focus_row_value",
        "analysis_focus_col_label",
        "analysis_focus_col_value",
        "analysis_focus_source",
        "analysis_focus_selection",
    ]:
        st.session_state.pop(key, None)


def set_analysis_focus(
    *,
    row_label: str | None = None,
    row_value: str | None = None,
    col_label: str | None = None,
    col_value: str | None = None,
    source: str | None = None,
) -> None:
    if row_label is not None:
        st.session_state["analysis_focus_row_label"] = row_label
        st.session_state["analysis_focus_row_value"] = row_value
    if col_label is not None:
        st.session_state["analysis_focus_col_label"] = col_label
        st.session_state["analysis_focus_col_value"] = col_value
    if source is not None:
        st.session_state["analysis_focus_source"] = source


def validate_analysis_focus(
    df: pd.DataFrame,
    row_col: str,
    row_label: str,
    col_col: str | None,
    col_label: str | None,
) -> None:
    row_value = st.session_state.get("analysis_focus_row_value")
    row_label_state = st.session_state.get("analysis_focus_row_label")
    if row_label_state != row_label:
        st.session_state.pop("analysis_focus_row_label", None)
        st.session_state.pop("analysis_focus_row_value", None)
    elif row_value is not None:
        valid_row_values = set(normalize_analysis_category(df.get(row_col, pd.Series(dtype='object'))).unique().tolist())
        if str(row_value) not in valid_row_values:
            st.session_state.pop("analysis_focus_row_label", None)
            st.session_state.pop("analysis_focus_row_value", None)

    if not col_col or not col_label:
        st.session_state.pop("analysis_focus_col_label", None)
        st.session_state.pop("analysis_focus_col_value", None)
    else:
        col_value = st.session_state.get("analysis_focus_col_value")
        col_label_state = st.session_state.get("analysis_focus_col_label")
        if col_label_state != col_label:
            st.session_state.pop("analysis_focus_col_label", None)
            st.session_state.pop("analysis_focus_col_value", None)
        elif col_value is not None:
            valid_col_values = set(normalize_analysis_category(df.get(col_col, pd.Series(dtype='object'))).unique().tolist())
            if str(col_value) not in valid_col_values:
                st.session_state.pop("analysis_focus_col_label", None)
                st.session_state.pop("analysis_focus_col_value", None)


def build_analysis_focus_dataset(
    df: pd.DataFrame,
    row_col: str | None = None,
    row_value: str | None = None,
    row_label: str | None = None,
    column_col: str | None = None,
    column_value: str | None = None,
    column_label: str | None = None,
) -> pd.DataFrame:
    detail = df.copy()
    focus_parts: list[str] = []

    if row_col and row_value not in {None, "", "Tous"}:
        detail = detail[normalize_analysis_category(detail.get(row_col, pd.Series(index=detail.index, dtype='object'))) == str(row_value)]
        focus_parts.append(f"{row_label or row_col} = {row_value}")

    if column_col and column_value not in {None, "", "Tous"}:
        detail = detail[normalize_analysis_category(detail.get(column_col, pd.Series(index=detail.index, dtype='object'))) == str(column_value)]
        focus_parts.append(f"{column_label or column_col} = {column_value}")

    detail = detail.copy()
    detail["Motif de présence"] = " | ".join(focus_parts) if focus_parts else "Périmètre filtré"
    detail_columns = [
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        SOC_COL,
        "Pays de résidence",
        "Segment",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Statut EDD",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Motif de présence",
    ]
    detail_columns = [c for c in detail_columns if c in detail.columns]
    return detail[detail_columns]


def render_analysis_kpis(df: pd.DataFrame, full_scope_df: pd.DataFrame | None = None) -> None:
    total_clients = int(len(df))
    scope_total = int(len(full_scope_df)) if full_scope_df is not None else total_clients
    part_portefeuille = (total_clients / scope_total) if scope_total else 0.0

    justificatifs_incomplets = int(
        df.get("Flag justificatif complet", pd.Series(index=df.index, dtype="string"))
        .astype("string")
        .fillna("")
        .ne("Oui")
        .sum()
    )
    sans_prochaine_revue = int(
        df.get("Date prochaine revue", pd.Series(index=df.index, dtype="datetime64[ns]"))
        .isna()
        .sum()
    )
    revue_trop_ancienne = int(
        df.get("Alerte revue trop ancienne", pd.Series(index=df.index, dtype="int64"))
        .fillna(0)
        .astype(int)
        .sum()
    )
    cross_border_eleve = int(
        df.get("Alerte cross-border élevé", pd.Series(index=df.index, dtype="int64"))
        .fillna(0)
        .astype(int)
        .sum()
    )
    cash_intensite_elevee = int(
        df.get("Alerte cash intensité élevée", pd.Series(index=df.index, dtype="int64"))
        .fillna(0)
        .astype(int)
        .sum()
    )
    vigilance_renforcee = int(
        df.get("Vigilance", pd.Series(index=df.index, dtype="string"))
        .astype("string")
        .isin(CRITICAL_VIGILANCE)
        .sum()
    )
    risque_avere = int(
        df.get("Risque", pd.Series(index=df.index, dtype="string"))
        .astype("string")
        .eq("Risque avéré")
        .sum()
    )

    cards = [
        ("Clients", f"{total_clients:,}".replace(",", " "), "Périmètre analysé", ""),
        ("Part du portefeuille", f"{part_portefeuille:.1%}".replace(".", ","), "Poids du périmètre", ""),
        ("Vigilance renforcée", f"{vigilance_renforcee:,}".replace(",", " "), "Élevée + critique", " is-alert"),
        ("Risque avéré", f"{risque_avere:,}".replace(",", " "), "Clients en risque avéré", " is-alert"),
        ("Justificatifs incomplets", f"{justificatifs_incomplets:,}".replace(",", " "), "Documents à compléter", ""),
        ("Sans prochaine revue", f"{sans_prochaine_revue:,}".replace(",", " "), "Revue non planifiée", ""),
        ("Revue trop ancienne", f"{revue_trop_ancienne:,}".replace(",", " "), "Suivi à mettre à jour", ""),
        ("Cross-border élevé", f"{cross_border_eleve:,}".replace(",", " "), "Exposition élevée", ""),
        ("Cash intensité élevée", f"{cash_intensite_elevee:,}".replace(",", " "), "Usage cash élevé", ""),
    ]

    st.markdown('<h3 class="cm-section-title">Bandeau de synthèse</h3>', unsafe_allow_html=True)
    st.markdown(
        "<div class='cm-kpi-band'>"
        + "".join(
            f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
            for label, value, sub, extra_class in cards
        )
        + "</div>",
        unsafe_allow_html=True,
    )

    if total_clients and "Vigilance Date de mise à jour" in df.columns:
        last_update = pd.to_datetime(df["Vigilance Date de mise à jour"], errors="coerce").max()
        if pd.notna(last_update):
            st.markdown(
                f"<div class='cm-kpi-note'>Dernière mise à jour vigilance visible : <strong>{last_update.strftime('%d/%m/%Y')}</strong>. Les indicateurs sont regroupés dans ce bandeau ; le tableau d’analyse présente uniquement les dimensions de lecture.</div>",
                unsafe_allow_html=True,
            )


def format_table_for_display(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for col in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[col]):
            output[col] = output[col].dt.strftime("%d/%m/%Y")
            continue
        if col.startswith("%"):
            output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{float(x):.1%}")
            continue
        if pd.api.types.is_float_dtype(output[col]):
            non_null = output[col].dropna()
            if non_null.empty:
                continue
            if np.allclose(non_null % 1, 0):
                output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{int(round(float(x))):,}".replace(",", " "))
            else:
                output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{float(x):,.1f}".replace(",", " ").replace(".", ","))
        elif pd.api.types.is_integer_dtype(output[col]):
            output[col] = output[col].map(lambda x: "" if pd.isna(x) else f"{int(x):,}".replace(",", " "))
    return output


def render_analysis_main_table(df: pd.DataFrame, selected_row_idx: int | None = None) -> None:
    if df is None or df.empty:
        st.info("Aucune donnée à afficher.")
        return

    display_df = format_table_for_display(df)
    html = ["<div class='cm-analysis-main-wrap'><table class='cm-analysis-main-table'><thead><tr>"]
    for col in display_df.columns:
        header_classes = []
        if str(col) == "Alertes de gouvernance (calculé)":
            header_classes.append("cm-calculated-col")
        header_class_attr = f" class='{' '.join(header_classes)}'" if header_classes else ""
        html.append(f"<th{header_class_attr}>{escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for row_idx, row in display_df.iterrows():
        row_class = " class='cm-row-selected'" if selected_row_idx is not None and row_idx == int(selected_row_idx) else ""
        html.append(f"<tr{row_class}>")
        for idx, col in enumerate(display_df.columns):
            value = row[col]
            classes = []
            original_value = df.iloc[row_idx][col] if col in df.columns else value
            if idx == 0:
                classes.append("cm-first-col")
            if str(col) == "Alertes de gouvernance (calculé)":
                classes.append("cm-calculated-col")
            if isinstance(original_value, (int, float, np.integer, np.floating)) and not isinstance(original_value, bool):
                classes.append("cm-number")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            rendered = "" if pd.isna(value) else escape(str(value))
            html.append(f"<td{class_attr}>{rendered}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)



ANALYSIS_FILTER_COLUMNS: list[tuple[str, str]] = [
    ("Vigilance", "Vigilance"),
    ("Risque", "Risque"),
    ("EDD", "Statut EDD"),
    ("Segment", "Segment"),
    ("Pays", "Pays de résidence"),
    ("Produit", "Produit(service) principal"),
    ("Canal", "Canal d’opérations principal 12 mois"),
    ("Analyste", "Analyste"),
    ("Valideur", "Valideur"),
]


def build_unified_analysis_table(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    group_labels = [label for label, _ in ANALYSIS_FILTER_COLUMNS]
    if df is None or df.empty:
        return pd.DataFrame(columns=group_labels), ""

    work = df.copy()
    for label, source in ANALYSIS_FILTER_COLUMNS:
        work[label] = normalize_analysis_category(work.get(source, pd.Series(index=work.index, dtype="object")))

    work["cm_client_key"] = work[SOC_COL].astype(str) + "|" + work["SIREN"].astype(str)
    grouped = (
        work.groupby(group_labels, dropna=False)
        .agg(__sort_clients=("cm_client_key", "nunique"))
        .reset_index()
        .sort_values("__sort_clients", ascending=False, kind="stable")
        .drop(columns=["__sort_clients"])
        .reset_index(drop=True)
    )
    caption = "Le tableau d’analyse présente uniquement les dimensions de lecture ; les indicateurs sont portés par le bandeau de synthèse."
    return grouped, caption


def apply_unified_analysis_table_controls(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    work = df.copy().reset_index(drop=True)
    text_cols = [label for label, _ in ANALYSIS_FILTER_COLUMNS if label in work.columns]

    control_cols = st.columns([1.8, 1.35, 1.1, 0.85])
    with control_cols[0]:
        search_value = st.text_input(
            "Recherche",
            value=st.session_state.get("analysis_table_search", ""),
            key="analysis_table_search",
            placeholder="Rechercher une valeur dans le tableau…",
        )
    sort_options = [c for c in work.columns if c not in text_cols] or list(work.columns)
    default_sort = "Clients" if "Clients" in sort_options else (sort_options[0] if sort_options else work.columns[0])
    if st.session_state.get("analysis_table_sort_by") not in sort_options:
        st.session_state["analysis_table_sort_by"] = default_sort
    with control_cols[1]:
        sort_by = st.selectbox(
            "Trier par",
            options=sort_options,
            index=sort_options.index(st.session_state.get("analysis_table_sort_by", default_sort)),
            key="analysis_table_sort_by",
        )
    order_options = ["Décroissant", "Croissant"]
    if st.session_state.get("analysis_table_sort_order") not in order_options:
        st.session_state["analysis_table_sort_order"] = "Décroissant"
    with control_cols[2]:
        sort_order = st.selectbox(
            "Ordre",
            options=order_options,
            index=order_options.index(st.session_state.get("analysis_table_sort_order", "Décroissant")),
            key="analysis_table_sort_order",
        )
    with control_cols[3]:
        top_n = st.number_input(
            "Top N",
            min_value=0,
            max_value=max(len(work), 1),
            value=min(int(st.session_state.get("analysis_table_top_n", min(len(work), 20))), max(len(work), 1)),
            step=1,
            key="analysis_table_top_n",
            help="0 = toutes les lignes",
        )

    if search_value:
        mask = pd.Series(False, index=work.index)
        for col in text_cols:
            mask = mask | work[col].astype(str).str.contains(str(search_value), case=False, na=False)
        work = work[mask]

    ascending = sort_order == "Croissant"
    work = work.sort_values(sort_by, ascending=ascending, kind="stable")
    if int(top_n) > 0:
        work = work.head(int(top_n))
    return work.reset_index(drop=True)


def build_analysis_focus_dataset_from_selection(
    df: pd.DataFrame,
    selection: list[dict[str, object]] | dict[str, object] | None,
) -> tuple[pd.DataFrame, list[str]]:
    if not selection:
        return pd.DataFrame(), []

    selections = selection if isinstance(selection, list) else [selection]
    base = df.copy()
    detail_frames: list[pd.DataFrame] = []
    focus_parts: list[str] = []

    for item in selections:
        row_mask = pd.Series(True, index=base.index)
        local_parts: list[str] = []
        for label, source in ANALYSIS_FILTER_COLUMNS:
            if label not in item:
                continue
            raw_value = item.get(label)
            value = "Non renseigné" if pd.isna(raw_value) or str(raw_value).strip() == "" else str(raw_value)
            row_mask = row_mask & (
                normalize_analysis_category(base.get(source, pd.Series(index=base.index, dtype="object"))) == value
            )
            local_parts.append(f"{label} = {value}")

        if not row_mask.any():
            continue

        motif = " | ".join(local_parts) if local_parts else "Périmètre filtré"
        row_detail = base.loc[row_mask].copy()
        row_detail["Motif de présence"] = motif
        detail_frames.append(row_detail)
        focus_parts.append(motif)

    if not detail_frames:
        return pd.DataFrame(), []

    detail = pd.concat(detail_frames, ignore_index=True)
    detail["cm_client_key"] = detail[SOC_COL].astype(str) + "|" + detail["SIREN"].astype(str)

    detail_columns = [
        "SIREN",
        "Dénomination",
        "Vigilance",
        "Risque",
        SOC_COL,
        "Pays de résidence",
        "Segment",
        "Produit(service) principal",
        "Canal d’opérations principal 12 mois",
        "Statut EDD",
        "Analyste",
        "Valideur",
        "Date dernière revue",
        "Motif de présence",
    ]
    detail_columns = [c for c in detail_columns if c in detail.columns]

    aggregate = {col: "first" for col in detail_columns if col != "Motif de présence"}
    aggregate["Motif de présence"] = lambda s: " || ".join(pd.unique([str(v) for v in s if pd.notna(v) and str(v).strip()]))
    detail = (
        detail[["cm_client_key"] + detail_columns]
        .groupby("cm_client_key", as_index=False)
        .agg(aggregate)
        .drop(columns=["cm_client_key"], errors="ignore")
    )
    return detail[detail_columns], focus_parts




def build_existing_review_dates_dataset(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Date prochaine revue"])

    work = df.copy()
    work["Date prochaine revue"] = pd.to_datetime(
        work.get("Date prochaine revue", pd.Series(index=work.index, dtype="datetime64[ns]")),
        errors="coerce",
        dayfirst=True,
    )
    work = work.dropna(subset=["Date prochaine revue"]).copy()
    if work.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Date prochaine revue"])

    regimes = work.apply(lambda row: review_vigilance_regime(row)[0], axis=1)
    work["Régime de vigilance"] = regimes
    cols = [c for c in [SOC_COL, "SIREN", "Dénomination", "Régime de vigilance", "Date prochaine revue"] if c in work.columns]
    work = work[cols].drop_duplicates(subset=[c for c in [SOC_COL, "SIREN"] if c in cols], keep="last")
    return work


def render_analysis_review_dates_from_base(df: pd.DataFrame) -> None:
    st.markdown('<h3 class="cm-section-title">Planification des revues</h3>', unsafe_allow_html=True)
    st.caption("Cette vue reprend uniquement les dates de prochaine revue déjà présentes dans le fichier 01, sur le périmètre filtré en haut de l’écran Analyse.")

    schedule_df = build_existing_review_dates_dataset(df)
    if schedule_df.empty:
        st.info("Aucune date de prochaine revue n’est disponible dans le fichier 01 sur le périmètre filtré.")
        return

    chart_df = build_review_schedule_chart_table(schedule_df)
    render_review_schedule_chart(chart_df)

    available = int(schedule_df["Date prochaine revue"].notna().sum())
    missing = int(len(df) - available)
    cards = [
        ("SIREN datés", f"{available:,}".replace(",", " "), "Dates issues du fichier 01", ""),
        ("Sans date", f"{missing:,}".replace(",", " "), "Aucune prochaine revue dans le fichier 01", " is-alert" if missing > 0 else ""),
    ]
    st.markdown(
        "<div class='cm-kpi-band'>"
        + "".join(
            f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
            for label, value, sub, extra_class in cards
        )
        + "</div>",
        unsafe_allow_html=True,
    )



def render_analysis_screen(portfolio: pd.DataFrame, indicators: pd.DataFrame) -> None:
    render_home_hero("Analyse")
    nav = render_primary_navigation("analysis")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()

    top_left, top_right = st.columns([5.4, 1.2])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Pilotage de l’analyse</h3>', unsafe_allow_html=True)
        st.caption("Un seul tableau d’analyse : les filtres cadrent le portefeuille, le clic sur une ligne alimente les clients sous-jacents.")
    with top_right:
        if st.button("Réinitialiser", type="secondary", key="analysis_reset_all"):
            reset_filters()
            for key in [
                "analysis_selected_idx_analysis_main",
                "analysis_table_search",
                "analysis_table_sort_by",
                "analysis_table_sort_order",
                "analysis_table_top_n",
            ]:
                st.session_state.pop(key, None)
            clear_analysis_focus()
            st.rerun()

    filter_labels = ["Vigilance", "Risque", "EDD", "Segment", "Pays", "Produit", "Canal", "Analyste", "Valideur"]
    selections: dict[str, str] = {}
    filter_cols = st.columns(5)
    for idx, label in enumerate(filter_labels):
        column = FILTER_MAPPING[label]
        options = ["Tous"] + non_empty_sorted(portfolio[column].unique()) if column in portfolio.columns else ["Tous"]
        state_key = "filter_" + label
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with filter_cols[idx % 5]:
            selections[label] = st.selectbox(label, options=options, key=state_key)
        if idx % 5 == 4 and idx < len(filter_labels) - 1:
            filter_cols = st.columns(5)

    st.markdown(
        """
        <div class="cm-analysis-mode-shell">
            <div class="cm-analysis-mode-kicker">Lecture de l’analyse</div>
            <div class="cm-analysis-mode-title">Le tableau présente uniquement les dimensions de lecture</div>
            <div class="cm-analysis-mode-note">Les indicateurs Clients, Part du portefeuille, Justificatifs incomplets, Sans prochaine revue, Revue trop ancienne, Cross-border élevé et Cash intensité élevée sont affichés dans le bandeau de synthèse.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    filtered = apply_filters(portfolio, selections)
    if filtered.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    render_analysis_kpis(filtered, portfolio)

    analysis_table, analysis_caption = build_unified_analysis_table(filtered)
    render_analysis_panel_header("Tableau d’analyse", analysis_caption)
    display_analysis_table = apply_unified_analysis_table_controls(analysis_table)
    main_action, selected_main = render_selectable_analysis_table(display_analysis_table, key_prefix="analysis_main", height=520)

    if main_action == "selected" and selected_main:
        st.session_state["analysis_focus_selection"] = selected_main
    elif main_action == "cleared":
        if "analysis_focus_selection" in st.session_state:
            st.session_state.pop("analysis_focus_selection", None)
            st.rerun()

    if analysis_table.empty:
        st.info("Aucun résultat à afficher pour les paramètres sélectionnés.")
        return
    if display_analysis_table.empty:
        st.info("Aucune ligne ne correspond aux contrôles intégrés du tableau d’analyse.")

    st.divider()
    indicator_table = build_indicator_analysis_table(filtered, indicators)
    render_indicator_contribution_chart(indicator_table)

    st.divider()
    render_analysis_review_dates_from_base(filtered)

    st.divider()
    st.markdown("<div id='clients-sous-jacents'></div>", unsafe_allow_html=True)
    st.markdown('<h3 class="cm-section-title">Clients sous-jacents</h3>', unsafe_allow_html=True)

    focus_selection = st.session_state.get("analysis_focus_selection")
    detail_df, focus_parts = build_analysis_focus_dataset_from_selection(filtered, focus_selection)

    focus_bar_left, focus_bar_right = st.columns([6.0, 1.2])
    with focus_bar_left:
        if focus_parts:
            if len(focus_parts) == 1:
                st.caption("Focus actif : " + focus_parts[0])
            else:
                preview = " ; ".join(focus_parts[:2])
                if len(focus_parts) > 2:
                    preview += f" ; +{len(focus_parts) - 2} autre(s) ligne(s)"
                st.caption(f"Focus actif : {len(focus_parts)} lignes sélectionnées — " + preview)
        else:
            st.caption("Cliquez sur une ou plusieurs lignes du tableau d’analyse pour afficher automatiquement les clients sous-jacents correspondants.")
    with focus_bar_right:
        if focus_parts and st.button("Effacer le focus", type="secondary", key="analysis_clear_focus"):
            clear_analysis_focus()
            st.rerun()

    if detail_df.empty:
        st.info("Aucun client sous-jacent à afficher tant qu’aucun focus n’est sélectionné.")
    else:
        st.caption("Cliquez sur un SIREN pour ouvrir la fiche client sans quitter votre contexte d’analyse.")
        render_clickable_styled_dataframe(
            style_dataframe(detail_df),
            detail_df,
            height=440,
            hide_index=True,
            key_prefix="analysis_detail_clients",
        )


def review_setting_slug(label: str) -> str:
    slug = label.lower()
    slug = slug.replace("é", "e").replace("è", "e").replace("ê", "e")
    slug = slug.replace("à", "a").replace("ù", "u")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def ensure_review_planning_state_defaults() -> None:
    saved_freq_map, saved_cap_map = load_saved_review_planning_settings()
    for label in VIGILANCE_ORDER:
        freq_key = f"review_freq_{review_setting_slug(label)}"
        cap_key = f"review_cap_{review_setting_slug(label)}"
        st.session_state.setdefault(freq_key, int(saved_freq_map.get(label, REVIEW_FREQUENCY_DEFAULTS.get(label, 12))))
        st.session_state.setdefault(cap_key, int(saved_cap_map.get(label, REVIEW_CAPACITY_DEFAULTS.get(label, 10))))


def get_review_planning_settings() -> tuple[dict[str, int], dict[str, int]]:
    ensure_review_planning_state_defaults()
    freq_map: dict[str, int] = {}
    cap_map: dict[str, int] = {}
    for label in VIGILANCE_ORDER:
        freq_key = f"review_freq_{review_setting_slug(label)}"
        cap_key = f"review_cap_{review_setting_slug(label)}"
        freq_map[label] = int(st.session_state.get(freq_key, REVIEW_FREQUENCY_DEFAULTS.get(label, 12)))
        cap_map[label] = int(st.session_state.get(cap_key, REVIEW_CAPACITY_DEFAULTS.get(label, 10)))
    return freq_map, cap_map


def review_table_static_cell(value: object, *, header: bool = False, align: str = "center") -> str:
    bg = PRIMARY_COLOR if header else "#F8FBFF"
    fg = "#FFFFFF" if header else "#163A59"
    weight = 700 if header else 600
    border = "none" if header else "1px solid rgba(22, 58, 89, 0.10)"
    radius = "10px" if header else "10px"
    pad = "0.72rem 0.55rem" if header else "0.78rem 0.55rem"
    size = "0.82rem" if header else "0.9rem"
    return (
        f"<div style='background:{bg}; color:{fg}; border:{border}; border-radius:{radius}; "
        f"padding:{pad}; text-align:{align}; font-weight:{weight}; font-size:{size}; line-height:1.1;'>"
        f"{escape(str(value))}</div>"
    )



def render_review_rule_editor(df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int], bool]:
    ensure_review_planning_state_defaults()
    dist = build_distribution(df, "Vigilance", VIGILANCE_ORDER).rename(columns={"Libellé": "Régime de vigilance"})
    count_map = {row["Régime de vigilance"]: int(row["Nb"]) for _, row in dist.iterrows()}
    share_map = {row["Régime de vigilance"]: float(row["%"] if pd.notna(row["%"] ) else 0.0) for _, row in dist.iterrows()}

    st.markdown('<h3 class="cm-section-title">Règles de planification des revues</h3>', unsafe_allow_html=True)
    st.caption("Fréquence par régime de vigilance + capacité maximale de revues par mois. Si la capacité d’un mois est dépassée, l’excédent est décalé automatiquement sur les mois suivants.")

    with st.form("review_planning_rules_form"):
        header_cols = st.columns([2.9, 0.8, 0.9, 1.35, 1.55])
        headers = ["Régime de vigilance", "Nb", "%", "Fréquence (mois)", "Capacité max / mois"]
        for col, title in zip(header_cols, headers):
            with col:
                st.markdown(review_table_static_cell(title, header=True), unsafe_allow_html=True)

        for regime in VIGILANCE_ORDER:
            freq_key = f"review_freq_{review_setting_slug(regime)}"
            cap_key = f"review_cap_{review_setting_slug(regime)}"
            row_cols = st.columns([2.9, 0.8, 0.9, 1.35, 1.55])
            with row_cols[0]:
                st.markdown(review_table_static_cell(regime, align="left"), unsafe_allow_html=True)
            with row_cols[1]:
                st.markdown(review_table_static_cell(count_map.get(regime, 0)), unsafe_allow_html=True)
            with row_cols[2]:
                st.markdown(review_table_static_cell(f"{share_map.get(regime, 0.0) * 100:.1f}%"), unsafe_allow_html=True)
            with row_cols[3]:
                st.number_input(
                    f"Fréquence {regime}",
                    min_value=1,
                    max_value=60,
                    step=1,
                    key=freq_key,
                    label_visibility="collapsed",
                )
            with row_cols[4]:
                st.number_input(
                    f"Capacité {regime}",
                    min_value=1,
                    max_value=500,
                    step=1,
                    key=cap_key,
                    label_visibility="collapsed",
                )

        recalc = st.form_submit_button("Recalculer le planning", type="primary", use_container_width=True)

    freq_map, cap_map = get_review_planning_settings()
    return freq_map, cap_map, recalc



def review_vigilance_regime(row: pd.Series) -> tuple[str, str]:
    raw_value = str(row.get("Vigilance", "") or "").strip()
    value = raw_value.lower()
    if "critique" in value:
        return "Vigilance Critique", "Régime de vigilance = Critique"
    if "élev" in value or "elev" in value:
        return "Vigilance Élevée", "Régime de vigilance = Élevée"
    if "modér" in value or "moder" in value:
        return "Vigilance Modérée", "Régime de vigilance = Modérée"
    if "allég" in value or "alleg" in value:
        return "Vigilance Allégée", "Régime de vigilance = Allégée"
    if "aucune" in value:
        return "Vigilance Aucune", "Régime de vigilance = Aucune"
    if raw_value in VIGILANCE_ORDER:
        return raw_value, f"Régime de vigilance = {raw_value.replace('Vigilance ', '')}"
    return "Vigilance Aucune", "Régime de vigilance par défaut = Aucune"



def compute_review_base_date(row: pd.Series, today: pd.Timestamp) -> tuple[pd.Timestamp, str]:
    last_review = pd.to_datetime(row.get("Date dernière revue"), errors="coerce")
    if pd.notna(last_review):
        return pd.Timestamp(last_review).normalize(), "Date dernière revue"

    vig_update = pd.to_datetime(row.get("Vigilance Date de mise à jour"), errors="coerce")
    if pd.notna(vig_update):
        return pd.Timestamp(vig_update).normalize(), "Dernière mise à jour vigilance"

    return today.normalize(), "Date du jour"



def shift_date_to_target_month(date_value: pd.Timestamp, target_month: pd.Timestamp) -> pd.Timestamp:
    date_value = pd.Timestamp(date_value).normalize()
    target_month = pd.Timestamp(target_month).normalize().replace(day=1)
    month_end = (target_month + pd.offsets.MonthEnd(0)).normalize()
    day = min(int(date_value.day), int(month_end.day))
    return pd.Timestamp(year=int(target_month.year), month=int(target_month.month), day=day)



def month_offset(start_month: pd.Timestamp, end_month: pd.Timestamp) -> int:
    start_month = pd.Timestamp(start_month)
    end_month = pd.Timestamp(end_month)
    return int((end_month.year - start_month.year) * 12 + (end_month.month - start_month.month))



def smooth_review_schedule(schedule_df: pd.DataFrame, capacity_map: dict[str, int], today: pd.Timestamp) -> pd.DataFrame:
    if schedule_df is None or schedule_df.empty:
        return schedule_df

    schedule = schedule_df.copy()
    schedule["Date prochaine revue"] = pd.NaT
    schedule["Mois théorique"] = ""
    schedule["Mois planifié"] = ""
    schedule["Lissé"] = "Non"
    schedule["Décalage (mois)"] = 0
    schedule["Capacité max / mois"] = 0

    current_month = today.to_period("M").to_timestamp()
    for regime in VIGILANCE_ORDER:
        mask = schedule["Régime de vigilance"].eq(regime)
        if not mask.any():
            continue
        capacity = max(int(capacity_map.get(regime, REVIEW_CAPACITY_DEFAULTS.get(regime, 10))), 1)
        bucket_usage: dict[pd.Timestamp, int] = {}
        group = schedule.loc[mask].sort_values(["Date prochaine revue théorique", "Date de base", "SIREN"], kind="stable")
        for idx, row in group.iterrows():
            theoretical = pd.to_datetime(row.get("Date prochaine revue théorique"), errors="coerce")
            if pd.isna(theoretical):
                theoretical = today.normalize()
            base_month = theoretical.to_period("M").to_timestamp()
            candidate_month = base_month if base_month >= current_month else current_month
            source_month = candidate_month
            while bucket_usage.get(candidate_month, 0) >= capacity:
                candidate_month = (candidate_month + pd.DateOffset(months=1)).to_period("M").to_timestamp()
            planned_date = shift_date_to_target_month(theoretical, candidate_month)
            bucket_usage[candidate_month] = bucket_usage.get(candidate_month, 0) + 1

            schedule.at[idx, "Date prochaine revue"] = planned_date
            schedule.at[idx, "Mois théorique"] = theoretical.to_period("M").strftime("%Y-%m")
            schedule.at[idx, "Mois planifié"] = pd.Timestamp(candidate_month).strftime("%Y-%m")
            schedule.at[idx, "Lissé"] = "Oui" if candidate_month != source_month else "Non"
            schedule.at[idx, "Décalage (mois)"] = month_offset(source_month, candidate_month)
            schedule.at[idx, "Capacité max / mois"] = capacity

    planned_dates = pd.to_datetime(schedule["Date prochaine revue"], errors="coerce")
    delta_days = (planned_dates - today).dt.days
    schedule["Statut planning"] = np.select(
        [delta_days < 0, delta_days <= 30, delta_days <= 90],
        ["En retard", "À 30 jours", "31-90 jours"],
        default="Au-delà de 90 jours",
    )
    schedule = schedule.sort_values(["Date prochaine revue", "Régime de vigilance", SOC_COL, "SIREN"], kind="stable").reset_index(drop=True)
    return schedule



def build_review_schedule(df: pd.DataFrame, freq_map: dict[str, int], capacity_map: dict[str, int], today: pd.Timestamp | None = None) -> pd.DataFrame:
    if today is None:
        today = pd.Timestamp.today().normalize()
    if df is None or df.empty:
        return pd.DataFrame(columns=[SOC_COL, "SIREN", "Régime de vigilance", "Date prochaine revue"]) 

    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        regime, reason = review_vigilance_regime(row)
        base_date, base_source = compute_review_base_date(row, today)
        months = int(freq_map.get(regime, REVIEW_FREQUENCY_DEFAULTS.get(regime, 12)))
        theoretical = (base_date + pd.DateOffset(months=months)).normalize()
        rows.append(
            {
                SOC_COL: row.get(SOC_COL),
                "SIREN": row.get("SIREN"),
                "Dénomination": row.get("Dénomination"),
                "Régime de vigilance": regime,
                "Règle appliquée": reason,
                "Fréquence (mois)": months,
                "Date de base": base_date,
                "Source date de base": base_source,
                "Date prochaine revue théorique": theoretical,
                "Vigilance": row.get("Vigilance"),
                "Risque": row.get("Risque"),
            }
        )

    schedule = pd.DataFrame(rows)
    if schedule.empty:
        return schedule
    return smooth_review_schedule(schedule, capacity_map, today)



def build_review_schedule_chart_table(schedule_df: pd.DataFrame, today: pd.Timestamp | None = None) -> pd.DataFrame:
    if today is None:
        today = pd.Timestamp.today().normalize()
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame(columns=["Mois"] + VIGILANCE_ORDER)

    work = schedule_df.copy()
    due = pd.to_datetime(work["Date prochaine revue"], errors="coerce")
    current_month = today.to_period("M").to_timestamp()
    month_bucket = due.dt.to_period("M").dt.to_timestamp()
    month_bucket = month_bucket.where(month_bucket >= current_month, current_month)
    work["Mois"] = month_bucket

    max_month = month_bucket.max()
    if pd.isna(max_month):
        max_month = current_month
    horizon_end = max(current_month + pd.DateOffset(months=11), pd.Timestamp(max_month))
    month_index = pd.date_range(current_month, horizon_end, freq="MS")

    grouped = (
        work.groupby(["Mois", "Régime de vigilance"]).size().unstack(fill_value=0).reindex(month_index, fill_value=0)
    )
    for col in VIGILANCE_ORDER:
        if col not in grouped.columns:
            grouped[col] = 0
    grouped = grouped[VIGILANCE_ORDER].reset_index().rename(columns={"index": "Mois"})
    grouped["Mois"] = pd.to_datetime(grouped["Mois"]).dt.strftime("%Y-%m")
    return grouped



def render_review_schedule_chart(chart_df: pd.DataFrame) -> None:
    if chart_df is None or chart_df.empty:
        st.info("Aucune revue planifiée n'est disponible sur le périmètre filtré.")
        return

    metric_cols = VIGILANCE_ORDER
    chart_df = chart_df.copy()
    for col in metric_cols:
        chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce").fillna(0).round(0).astype(int)
    chart_df["Total"] = chart_df[metric_cols].sum(axis=1)

    month_order = chart_df["Mois"].astype(str).tolist()
    melted = chart_df.melt(id_vars=["Mois"], value_vars=metric_cols, var_name="Régime de vigilance", value_name="Cas")
    color_scale = alt.Scale(
        domain=metric_cols,
        range=["#BF2424", "#F28C28", "#EAAA08", "#5E8FC7", "#163A59"],
    )

    bars = alt.Chart(melted).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Mois:N", sort=month_order, title=None, axis=alt.Axis(labelAngle=0, labelPadding=10, labelFontSize=12, labelColor="#163A59")),
        y=alt.Y("Cas:Q", title=None, axis=alt.Axis(grid=True, tickMinStep=1, labelFontSize=12, labelColor="#526273"), stack=True),
        color=alt.Color("Régime de vigilance:N", sort=metric_cols, scale=color_scale, legend=alt.Legend(title=None, orient="top", direction="horizontal", labelFontSize=12, symbolType="square")),
        tooltip=[
            alt.Tooltip("Mois:N", title="Mois"),
            alt.Tooltip("Régime de vigilance:N", title="Régime"),
            alt.Tooltip("Cas:Q", title="Cas", format=".0f"),
        ],
    )

    totals = alt.Chart(chart_df).mark_text(dy=-10, font="Sora", fontSize=11, fontWeight="bold", color="#163A59").encode(
        x=alt.X("Mois:N", sort=month_order),
        y=alt.Y("Total:Q"),
        text=alt.Text("Total:Q", format=".0f"),
    )

    chart = (
        (bars + totals)
        .properties(height=330)
        .configure_view(strokeOpacity=0)
        .configure_axis(domain=False, gridColor="#E6EEF6", tickColor="#E6EEF6", titleColor="#163A59")
        .configure_legend(labelColor="#163A59")
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("Chaque barre empilée représente la charge mensuelle planifiée après lissage. Les dossiers au-delà de la capacité d’un mois sont décalés sur les mois suivants dans le même régime de vigilance.")



def render_review_schedule_kpis(schedule_df: pd.DataFrame) -> None:
    if schedule_df is None or schedule_df.empty:
        st.info("Aucune revue n'est disponible sur le périmètre filtré.")
        return

    today = pd.Timestamp.today().normalize()
    planned_dates = pd.to_datetime(schedule_df["Date prochaine revue"], errors="coerce")
    current_month = today.to_period("M").strftime("%Y-%m")
    this_month = planned_dates.dt.to_period("M").astype(str).eq(current_month)
    cards = [
        ("SIREN planifiés", f"{len(schedule_df):,}".replace(",", " "), "Portefeuille courant", ""),
        ("Revues ce mois", f"{int(this_month.sum()):,}".replace(",", " "), "Charge du mois courant", ""),
        ("Dossiers lissés", f"{int(schedule_df['Lissé'].eq('Oui').sum()):,}".replace(",", " "), "Décalés sur les mois suivants", ""),
        ("Vigilance critique", f"{int(schedule_df['Régime de vigilance'].eq('Vigilance Critique').sum()):,}".replace(",", " "), "Régime critique", " is-alert"),
        ("Vigilance élevée", f"{int(schedule_df['Régime de vigilance'].eq('Vigilance Élevée').sum()):,}".replace(",", " "), "Régime élevé", ""),
        ("En retard théorique", f"{int((pd.to_datetime(schedule_df['Date prochaine revue théorique'], errors='coerce') < today).sum()):,}".replace(",", " "), "Échéance théorique dépassée", " is-alert"),
    ]
    st.markdown('<h3 class="cm-section-title">Bandeau de synthèse</h3>', unsafe_allow_html=True)
    st.markdown(
        "<div class='cm-kpi-band'>"
        + "".join(
            f"<div class='cm-kpi-card{extra_class}'><div class='cm-kpi-label'>{escape(label)}</div><div class='cm-kpi-value'>{escape(value)}</div><div class='cm-kpi-sub'>{escape(sub)}</div></div>"
            for label, value, sub, extra_class in cards
        )
        + "</div>",
        unsafe_allow_html=True,
    )



def build_review_export_dataframe(schedule_df: pd.DataFrame) -> pd.DataFrame:
    if schedule_df is None or schedule_df.empty:
        return pd.DataFrame(
            columns=[
                "SIREN",
                "Dénomination",
                "Régime de vigilance",
                "Fréquence (mois)",
                "Date de base",
                "Date théorique",
                "Date prochaine revue",
                "Lissé",
                "Décalage (mois)",
            ]
        )

    export_df = schedule_df[[
        "SIREN",
        "Dénomination",
        "Régime de vigilance",
        "Fréquence (mois)",
        "Date de base",
        "Date prochaine revue théorique",
        "Date prochaine revue",
        "Lissé",
        "Décalage (mois)",
    ]].copy()
    export_df = export_df.rename(
        columns={
            "Date prochaine revue théorique": "Date théorique",
            "Date prochaine revue": "Date prochaine revue",
        }
    )
    for col in ["Date de base", "Date théorique", "Date prochaine revue"]:
        export_df[col] = pd.to_datetime(export_df[col], errors="coerce").dt.strftime("%d/%m/%Y").fillna("")
    return export_df



def apply_review_schedule_to_active_base(schedule_df: pd.DataFrame, user: dict) -> int:
    if schedule_df is None or schedule_df.empty:
        return 0

    path = active_dataset_path() / DATA_FILES["base"]
    if not path.exists():
        raise FileNotFoundError("Le fichier 01_Donnees_base_source.csv est introuvable dans le jeu actif.")

    base_raw = read_csv_semicolon(path)
    validate_required_columns(base_raw, "base")
    base_raw[SOC_COL] = normalize_societe_id(base_raw[SOC_COL])
    base_raw["SIREN"] = normalize_siren(base_raw["SIREN"])
    if "Date prochaine revue" not in base_raw.columns:
        base_raw["Date prochaine revue"] = ""

    updates = schedule_df[[SOC_COL, "SIREN", "Date prochaine revue"]].copy()
    updates[SOC_COL] = normalize_societe_id(updates[SOC_COL])
    updates["SIREN"] = normalize_siren(updates["SIREN"])
    updates["Date prochaine revue"] = pd.to_datetime(updates["Date prochaine revue"], errors="coerce").dt.strftime("%d/%m/%Y")
    updates = updates.dropna(subset=KEY_COLUMNS).drop_duplicates(subset=KEY_COLUMNS, keep="last")
    updates = updates.rename(columns={"Date prochaine revue": "Date prochaine revue__calc"})

    merged = base_raw.merge(updates, on=KEY_COLUMNS, how="left")
    mask = merged["Date prochaine revue__calc"].fillna("").astype(str).str.strip().ne("")
    updated_count = int(mask.sum())
    merged.loc[mask, "Date prochaine revue"] = merged.loc[mask, "Date prochaine revue__calc"]
    merged = merged.drop(columns=["Date prochaine revue__calc"])
    merged.to_csv(path, sep=";", index=False, encoding="utf-8-sig")

    manifest = load_manifest() or {}
    manifest["last_review_schedule_apply_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["last_review_schedule_apply_by"] = user.get("username")
    manifest["last_review_schedule_apply_by_name"] = user.get("display_name")
    save_manifest(manifest)
    return updated_count



def render_review_planning_content(
    df: pd.DataFrame,
    *,
    user: dict | None = None,
    show_export: bool = True,
    allow_apply: bool = False,
    notice_key: str | None = None,
    section_caption: str | None = None,
    persist_settings: bool = False,
) -> pd.DataFrame:
    if notice_key and st.session_state.get(notice_key):
        st.success(str(st.session_state.pop(notice_key)))

    if section_caption:
        st.caption(section_caption)

    freq_map, capacity_map, recalc = render_review_rule_editor(df)
    if recalc and persist_settings:
        persist_review_planning_settings(freq_map, capacity_map, user)
        st.success("Planning recalculé avec les paramètres saisis. Les paramètres sont mémorisés pour la suite.")
    elif recalc:
        st.success("Planning recalculé avec les paramètres saisis.")

    schedule_df = build_review_schedule(df, freq_map, capacity_map)
    if schedule_df.empty:
        st.info("Aucune revue à planifier sur le périmètre filtré.")
        return schedule_df

    st.divider()
    render_review_schedule_kpis(schedule_df)

    st.divider()
    st.markdown('<h3 class="cm-section-title">Jalons temporels de l’ensemble des revues</h3>', unsafe_allow_html=True)
    chart_df = build_review_schedule_chart_table(schedule_df)
    render_review_schedule_chart(chart_df)

    if show_export or (allow_apply and user and user.get("role") == "admin"):
        st.divider()
        st.markdown('<h3 class="cm-section-title">Table de planification</h3>', unsafe_allow_html=True)
        export_df = build_review_export_dataframe(schedule_df)

        if allow_apply and user and user.get("role") == "admin":
            info_col, export_col, apply_col = st.columns([4.5, 1.4, 2.1])
        else:
            info_col, export_col = st.columns([5.8, 1.4])
            apply_col = None

        with info_col:
            st.caption("Table exportable par SIREN avec régime de vigilance, fréquence appliquée, date théorique et date planifiée. La diffusion met à jour la colonne Date prochaine revue du fichier 01 pour le périmètre courant.")
        with export_col:
            st.download_button(
                label="Exporter (.csv)",
                data=dataframe_to_csv_bytes(export_df),
                file_name="planification_des_revues.csv",
                mime="text/csv",
                type="secondary",
                key="export_review_schedule_csv",
                use_container_width=True,
            )
        if apply_col is not None:
            with apply_col:
                if st.button(
                    "Diffuser dans l’onglet 01",
                    type="primary",
                    key="apply_review_schedule_to_base",
                    use_container_width=True,
                ):
                    updated_count = apply_review_schedule_to_active_base(schedule_df, user)
                    st.session_state[notice_key or "review_schedule_apply_notice"] = (
                        f"{updated_count} date(s) de prochaine revue ont été diffusées dans le fichier 01 sur le périmètre courant."
                    )
                    st.rerun()

        render_small_table(export_df, bold_numbers=False)

    return schedule_df



def render_review_planning_screen(portfolio: pd.DataFrame, user: dict) -> None:
    render_home_hero("Planification des revues")
    nav = render_primary_navigation("review_dates")
    if nav == "portfolio":
        open_portfolio_view()
        st.rerun()
    if nav == "analysis":
        open_analysis_view()
        st.rerun()

    top_left, top_right = st.columns([5.3, 1.2])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Planification des revues</h3>', unsafe_allow_html=True)
        st.caption("La date de prochaine revue est calculée à partir du régime de vigilance, puis lissée sur les mois suivants si la capacité mensuelle du régime est dépassée.")
    with top_right:
        if st.button("Réinitialiser", type="secondary", key="review_planning_reset"):
            reset_review_filters()
            default_freq = {label: int(REVIEW_FREQUENCY_DEFAULTS.get(label, 12)) for label in VIGILANCE_ORDER}
            default_cap = {label: int(REVIEW_CAPACITY_DEFAULTS.get(label, 10)) for label in VIGILANCE_ORDER}
            for label in VIGILANCE_ORDER:
                st.session_state[f"review_freq_{review_setting_slug(label)}"] = default_freq[label]
                st.session_state[f"review_cap_{review_setting_slug(label)}"] = default_cap[label]
            persist_review_planning_settings(default_freq, default_cap, user)
            st.rerun()

    filter_labels = ["Vigilance", "Risque", "EDD", "Segment", "Pays", "Produit", "Canal", "Analyste", "Valideur"]
    selections: dict[str, str] = {}
    filter_cols = st.columns(5)
    for idx, label in enumerate(filter_labels):
        column = FILTER_MAPPING[label]
        options = ["Tous"] + non_empty_sorted(portfolio[column].unique()) if column in portfolio.columns else ["Tous"]
        state_key = "review_filter_" + label
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with filter_cols[idx % 5]:
            selections[label] = st.selectbox(label, options=options, key=state_key)
        if idx % 5 == 4 and idx < len(filter_labels) - 1:
            filter_cols = st.columns(5)

    filtered = apply_filters(portfolio, selections)
    if filtered.empty:
        st.warning("Aucun client ne correspond au périmètre société + filtres sélectionnés.")
        return

    st.divider()
    render_review_planning_content(
        filtered,
        user=user,
        show_export=True,
        allow_apply=True,
        notice_key="review_schedule_apply_notice",
        persist_settings=True,
    )



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

    render_admin_data_manager(user)
    sync_view_state_from_query_params()

    try:
        base, indicators, history, portfolio = load_app_datasets()
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

    current_view = st.session_state.get("cm_view", "portfolio")
    scoped_indicators = restrict_to_societies(indicators, selected_societies)
    scoped_history = restrict_to_societies(history, selected_societies)
    if current_view == "client":
        render_client_screen(scoped, scoped_indicators, scoped_history, selected_societies, allowed_societies)
        return

    if current_view == "analysis":
        render_analysis_screen(scoped, scoped_indicators)
        return

    if current_view == "review_dates":
        render_review_planning_screen(scoped, user)
        return

    if current_view == "review_simulations":
        render_review_simulations_screen(scoped, user)
        return

    render_home_hero("Portefeuille 360°")
    nav = render_primary_navigation("portfolio")
    if nav == "analysis":
        open_analysis_view()
        st.rerun()
    if nav == "review_dates":
        open_review_dates_view()
        st.rerun()
    if nav == "review_simulations":
        open_review_simulations_view()
        st.rerun()

    render_client_launcher(scoped, key_prefix="header")

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
        render_alert_block("Alertes de gouvernance", build_alert_table(filtered))

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
    priority_df = build_priority_table(filtered, top_n=10)
    render_clickable_styled_dataframe(style_dataframe(priority_df), priority_df, use_container_width=True, height=420, hide_index=True, key_prefix="priority_table")

    export_columns = [c for c in DISPLAY_COLUMNS if c in filtered.columns]
    st.download_button(
        label="Exporter la vue filtrée (.csv)",
        data=dataframe_to_csv_bytes(filtered[export_columns]),
        file_name="tableau1_portefeuille_filtre.csv",
        mime="text/csv",
        type="primary",
    )

    with st.expander("Aperçu des données sous-jacentes filtrées"):
        render_clickable_styled_dataframe(style_dataframe(filtered[export_columns]), filtered[export_columns], use_container_width=True, height=420, hide_index=True, key_prefix="filtered_table")




if __name__ == "__main__":
    main()
