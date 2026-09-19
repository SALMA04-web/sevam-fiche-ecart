import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import load_events, load_suivi_2025, setup_page
from src import config, db, kpi

setup_page("Accueil", icon="🏭")
db.init_db()

st.title("Suivi des arrêts de ligne — SEVAM")
st.markdown(
    "Outil de suivi et d'analyse des arrêts de production, construit à partir des "
    "**données réelles** transmises par le service Maintenance/Production : le journal "
    "détaillé des arrêts sur l'année **2024** (3 260 événements, 6 lignes) et le suivi "
    "quotidien agrégé de **janvier à septembre 2025**. Les nouvelles déclarations saisies "
    "dans cette application s'ajoutent à cette même base et restent enregistrées de façon "
    "permanente."
)

events = load_events()
suivi = load_suivi_2025()

date_min = pd.to_datetime(events["date"]).min()
date_max = pd.to_datetime(events["date"]).max()

fiab = kpi.calc_fiabilite(events, date_min, date_max, lignes=config.LIGNES)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Événements enregistrés", f"{len(events):,}".replace(",", " "))
c2.metric("Temps d'arrêt cumulé", f"{fiab.temps_arret_h:,.0f} h".replace(",", " "))
c3.metric("Disponibilité globale (6 lignes)", f"{fiab.disponibilite * 100:.2f} %")
c4.metric("Déclarations saisies dans l'app", f"{db.count_manual_declarations()}")

st.caption(
    f"Période couverte : {date_min.date().isoformat()} → {date_max.date().isoformat()} · "
    "6 lignes réelles : Four 1 (L11, L12, L13) et Four 2 (L21, L22, L23)."
)

st.divider()
st.subheader("Évolution mensuelle du temps d'arrêt cumulé")

evt_monthly = events.dropna(subset=["duree_min"]).copy()
evt_monthly["mois"] = pd.to_datetime(evt_monthly["date"]).dt.to_period("M").dt.to_timestamp()
monthly = evt_monthly.groupby("mois")["duree_min"].sum().reset_index()
monthly["heures"] = monthly["duree_min"] / 60

fig = go.Figure()
fig.add_trace(go.Bar(
    x=monthly["mois"], y=monthly["heures"],
    marker_color=config.COLOR["amber"],
    hovertemplate="%{x|%B %Y}<br>%{y:.0f} h d'arrêt<extra></extra>",
    name="Temps d'arrêt cumulé",
))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white", paper_bgcolor="white",
    yaxis_title="Heures d'arrêt / mois", xaxis_title=None,
    showlegend=False,
)
fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Pages disponibles")
st.markdown(
    "- **Nouvelle déclaration** — enregistrer un nouvel arrêt (ligne, équipement, durée).\n"
    "- **Historique** — rechercher/filtrer tous les événements enregistrés.\n"
    "- **Suivi quotidien 2025** — reprise du suivi journalier réel, comparé au seuil SEVAM.\n"
    "- **Analyse Pareto** — causes qui concentrent le plus de temps d'arrêt.\n"
    "- **Fiabilité** — MTBF, MTTR, disponibilité par ligne/four et par période.\n"
    "- **AMDEC** — grille de criticité des équipements (Fréquence x Gravité) et simulateur d'incident.\n"
    "- **Impact économique** — estimation du coût des arrêts (paramètre réglable).\n"
    "- **Qualité des données** — transparence totale sur les corrections appliquées aux données brutes."
)
