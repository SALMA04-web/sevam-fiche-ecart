import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import load_events, sidebar_filters, setup_page
from src import config, kpi

setup_page("AMDEC", icon="🧭")
st.title("Criticité des équipements (AMDEC) et simulateur d'incident")
st.info(
    "Grille à 2 facteurs (Fréquence x Gravité), calculée sur données réelles. Le 3ᵉ facteur "
    "AMDEC classique, la **Détection**, n'est pas encore mesurable chez SEVAM (aucun système "
    "de détection automatique des pannes) — c'est cohérent avec l'action 2 proposée dans le "
    "rapport PFA.",
    icon="ℹ️",
)

events = load_events()
date_from, date_to, lignes = sidebar_filters(events, key_prefix="amdec")

table = kpi.amdec_table(events, date_from, date_to, lignes, group_col="equipement")
if table.empty:
    st.warning("Aucun événement exploitable sur cette période/périmètre.")
    st.stop()

top = table.head(15).reset_index(drop=True)
# Sur des données réelles, les équipements les plus critiques ont souvent des fréquences
# et gravités très proches : des étiquettes systématiques se chevauchent et deviennent
# illisibles. On s'appuie donc sur le survol (nom + valeurs) et sur la table détaillée
# ci-dessous plutôt que sur des étiquettes fixes sur le graphique.
fig = go.Figure(go.Scatter(
    x=top["frequence"], y=top["gravite_moyenne_min"], mode="markers",
    customdata=top["equipement"],
    marker=dict(
        size=(top["duree_totale_min"] / top["duree_totale_min"].max() * 40 + 10),
        color=top["criticite"], colorscale=[[0, config.COLOR["amber_pale"]], [1, config.COLOR["amber_deep"]]],
        showscale=True, colorbar=dict(title="Criticité"),
        line=dict(color=config.COLOR["white"], width=1),
    ),
    hovertemplate="%{customdata}<br>Fréquence : %{x} pannes<br>Gravité moyenne : %{y:.0f} min<extra></extra>",
))
fig.update_layout(
    height=460, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white",
    xaxis_title="Fréquence (nombre de pannes)", yaxis_title="Gravité moyenne (min/panne)",
)
fig.update_xaxes(gridcolor=config.COLOR["steel_light"])
fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig, width='stretch')
st.caption("Survolez un point pour voir le nom de l'équipement — le détail complet est aussi dans la table ci-dessous.")

st.subheader("Top équipements les plus critiques")
st.dataframe(
    table.head(20).rename(columns={
        "equipement": "Équipement", "frequence": "Fréquence", "gravite_moyenne_min": "Gravité moy. (min)",
        "duree_totale_min": "Durée totale (min)", "rang_f": "Rang F (1-5)", "rang_g": "Rang G (1-5)",
        "criticite": "Criticité",
    }),
    width='stretch', hide_index=True,
)

st.divider()
st.subheader("Simulateur d'incident")
st.markdown("Estimer l'impact d'une panne hypothétique sur la fiabilité de la période sélectionnée.")

col1, col2 = st.columns(2)
with col1:
    ligne_sim = st.selectbox("Ligne concernée", lignes if lignes else config.LIGNES)
with col2:
    duree_sim = st.slider("Durée hypothétique (minutes)", 5, 480, 60, step=5)

if st.button("Simuler l'impact", type="primary"):
    avant, apres = kpi.simuler_incident(events, date_from, date_to, lignes, duree_sim)
    c1, c2, c3 = st.columns(3)
    c1.metric("MTBF", f"{apres.mtbf_h:.1f} h", delta=f"{apres.mtbf_h - avant.mtbf_h:.1f} h")
    c2.metric("MTTR", f"{apres.mttr_h:.2f} h", delta=f"{apres.mttr_h - avant.mttr_h:.2f} h")
    c3.metric("Disponibilité", f"{apres.disponibilite * 100:.2f} %",
              delta=f"{(apres.disponibilite - avant.disponibilite) * 100:.3f} pt")
    st.caption(
        f"Simulation : +1 panne de {duree_sim} min sur {ligne_sim}, période {date_from.date()} → {date_to.date()}."
    )
