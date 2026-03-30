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

    top_left, top_right = st.columns([5.2, 1.2])
    with top_left:
        st.markdown('<h3 class="cm-section-title">Revues &amp; Simulations</h3>', unsafe_allow_html=True)
        st.caption(
            "Choisissez un type de revue, préparez un lot de 10 SIREN maximum et exportez les consignes simulées."
        )
    with top_right:
        if st.button("Réinitialiser", type="secondary", key="review_sim_reset"):
            for label in ["Vigilance", "Risque", "EDD", "Segment", "Pays", "Produit", "Canal", "Analyste", "Valideur"]:
                st.session_state.pop("review_sim_filter_" + label, None)
            st.session_state.pop("review_sim_type", None)
            st.rerun()

    review_types = ["Tous"] + list(dict.fromkeys(REVIEW_TYPE_BY_VIGILANCE.values()))
    type_to_vigilance = {v: k for k, v in REVIEW_TYPE_BY_VIGILANCE.items()}

    review_type_col, review_objectives_col = st.columns([2.1, 3.9])
    with review_type_col:
        if st.session_state.get("review_sim_type") not in review_types:
            st.session_state["review_sim_type"] = "Tous"
        selected_review_type = st.selectbox(
            "Type de revue",
            options=review_types,
            key="review_sim_type",
            help="Le type de revue est déduit du régime de vigilance. Vous pouvez concentrer l'écran sur un seul type ou garder tous les dossiers.",
        )

    selected_vigilance_for_prompt = type_to_vigilance.get(selected_review_type, "Vigilance Modérée")
    if selected_review_type == "Tous":
        objective_1 = "Cibler les dossiers à traiter, préparer les consignes et répartir la charge de revue."
        objective_2 = "Conserver pour chaque SIREN une synthèse exploitable et un niveau de vigilance espéré après remédiation."
        prompt_value = (
            "Tu es un analyste conformité. Prépare des consignes de revue adaptées au type de revue du dossier, "
            "au régime de vigilance, aux alertes calculées actives et au statut EDD. La sortie doit contenir : "
            "diagnostic, actions prioritaires, justificatifs à obtenir, et statut de vigilance estimé après remédiation."
        )
        kicker = "Tous les types"
    else:
        objective_1, objective_2 = review_objectives_for_vigilance(selected_vigilance_for_prompt)
        prompt_value = build_generic_review_prompt(selected_vigilance_for_prompt)
        kicker = selected_review_type

    with review_objectives_col:
        st.markdown(
            "<div class='cm-analysis-mode-shell'>"
            f"<div class='cm-analysis-mode-kicker'>{escape(kicker)}</div>"
            "<div class='cm-analysis-mode-title'>Objectifs de la revue</div>"
            f"<div class='cm-analysis-mode-note'>1. {escape(objective_1)}<br>2. {escape(objective_2)}</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.text_area(
            "Prompt prêt à l’emploi",
            value=prompt_value,
            height=190,
            key="review_sim_prompt_preview",
        )

    filter_labels = ["Vigilance", "Risque", "EDD", "Segment", "Pays", "Produit", "Canal", "Analyste", "Valideur"]
    selections: dict[str, str] = {}
    filter_cols = st.columns(5)
    for idx, label in enumerate(filter_labels):
        column = FILTER_MAPPING[label]
        options = ["Tous"] + non_empty_sorted(portfolio[column].unique()) if column in portfolio.columns else ["Tous"]
        state_key = "review_sim_filter_" + label
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

    working_df = build_review_simulation_working_table(filtered, "")
    if selected_review_type != "Tous":
        working_df = working_df[working_df["Type de revue"].astype(str).eq(selected_review_type)].copy()
    if working_df.empty:
        st.info("Aucun SIREN n’est à traiter pour le type de revue retenu sur ce périmètre.")
        return

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
    meta = filtered[[c for c in metadata_cols if c in filtered.columns]].copy()
    work_for_editor = working_df.merge(
        meta,
        on=KEY_COLUMNS + (["Date prochaine revue"] if "Date prochaine revue" in working_df.columns and "Date prochaine revue" in meta.columns else []),
        how="left",
    )
    if len(work_for_editor) != len(working_df):
        work_for_editor = working_df.merge(meta, on=KEY_COLUMNS, how="left")

    st.divider()
    stats_col, action_col, export_col = st.columns([3.4, 2.2, 1.4])
    with stats_col:
        st.caption(
            "Sélectionnez jusqu’à 10 SIREN dans la colonne 'Sélection' pour préparer le lot. "
            "La colonne 'Explique moi' stocke la simulation avant branchement de Gemini."
        )

    edited_df = render_review_simulation_editor(work_for_editor, key=f"review_sim_editor_{selected_review_type}")
    persist_review_simulation_subset(edited_df)

    selected_count = int(edited_df["Sélection"].fillna(False).astype(bool).sum())
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
