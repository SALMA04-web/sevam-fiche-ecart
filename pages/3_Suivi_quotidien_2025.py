import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import load_suivi_2025, setup_page
from src import config

setup_page("Suivi quotidien 2025", icon="📅")
st.title("Suivi quotidien 2025")
st.markdown(
    "Reprise du suivi journalier réel tenu par le service Production (janvier à septembre 2025), "
    f"comparé au seuil de référence déjà utilisé par SEVAM : "
    f"**{config.SEUIL_ARRET_2024_MIN_PAR_JOUR} minutes d'arrêt par jour et par ligne**."
)

suivi = load_suivi_2025()

st.sidebar.header("Filtres")
lignes = st.sidebar.multiselect("Lignes", config.LIGNES, default=config.LIGNES)
sub = suivi[suivi["ligne"].isin(lignes)]

st.subheader("Évolution quotidienne par ligne")
fig = go.Figure()
for ligne in lignes:
    d = sub[sub["ligne"] == ligne].sort_values("date")
    fig.add_trace(go.Scatter(
        x=d["date"], y=d["minutes_arret"], mode="lines", name=ligne,
        line=dict(color=config.LIGNE_COLOR.get(ligne), width=2),
        hovertemplate="%{x|%d %b %Y}<br>" + ligne + " : %{y:.0f} min<extra></extra>",
    ))
fig.add_hline(y=config.SEUIL_ARRET_2024_MIN_PAR_JOUR, line_dash="dash", line_color=config.COLOR["red"])
fig.update_layout(
    height=420, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white", paper_bgcolor="white",
    yaxis_title="Minutes d'arrêt / jour", legend_title=None,
)
fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig, width='stretch')
st.caption(
    "La ligne rouge pointillée marque le seuil de référence (18 min/jour et par ligne). Les "
    "pics ponctuels dépassent largement l'échelle du seuil — le graphique suivant (total "
    "mensuel) donne une lecture plus stable de la tendance."
)

st.subheader("Total mensuel par ligne")
monthly = sub.copy()
monthly["mois"] = pd.to_datetime(monthly["date"]).dt.to_period("M").dt.to_timestamp()
monthly = monthly.groupby(["mois", "ligne"])["minutes_arret"].sum().reset_index()

fig2 = go.Figure()
for ligne in lignes:
    d = monthly[monthly["ligne"] == ligne]
    fig2.add_trace(go.Bar(
        x=d["mois"], y=d["minutes_arret"] / 60, name=ligne,
        marker_color=config.LIGNE_COLOR.get(ligne),
        hovertemplate="%{x|%B %Y}<br>" + ligne + " : %{y:.1f} h<extra></extra>",
    ))
fig2.update_layout(
    barmode="group", height=380, margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white", paper_bgcolor="white", yaxis_title="Heures d'arrêt / mois",
)
fig2.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig2, width='stretch')

with st.expander("Voir les données détaillées"):
    st.dataframe(sub.sort_values("date", ascending=False), width='stretch', hide_index=True)

st.info(
    "Ce suivi quotidien est une source distincte du journal détaillé des arrêts (2024) : "
    "il ne détaille ni l'équipement ni la cause, seulement le total de minutes d'arrêt par "
    "ligne et par jour. Voir la page **Qualité des données** pour le détail de cet écart de "
    "périmètre entre les deux sources.",
    icon="ℹ️",
)
