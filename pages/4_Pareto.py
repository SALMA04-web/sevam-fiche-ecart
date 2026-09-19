import plotly.graph_objects as go
import streamlit as st

from common import load_events, sidebar_filters, setup_page
from src import config, kpi

setup_page("Analyse Pareto", icon="📊")
st.title("Analyse Pareto des causes d'arrêt")
st.markdown(
    "SEVAM ne dispose pas encore de codes cause standardisés (FOUR / APPRO / SÉRIE / QUALITÉ...) : "
    "c'est justement l'action proposée dans le rapport PFA. En attendant, cette analyse s'appuie "
    "sur la donnée réelle déjà disponible : la **famille d'équipement** ou l'**équipement précis** "
    "à l'origine de chaque arrêt."
)

events = load_events()
date_from, date_to, lignes = sidebar_filters(events, key_prefix="pareto")

niveau = st.radio("Niveau d'analyse", ["Famille d'équipement", "Équipement précis"], horizontal=True)
group_col = "famille" if niveau == "Famille d'équipement" else "equipement"
top_n = st.slider("Nombre de catégories affichées", 5, 30, 12)

table = kpi.pareto_table(events, date_from, date_to, lignes, group_col=group_col)

if table.empty:
    st.warning("Aucun événement avec durée exploitable sur cette période/périmètre.")
    st.stop()

display = table.head(top_n)
n_colors = len(config.AMBER_SEQUENTIAL)
colors = [config.AMBER_SEQUENTIAL[min(i * n_colors // len(display), n_colors - 1)] for i in range(len(display))]

c1, c2 = st.columns(2)
c1.metric("Catégories distinctes", len(table))
c2.metric(f"Temps d'arrêt cumulé (top {top_n})", f"{display['duree_totale_min'].sum() / 60:.1f} h")

st.subheader("Temps d'arrêt cumulé par catégorie")
fig1 = go.Figure(go.Bar(
    x=display["duree_totale_min"] / 60, y=display[group_col], orientation="h",
    marker_color=colors,
    hovertemplate="%{y}<br>%{x:.1f} h — %{customdata} pannes<extra></extra>",
    customdata=display["nb_pannes"],
))
fig1.update_layout(
    height=max(320, 28 * len(display)), margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white", paper_bgcolor="white", xaxis_title="Heures d'arrêt cumulées",
    yaxis=dict(autorange="reversed"),
)
fig1.update_xaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig1, width='stretch')

st.subheader("Pourcentage cumulé (règle des 80/20)")
fig2 = go.Figure(go.Scatter(
    x=display[group_col], y=display["pct_cumule"], mode="lines+markers",
    line=dict(color=config.COLOR["anthracite"], width=2), marker=dict(size=7),
    hovertemplate="%{x}<br>%{y:.1f} %% cumulé<extra></extra>",
))
fig2.add_hline(y=80, line_dash="dash", line_color=config.COLOR["red"],
               annotation_text="80 %", annotation_position="bottom right")
fig2.update_layout(
    height=300, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white",
    yaxis_title="% cumulé du temps d'arrêt", yaxis_range=[0, 105],
)
fig2.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig2, width='stretch')

n_80 = (table["pct_cumule"] <= 80).sum() + 1
st.info(
    f"**{min(n_80, len(table))} catégorie(s)** sur {len(table)} concentrent à elles seules "
    f"80 % du temps d'arrêt observé sur cette période et ce périmètre.",
    icon="🎯",
)

with st.expander("Voir la table complète"):
    st.dataframe(table, width='stretch', hide_index=True)
