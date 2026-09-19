import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import load_events, sidebar_filters, setup_page
from src import config, kpi

setup_page("Impact économique", icon="💶")
st.title("Impact économique estimé des arrêts")
st.warning(
    "Le coût par minute d'arrêt n'est **pas une donnée SEVAM validée** — aucun des deux fichiers "
    "transmis ne contient de coût. La valeur ci-dessous est un curseur libre, à ajuster avec les "
    "vrais chiffres du service financier / production pour obtenir une estimation fiable. Tant "
    "qu'elle n'est pas confirmée, ne considérez ce chiffre que comme un ordre de grandeur illustratif.",
    icon="⚠️",
)

events = load_events()
date_from, date_to, lignes = sidebar_filters(events, key_prefix="eco")

col1, col2 = st.columns(2)
with col1:
    devise = st.text_input("Unité monétaire", value="MAD")
with col2:
    cout_par_minute = st.number_input(
        f"Coût estimé par minute d'arrêt ({devise})", min_value=0.0, value=10.0, step=1.0,
    )

resultat = kpi.cout_arrets(events, date_from, date_to, lignes, cout_par_minute)

c1, c2, c3 = st.columns(3)
c1.metric("Temps d'arrêt cumulé", f"{resultat['total_heures']:,.1f} h".replace(",", " "))
c2.metric("Minutes d'arrêt cumulées", f"{resultat['total_minutes']:,.0f} min".replace(",", " "))
c3.metric("Coût estimé", f"{resultat['cout_estime']:,.0f} {devise}".replace(",", " "))

st.divider()
st.subheader("Répartition du coût estimé par ligne")

rows = []
for ligne in lignes:
    r = kpi.cout_arrets(events, date_from, date_to, [ligne], cout_par_minute)
    rows.append({"ligne": ligne, "cout_estime": r["cout_estime"], "total_heures": r["total_heures"]})
comp = pd.DataFrame(rows).sort_values("cout_estime", ascending=False)

fig = go.Figure(go.Bar(
    x=comp["ligne"], y=comp["cout_estime"],
    marker_color=[config.LIGNE_COLOR.get(l) for l in comp["ligne"]],
    hovertemplate="%{x}<br>%{y:,.0f} " + devise + "<extra></extra>",
))
fig.update_layout(
    height=360, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white",
    yaxis_title=f"Coût estimé ({devise})",
)
fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig, width='stretch')

st.divider()
st.subheader("Simulateur de gain")
st.markdown(
    "Si une action corrective (les 3 actions proposées dans le rapport PFA : codes cause "
    "standardisés, capteurs de détection, maintenance préventive ciblée sur les équipements "
    "les plus critiques) permettait de réduire le temps d'arrêt, quel serait le gain estimé ?"
)
reduction_pct = st.slider("Réduction hypothétique du temps d'arrêt (%)", 0, 100, 20, step=5)
gain = resultat["cout_estime"] * reduction_pct / 100
gain_h = resultat["total_heures"] * reduction_pct / 100
c1, c2 = st.columns(2)
c1.metric(f"Temps d'arrêt évité (-{reduction_pct} %)", f"{gain_h:,.1f} h".replace(",", " "))
c2.metric(f"Gain estimé (-{reduction_pct} %)", f"{gain:,.0f} {devise}".replace(",", " "))
