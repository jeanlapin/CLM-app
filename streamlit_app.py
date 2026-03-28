import streamlit as st
import pandas as pd

# Configuration Be CLM
st.set_page_config(page_title="Be CLM - Portefeuille Clients", layout="wide")

# Style CSS personnalisé pour le look Be CLM
st.markdown("""
    <style>
    .stApp { background-color: #002b45; color: white; }
    .metric-card { background-color: #ffffff1a; padding: 20px; border-radius: 10px; text-align: center; }
    h1, h2, h3 { color: #ffffff; }
    .stDataFrame { background-color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Be CLM - Classification Management")

@st.cache_data
def load_data():
    try:
        # Lecture de votre fichier avec vos colonnes réelles
        df = pd.read_csv("01_Donnees_base_source.csv", sep=';', encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
        return None

df = load_data()

if df is not None:
    # --- BANDEAU DE SYNTHÈSE (KPIs) ---
    st.subheader("Synthèse du Portefeuille")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Clients", len(df))
    
    with col2:
        # Calcul des risques potentiels (colonne exacte de votre fichier)
        risques_potentiels = len(df[df['Statut de risque (import SaaS source)'] == 'Risque potentiel'])
        st.metric("Risques Potentiels", risques_potentiels)

    with col3:
        # Clients en France
        fr_clients = len(df[df['Pays de résidence'] == 'France'])
        st.metric("Clients France", fr_clients)

    with col4:
        # Clients Hors France
        int_clients = len(df[df['Pays de résidence'] != 'France'])
        st.metric("Hors France", int_clients)

    # --- TABLEAU DE BORD ---
    st.markdown("---")
    st.subheader("Détail du Portefeuille")
    
    # Filtres interactifs
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        segment_choice = st.multiselect("Filtrer par Segment", options=df['Segment'].unique())
    with col_f2:
        pays_choice = st.multiselect("Filtrer par Pays", options=df['Pays de résidence'].unique())

    # Application des filtres
    df_filtered = df.copy()
    if segment_choice:
        df_filtered = df_filtered[df_filtered['Segment'].isin(segment_choice)]
    if pays_choice:
        df_filtered = df_filtered[df_filtered['Pays de résidence'].isin(pays_choice)]

    # Affichage du tableau (colonnes principales de votre fichier)
    st.dataframe(df_filtered[[
        'SIREN', 'Dénomination', 'Pays de résidence', 
        'Segment', 'Statut EDD', 'Statut de risque (import SaaS source)'
    ]], use_container_width=True)

else:
    st.warning("Veuillez vérifier que le fichier '01_Donnees_base_source.csv' est bien présent à la racine de votre dépôt GitHub.")
