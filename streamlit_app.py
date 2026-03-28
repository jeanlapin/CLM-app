import streamlit as st
import pandas as pd

# Configuration Be CLM Premium
st.set_page_config(page_title="Be CLM - Dashboard", layout="wide")

# Style Be CLM : Police Inter, Fond Marine, Textes Blancs
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #002b45;
        color: white;
    }

    /* FORCER LE BLANC SUR LES LIBELLÉS DES MÉTRIQUES (Ligne Total) */
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }

    /* Couleur des chiffres (Valeurs) */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-weight: 700;
    }

    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Nettoyage du tableau pour qu'il soit pro */
    .stDataFrame {
        background-color: white;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

def load_and_clean(file_name):
    try:
        # Lecture avec point-virgule
        df = pd.read_csv(file_name, sep=';', encoding='utf-8')
        # On supprime les lignes où le SIREN est vide (enlève les 944 lignes inutiles)
        df = df.dropna(subset=['SIREN'])
        return df
    except:
        return None

# Chargement des données
df_base = load_and_clean("01_Donnees_base_source.csv")

st.title("🛡️ Be CLM - Portefeuille Clients")

if df_base is not None:
    # --- CALCULS ---
    total_clients = len(df_base)
    france = len(df_base[df_base['Pays de résidence'] == 'France'])
    etranger = total_clients - france
    # On gère les majuscules/minuscules pour le risque potentiel
    risques_p = len(df_base[df_base['Statut de risque (import SaaS source)'].str.contains('potentiel', na=False, case=False)])

    # --- BANDEAU DE SYNTHÈSE ---
    st.markdown("### Synthèse du Portefeuille")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clients", f"{total_clients}")
    with col2:
        st.metric("Risques Potentiels", f"{risques_p}")
    with col3:
        st.metric("Clients France", f"{france}")
    with col4:
        st.metric("Clients International", f"{etranger}")

    st.markdown("---")
    st.subheader("Détail des Dossiers")
    
    # Affichage du tableau nettoyé
    cols = ['SIREN', 'Dénomination', 'Pays de résidence', 'Segment', 'Statut de risque (import SaaS source)']
    st.dataframe(df_base[cols], use_container_width=True)

else:
    st.error("Fichier source introuvable. Vérifiez l'import sur GitHub.")
