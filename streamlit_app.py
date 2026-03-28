from __future__ import annotations

import streamlit as st

from tableau1_logic import (
    CRITICAL_VIGILANCE,
    DISPLAY_COLUMNS,
    FILTER_MAPPING,
    RISK_ORDER,
    VIGILANCE_ORDER,
    apply_filters,
    build_alert_table,
    build_distribution,
    build_portfolio_dataset,
    build_priority_table,
    dataframe_to_csv_bytes,
    format_percent_column,
    non_empty_sorted,
    ranked_counts,
)

PAGE_TITLE = "Tableau 1 – Portefeuille"


@st.cache_data(show_spinner=False)
def load_portfolio():
    return build_portfolio_dataset()


def reset_filters() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("filter_"):
            st.session_state[key] = "Tous"


def render_filters(df):
    st.subheader("Filtres")
    st.caption("Les filtres sont cumulatifs et recalculent tout le tableau.")

    if st.button("Réinitialiser les filtres", type="secondary"):
        reset_filters()

    row1 = st.columns(5)
    row2 = st.columns(4)
    labels = list(FILTER_MAPPING.keys())
    selections = {}

    for container, label in zip(row1 + row2, labels, strict=False):
        column = FILTER_MAPPING[label]
        options = ["Tous", *non_empty_sorted(df[column].unique())]
        state_key = f"filter_{label}"
        if st.session_state.get(state_key) not in options:
            st.session_state[state_key] = "Tous"
        with container:
            selections[label] = st.selectbox(label, options=options, key=state_key)
    return selections


def render_kpis(df):
    st.subheader("Bandeau de synthèse")
    total = len(df)
    vigilance_renforcee = int(df["Vigilance"].isin(CRITICAL_VIGILANCE).sum())
    risque_avere = int((df["Risque"] == "Risque avéré").sum())
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

    if total:
        last_update = df["Vigilance Date de mise à jour"].max()
        if last_update == last_update:
            st.caption(f"Fraîcheur visible : dernière mise à jour vigilance = {last_update:%d/%m/%Y}.")


def render_distribution_block(title, dist_df, index_col):
    st.markdown(f"**{title}**")
    st.bar_chart(dist_df.set_index(index_col)[["Nb"]], height=260)
    st.dataframe(format_percent_column(dist_df), hide_index=True, use_container_width=True)


def render_top_block(title, df):
    st.markdown(f"**{title}**")
    st.dataframe(df, hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.title(PAGE_TITLE)
    st.caption(
        "Reproduction Streamlit du tableau 1 basée sur 01_Donnees_base_source.csv, "
        "02_Indicateurs_source.csv et 03_Indicateurs_historique.csv."
    )

    portfolio = load_portfolio()
    filters = render_filters(portfolio)
    filtered = apply_filters(portfolio, filters)

    if filtered.empty:
        st.warning("Aucun client ne correspond aux filtres sélectionnés.")
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
        st.markdown("**Alertes de gouvernance**")
        st.dataframe(build_alert_table(filtered), hide_index=True, use_container_width=True, height=400)

    st.divider()
    st.subheader("Concentrations")
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
    st.subheader("Dossiers prioritaires")
    st.dataframe(build_priority_table(filtered, top_n=10), hide_index=True, use_container_width=True, height=420)

    st.download_button(
        label="Exporter la vue filtrée (.csv)",
        data=dataframe_to_csv_bytes(filtered[[c for c in DISPLAY_COLUMNS if c in filtered.columns]]),
        file_name="tableau1_portefeuille_filtre.csv",
        mime="text/csv",
        type="primary",
    )

    with st.expander("Aperçu des données sous-jacentes filtrées"):
        preview_cols = [c for c in DISPLAY_COLUMNS if c in filtered.columns]
        st.dataframe(filtered[preview_cols], hide_index=True, use_container_width=True, height=420)


if __name__ == "__main__":
    main()
