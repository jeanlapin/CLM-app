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
    
    /* Libellés en blanc pur */
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
        # Lecture du fichier
        df = pd.read_csv("01_Donnees_base_source.csv", sep=';', encoding='utf-8')
        # On supprime les lignes vides (basé sur SIREN)
        df = df.dropna(subset=['SIREN'])
        return df
    except Exception as e:
        return None

df_base = load_data()

st.title("🛡️ Be CLM - Classification Management")

if df_base is not None:
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres de recherche")
    
    sel_seg = st.sidebar.multiselect("Segments", options=sorted(df_base['Segment'].dropna().unique()))
    sel_pays = st.sidebar.multiselect("Pays", options=sorted(df_base['Pays de résidence'].dropna().unique()))
    
    # Filtre Statut de Risque
    risk_col = 'Statut de risque (import SaaS source)'
    sel_risk = st.sidebar.multiselect("Statut de Risque", options=sorted(df_base[risk_col].dropna().unique()))
    
    # Filtre Statut de Vigilance
    # Si la colonne s'appelle 'Vigilance' dans votre fichier
    vig_col = 'Vigilance' if 'Vigilance' in df_base.columns else 'Statut EDD'
    sel_vig = st.sidebar.multiselect("Niveau de Vigilance", options=sorted(df_base[vig_col].dropna().unique()))

    # Application des filtres
    df_f = df_base.copy()
    if sel_seg: df_f = df_f[df_f['Segment'].isin(sel_seg)]
    if sel_pays: df_f = df_f[df_f['Pays de résidence'].isin(sel_pays)]
    if sel_risk: df_f = df_f[df_f[risk_col].isin(sel_risk)]
    if sel_vig: df_f = df_f[df_f[vig_col].isin(sel_vig)]

    # --- BANDEAU DE SYNTHÈSE ---
    st.subheader("Synthèse et Pilotage du Portefeuille")
    
    col_kpi, col_chart = st.columns([2, 1])
    
    with col_kpi:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Clients", len(df_f))
            fr = len(df_f[df_f['Pays de résidence'] == 'France'])
            st.metric("Clients France", fr)
        with c2:
            rp = len(df_f[df_f[risk_col].str.contains('potentiel', na=False, case=False)])
            st.metric("Risques Potentiels", rp)
            st.metric("International", len(df_f) - fr)

    with col_chart:
        # JAUGE SUR LE STATUT DE VIGILANCE
        vig_counts = df_f[vig_col].value_counts().reset_index()
        vig_counts.columns = ['Statut', 'Nombre']
        
        # Couleurs adaptées : Bleu pour Standard/Aucune, Orange/Rouge pour Renforcée
        chart = alt.Chart(vig_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Nombre", type="quantitative"),
            color=alt.Color(field="Statut", type="nominal", 
                            scale=alt.Scale(range=['#00d4ff', '#ffaa00', '#ff4b4b', '#2ecc71'])),
            tooltip=['Statut', 'Nombre']
        ).properties(height=200, title="Répartition par Vigilance")
        
        st.altair_chart(chart, use_container_width=True)

    # --- TABLEAU DE DÉTAIL ---
    st.markdown("---")
    st.subheader("Liste des Dossiers")
    cols_display = ['SIREN', 'Dénomination', 'Pays de résidence', 'Segment', vig_col, risk_col]
    st.dataframe(df_f[cols_display], use_container_width=True)

else:
    st.error("Fichier source introuvable ou mal nommé sur GitHub.")
