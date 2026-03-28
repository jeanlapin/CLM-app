import streamlit as st
import pandas as pd
import altair as alt

# 1. Configuration et Style Premium
st.set_page_config(page_title="Be CLM - Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #002b45; color: white; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight: 700; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 700 !important; }
    .stDataFrame { background-color: white; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #001f33 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Chargement et Nettoyage
def load_data():
    try:
        df = pd.read_csv("01_Donnees_base_source.csv", sep=';', encoding='utf-8')
        df = df.dropna(subset=['SIREN']) # Supprime les lignes vides
        return df
    except:
        return None

df_base = load_data()

st.title("🛡️ Be CLM - Classification Management")

if df_base is not None:
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres de recherche")
    
    seg_opt = sorted(df_base['Segment'].dropna().unique())
    sel_seg = st.sidebar.multiselect("Segments", options=seg_opt)
    
    pays_opt = sorted(df_base['Pays de résidence'].dropna().unique())
    sel_pays = st.sidebar.multiselect("Pays", options=pays_opt)
    
    # NOUVEAU : Filtre Statut de Risque
    risk_opt = sorted(df_base['Statut de risque (import SaaS source)'].dropna().unique())
    sel_risk = st.sidebar.multiselect("Statut de Risque", options=risk_opt)
    
    # NOUVEAU : Filtre Statut EDD (Vigilance)
    edd_opt = sorted(df_base['Statut EDD'].dropna().unique())
    sel_edd = st.sidebar.multiselect("Statut EDD / Vigilance", options=edd_opt)

    # Application des filtres
    df_f = df_base.copy()
    if sel_seg: df_f = df_f[df_f['Segment'].isin(sel_seg)]
    if sel_pays: df_f = df_f[df_f['Pays de résidence'].isin(sel_pays)]
    if sel_risk: df_f = df_f[df_f['Statut de risque (import SaaS source)'].isin(sel_risk)]
    if sel_edd: df_f = df_f[df_f['Statut EDD'].isin(sel_edd)]

    # --- BANDEAU DE SYNTHÈSE AVEC JAUGE ---
    st.subheader("Synthèse et Pilotage du Portefeuille")
    
    col_kpi, col_chart = st.columns([2, 1]) # 2/3 pour les chiffres, 1/3 pour la jauge
    
    with col_kpi:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Clients", len(df_f))
            fr = len(df_f[df_f['Pays de résidence'] == 'France'])
            st.metric("Clients France", fr)
        with c2:
            rp = len(df_f[df_f['Statut de risque (import SaaS source)'].str.contains('potentiel', na=False, case=False)])
            st.metric("Risques Potentiels", rp)
            st.metric("International", len(df_f) - fr)

    with col_chart:
        # Création de la Jauge (Donut Chart) pour le Statut EDD
        edd_counts = df_f['Statut EDD'].value_counts().reset_index()
        edd_counts.columns = ['Statut', 'Nombre']
        
        chart = alt.Chart(edd_counts).mark_arc(innerRadius=40).encode(
            theta=alt.Theta(field="Nombre", type="quantitative"),
            color=alt.Color(field="Statut", type="nominal", 
                            scale=alt.Scale(range=['#00d4ff', '#ff4b4b', '#ffaa00', '#2ecc71'])),
            tooltip=['Statut', 'Nombre']
        ).properties(width=180, height=180, title="Répartition Vigilance")
        
        st.altair_chart(chart, use_container_width=True)

    # --- TABLEAU DE DÉTAIL ---
    st.markdown("---")
    st.subheader("Liste des Dossiers Filtrés")
    cols_display = ['SIREN', 'Dénomination', 'Pays de résidence', 'Segment', 'Statut EDD', 'Statut de risque (import SaaS source)']
    st.dataframe(df_f[cols_display], use_container_width=True)

else:
    st.error("Fichier source introuvable.")
