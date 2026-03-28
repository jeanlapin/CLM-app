import streamlit as st
import pandas as pd
import altair as alt

# 1. Configuration et Style Premium Be CLM
st.set_page_config(page_title="Be CLM - Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #002b45; color: white; }
    
    /* Libellés en BLANC PUR */
    [data-testid="stMetricLabel"] { 
        color: #ffffff !important; 
        font-weight: 600 !important; 
        font-size: 1.1rem !important; 
    }
    [data-testid="stMetricValue"] { 
        color: #00d4ff !important; 
        font-weight: 700 !important; 
    }
    
    h1, h2, h3 { color: #ffffff !important; font-weight: 700 !important; }
    .stDataFrame { background-color: white; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #001f33 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Chargement et Fusion des données (Fichier 01 + Fichier 02)
@st.cache_data
def load_and_merge_data():
    try:
        # Lecture du fichier de base (Fichier 01)
        df_base = pd.read_csv("01_Donnees_base_source.csv", sep=';', encoding='utf-8')
        df_base = df_base.dropna(subset=['SIREN'])
        # Normalisation du SIREN pour la fusion
        df_base['SIREN'] = pd.to_numeric(df_base['SIREN'], errors='coerce').fillna(0).astype(int)

        # Lecture du fichier indicateurs (Fichier 02)
        df_ind = pd.read_csv("02_Indicateurs_source.csv", sep=';', encoding='utf-8')
        df_ind = df_ind.dropna(subset=['SIREN'])
        df_ind['SIREN'] = pd.to_numeric(df_ind['SIREN'], errors='coerce').fillna(0).astype(int)

        # FUSION : On prend le SIREN du 01 et on va chercher le "Statut" dans le 02
        # On renomme "Statut" en "Statut de Vigilance" pour plus de clarté
        if 'Statut' in df_ind.columns:
            df_ind_subset = df_ind[['SIREN', 'Statut']].rename(columns={'Statut': 'Statut de Vigilance'})
            # Fusion à gauche pour garder tous les clients du fichier 01
            df_final = pd.merge(df_base, df_ind_subset, on='SIREN', how='left')
        else:
            st.error("La colonne 'Statut' n'existe pas dans 02_Indicateurs_source.csv")
            return df_base

        return df_final
    except Exception as e:
        st.error(f"Erreur lors de la fusion des fichiers : {e}")
        return None

df = load_and_merge_data()

st.title("🛡️ Be CLM - Classification Management")

if df is not None:
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres")
    
    f_seg = st.sidebar.multiselect("Segment", options=sorted(df['Segment'].unique()))
    f_pays = st.sidebar.multiselect("Pays", options=sorted(df['Pays de résidence'].unique()))
    
    risk_col = 'Statut de risque (import SaaS source)'
    f_risk = st.sidebar.multiselect("Statut de Risque", options=sorted(df[risk_col].unique()))
    
    # Le filtre utilise maintenant la donnée venant du fichier Indicateurs
    vig_col = 'Statut de Vigilance'
    f_vig = st.sidebar.multiselect("Statut de Vigilance", options=sorted(df[vig_col].dropna().unique()))

    # Application des filtres
    df_f = df.copy()
    if f_seg: df_f = df_f[df_f['Segment'].isin(f_seg)]
    if f_pays: df_f = df_f[df_f['Pays de résidence'].isin(f_pays)]
    if f_risk: df_f = df_f[df_f[risk_col].isin(f_risk)]
    if f_vig: df_f = df_f[df_f[vig_col].isin(f_vig)]

    # --- SYNTHÈSE ET JAUGE (Données Indicateurs) ---
    col_metrics, col_gauge = st.columns([2, 1])

    with col_metrics:
        m1, m2 = st.columns(2)
        m1.metric("Total Clients", len(df_f))
        m1.metric("Clients France", len(df_f[df_f['Pays de résidence'] == 'France']))
        m2.metric("Risques Potentiels", len(df_f[df_f[risk_col] == 'Risque potentiel']))
        m2.metric("International", len(df_f[df_f['Pays de résidence'] != 'France']))

    with col_gauge:
        # JAUGE SUR LE STATUT DU FICHIER INDICATEURS
        if vig_col in df_f.columns:
            vig_data = df_f[vig_col].value_counts().reset_index()
            vig_data.columns = ['Statut', 'Nombre']
            chart = alt.Chart(vig_data).mark_arc(innerRadius=50).encode(
                theta="Nombre",
                color=alt.Color("Statut", scale=alt.Scale(range=['#00d4ff', '#ffaa00', '#ff4b4b', '#2ecc71'])),
                tooltip=['Statut', 'Nombre']
            ).properties(height=220, title="Répartition Vigilance")
            st.altair_chart(chart, width='stretch')

    # --- TABLEAU ---
    st.markdown("---")
    # On affiche bien la colonne fusionnée "Statut de Vigilance"
    cols_to_show = ['SIREN', 'Dénomination', 'Pays de résidence', vig_col, risk_col]
    st.dataframe(df_f[cols_to_show], width='stretch')
else:
    st.error("Impossible de charger les données. Vérifiez vos fichiers sur GitHub.")
