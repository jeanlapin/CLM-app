import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURATION ET DESIGN (Be CLM)
# ==========================================
st.set_page_config(
    page_title="Classification Management", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thème Bleu Marine très sobre via CSS
st.markdown("""
    <style>
    /* Couleur principale Bleu Marine pour les titres et boutons */
    h1, h2, h3 { color: #000080 !important; }
    .stButton>button { background-color: #000080; color: white; border-radius: 4px; border: none; }
    .stButton>button:hover { background-color: #000050; color: white; }
    
    /* Style du header/logo */
    .header-container { display: flex; align-items: center; padding-bottom: 20px; border-bottom: 2px solid #000080; margin-bottom: 20px;}
    .logo-text { font-size: 24px; font-weight: bold; color: #000080; margin-left: 15px; letter-spacing: 1px;}
    .app-title { font-size: 18px; color: #666; margin-left: auto; }
    
    /* KPI Metrics styling */
    div[data-testid="metric-container"] { border: 1px solid #e0e0e0; padding: 10px; border-radius: 5px; border-left: 4px solid #000080; background-color: #fcfcfc;}
    </style>
""", unsafe_allow_html=True)

# En-tête avec Logo Be CLM simulé
st.markdown("""
    <div class="header-container">
        <div style="width: 40px; height: 40px; background-color: #000080; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 20px;">Be</div>
        <div class="logo-text">Be CLM</div>
        <div class="app-title">Classification Management</div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 2. SIMULATION AUTHENTIFICATION MULTI-SOCIÉTÉS
# ==========================================
st.sidebar.markdown("### 🔐 Authentification")
# Simulation d'une base d'utilisateurs et de leurs sociétés rattachées
users_db = {
    "jean.dupont@filiale-a.com": {"nom": "Jean Dupont", "societe": "Société Alpha (Filiale A)", "role": "Analyste"},
    "marie.curie@groupe-b.com": {"nom": "Marie Curie", "societe": "Société Beta (Groupe B)", "role": "Manager"},
    "admin@be-clm.com": {"nom": "Admin Système", "societe": "Toutes (Vue consolidée)", "role": "Superviseur"}
}

selected_user = st.sidebar.selectbox("Connexion Utilisateur", list(users_db.keys()))
user_info = users_db[selected_user]

st.sidebar.info(f"**Connecté en tant que :**\n\n👤 {user_info['nom']}\n\n🏢 {user_info['societe']}\n\n🔑 {user_info['role']}")
st.sidebar.markdown("---")

# ==========================================
# 3. CHARGEMENT ET PRÉPARATION DES DONNÉES
# ==========================================
@st.cache_data
def load_data():
    try:
        # Chargement des fichiers sources
        df_base = pd.read_csv("01_Donnees_base_source.csv")
        
        # Nettoyage et préparation selon les specs
        # On s'assure que les colonnes clés existent pour le prototype, sinon on les simule pour l'affichage
        if "Niveau de vigilance" not in df_base.columns:
            df_base["Niveau de vigilance"] = df_base.get("Score de priorité", "Standard") # Fallback logique
            
        if "Statut de risque (import SaaS source)" not in df_base.columns:
            # Application de la règle de dérivation (Chapitre 2.1) si absent (Simulé ici en fallback)
            df_base["Statut de risque (import SaaS source)"] = "À évaluer"
            
        return df_base
    except FileNotFoundError:
        # Création d'un jeu de données factice si les fichiers ne sont pas trouvés pour que le prototype tourne quand même
        data = {
            "SIREN": ["111111111", "222222222", "333333333", "444444444", "555555555"],
            "Dénomination": ["Client A", "Client B", "Client C", "Client D", "Client E"],
            "Segment": ["PME", "Corporate", "Retail", "Corporate", "PME"],
            "Pays de résidence": ["France", "Luxembourg", "France", "Panama", "Belgique"],
            "Niveau de vigilance": ["Standard", "Renforcée", "Standard", "Maximale", "Renforcée"],
            "Statut de risque (import SaaS source)": ["Aucun risque détecté", "Risque potentiel", "Risque mitigé", "Risque avéré", "Risque potentiel"],
            "Statut EDD": ["Clôturée", "À ouvrir", "Non requise", "En cours", "En retard"]
        }
        return pd.DataFrame(data)

df = load_data()

# Filtrage Multi-Sociétés (Cloisonnement des données)
# Dans la réalité, le fichier CSV aurait une colonne "Entité_ID". Ici on simule le filtre.
if user_info["societe"] == "Société Alpha (Filiale A)":
    # On simule que Alpha ne voit que la France et la Belgique
    df = df[df["Pays de résidence"].isin(["France", "Belgique"])]
elif user_info["societe"] == "Société Beta (Groupe B)":
    # Beta voit le reste
    df = df[~df["Pays de résidence"].isin(["France", "Belgique"])]
# Si Admin (Toutes), pas de filtre.

# ==========================================
# 4. FILTRES DE L'ÉCRAN (Barre latérale)
# ==========================================
st.sidebar.markdown("### 📊 Filtres du Portefeuille")
col_pays = df["Pays de résidence"].dropna().unique() if "Pays de résidence" in df.columns else []
col_segment = df["Segment"].dropna().unique() if "Segment" in df.columns else []

filtre_pays = st.sidebar.multiselect("Pays / Zone", col_pays)
filtre_segment = st.sidebar.multiselect("Segment", col_segment)
filtre_vigilance = st.sidebar.multiselect("Niveau de Vigilance", df["Niveau de vigilance"].unique())

# Application des filtres
df_filtered = df.copy()
if filtre_pays:
    df_filtered = df_filtered[df_filtered["Pays de résidence"].isin(filtre_pays)]
if filtre_segment:
    df_filtered = df_filtered[df_filtered["Segment"].isin(filtre_segment)]
if filtre_vigilance:
    df_filtered = df_filtered[df_filtered["Niveau de vigilance"].isin(filtre_vigilance)]

# ==========================================
# 5. CONSTRUCTION DE L'ÉCRAN 1 : PORTEFEUILLE
# ==========================================
st.markdown("## Vue d'ensemble du Portefeuille")

# --- BANDEAU DE SYNTHÈSE (KPIs) ---
total_clients = len(df_filtered)
# Gestion sécurisée des valeurs pour éviter les erreurs si la donnée n'existe pas
renforcee_count = len(df_filtered[df_filtered["Niveau de vigilance"].isin(["Renforcée", "Maximale"])])
part_renforcee = (renforcee_count / total_clients * 100) if total_clients > 0 else 0
risque_avere = len(df_filtered[df_filtered["Statut de risque (import SaaS source)"] == "Risque avéré"])

if "Statut EDD" in df_filtered.columns:
    edd_retard = len(df_filtered[df_filtered["Statut EDD"].str.contains("retard", case=False, na=False)])
else:
    edd_retard = 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Clients", total_clients)
col2.metric("Vigilance Renforcée/Max", f"{renforcee_count} ({part_renforcee:.1f}%)")
col3.metric("Risques Avérés", risque_avere)
col4.metric("EDD en retard", edd_retard)
col5.metric("Alertes Gouvernance", "0") # Placeholder pour le Lot 2 (Tableau 4)

st.markdown("---")

# --- BLOC DE VISUALISATION (Graphiques) ---
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.markdown("#### Répartition par Niveau de Vigilance")
    vigilance_counts = df_filtered["Niveau de vigilance"].value_counts()
    st.bar_chart(vigilance_counts, color="#000080")

with col_graph2:
    st.markdown("#### Répartition par Statut de Risque")
    risque_counts = df_filtered["Statut de risque (import SaaS source)"].value_counts()
    st.bar_chart(risque_counts, color="#4682B4") # Bleu acier pour contraster

# --- BLOC DE CONCENTRATION & DOSSIERS PRIORITAIRES ---
st.markdown("### 🚨 Dossiers Prioritaires (Vigilance Élevée / Risque Avéré)")

# On filtre pour ne montrer que les cas nécessitant une attention
dossiers_prio = df_filtered[
    (df_filtered["Niveau de vigilance"].isin(["Renforcée", "Maximale"])) | 
    (df_filtered["Statut de risque (import SaaS source)"] == "Risque avéré")
]

# Sélection des colonnes pertinentes demandées dans la spécification
cols_to_show = ["SIREN", "Dénomination", "Segment", "Pays de résidence", "Niveau de vigilance", "Statut de risque (import SaaS source)"]
if "Statut EDD" in dossiers_prio.columns:
    cols_to_show.append("Statut EDD")

st.dataframe(dossiers_prio[cols_to_show], use_container_width=True)

st.caption("Données filtrées selon le périmètre de la société sélectionnée. Conformité métier assurée par le moteur externe.")
