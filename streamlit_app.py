import streamlit as st
import pandas as pd
import altair as alt

# Configuration Be CLM
st.set_page_config(page_title="Be CLM - Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #002b45; color: white; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight: 700; }
    h1, h2, h3 { color: #ffffff !important; }
    .stDataFrame { background-color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_and_merge():
    try:
        # Fichier 01
        df1 = pd.read_csv("01_Donnees_base_source.csv", sep=';', encoding='utf-8').dropna(subset=['SIREN'])
        df1['SIREN'] = pd.to_numeric(df1['SIREN'], errors='coerce').fillna(0).astype(int)
        
        # Fichier 02 (Indicateurs)
        df2 = pd.read_csv("02_Indicateurs_source.csv", sep=';', encoding='utf-8').dropna(subset=['SIREN'])
        df2['SIREN'] = pd.to_numeric(df2['SIREN'], errors='coerce').fillna(0).astype(int)
        
        # Fusion sur SIREN - On récupère la colonne 'Statut' du fichier 02
        # On s'assure que 'Statut' existe dans df2
        if 'Statut' in df2.columns:
            df_merged = pd.merge(df1, df2[['SIREN', 'Statut']], on='SIREN', how='left')
            df_merged = df_merged.rename(columns={'Statut': 'Statut de Vigilance'})
        else:
            df_merged = df1
            st.error("La colonne 'Statut' est absente du fichier 02.")
            
        return df_merged
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return None

df = load_and_merge()

st.title("🛡️ Be CLM - Classification Management")

if df is not None:
    # FILTRES
    st.sidebar.header("Filtres")
    vig_col = 'Statut de Vigilance' if 'Statut de Vigilance' in df.columns else 'Statut EDD'
    
    sel_vig = st.sidebar.multiselect("Statut de Vigilance", options=sorted(df[vig_col].dropna().unique()))
    df_f = df[df[vig_col].isin(sel_vig)] if sel_vig else df

    # AFFICHAGE
    c_kpi, c_jauge = st.columns([2, 1])
    with c_kpi:
        st.metric("Total Clients", len(df_f))
        st.metric("Risques Potentiels", len(df_f[df_f['Statut de risque (import SaaS source)'].str.contains('potentiel', na=False, case=False)]))
    
    with c_jauge:
        if vig_col in df_f.columns:
            source = df_f[vig_col].value_counts().reset_index()
            source.columns = ['Statut', 'Nombre']
            chart = alt.Chart(source).mark_arc(innerRadius=50).encode(
                theta="Nombre", color="Statut", tooltip=['Statut', 'Nombre']
            ).properties(height=200, title="Répartition Vigilance")
            st.altair_chart(chart, width='stretch') # Corrigé selon vos logs !

    st.dataframe(df_f[['SIREN', 'Dénomination', vig_col]], width='stretch')
