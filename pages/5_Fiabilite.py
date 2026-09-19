import plotly.graph_objects as go
import streamlit as st

from common import load_events, sidebar_filters, setup_page
from src import config, kpi

setup_page("Fiabilité", icon="💓")
st.title("Fiabilité : MTBF, MTTR, disponibilité")

events = load_events()
date_from, date_to, lignes = sidebar_filters(events, key_prefix="fiab")

fiab = kpi.calc_fiabilite(events, date_from, date_to, lignes)

st.markdown(
    f"Période : **{date_from.date()} → {date_to.date()}** ({fiab.nb_jours} jours) · "
    f"Lignes considérées : **{', '.join(lignes)}** · "
    f"Heures d'ouverture totales : **{fiab.heures_ouverture:,.0f} h**".replace(",", " ")
)

c1, c2, c3 = st.columns(3)
c1.metric("MTBF — temps moyen entre pannes", f"{fiab.mtbf_h:.1f} h" if fiab.mtbf_h else "—")
c2.metric("MTTR — temps moyen de réparation", f"{fiab.mttr_h:.2f} h" if fiab.mttr_h else "—")
c3.metric("Disponibilité", f"{fiab.disponibilite * 100:.2f} %" if fiab.disponibilite is not None else "—")

st.caption(
    f"{fiab.nb_pannes} panne(s) observée(s) sur la période, "
    f"{fiab.temps_arret_h:.1f} h d'arrêt cumulé, "
    f"{fiab.temps_fonctionnement_h:,.0f} h de fonctionnement effectif.".replace(",", " ")
)

with st.expander("Méthode de calcul"):
    st.markdown(
        "- **Heures d'ouverture** = nombre de jours x 24 h x nombre de lignes (fonctionnement continu).\n"
        "- **MTBF** = (heures d'ouverture − temps d'arrêt cumulé) / nombre de pannes.\n"
        "- **MTTR** = temps d'arrêt cumulé / nombre de pannes.\n"
        "- **Disponibilité** = temps de fonctionnement / heures d'ouverture = MTBF / (MTBF + MTTR).\n\n"
        "Méthode identique à celle déjà présentée en soutenance (étude de cas Four U2)."
    )

st.divider()
st.subheader("Comparaison entre les 6 lignes sur la même période")

rows = []
for ligne in config.LIGNES:
    f = kpi.calc_fiabilite(events, date_from, date_to, [ligne])
    rows.append({"ligne": ligne, "mtbf_h": f.mtbf_h, "mttr_h": f.mttr_h,
                 "disponibilite": f.disponibilite * 100 if f.disponibilite is not None else None,
                 "nb_pannes": f.nb_pannes})
import pandas as pd  # noqa: E402
comp = pd.DataFrame(rows)

fig = go.Figure(go.Bar(
    x=comp["ligne"], y=comp["disponibilite"],
    marker_color=[config.LIGNE_COLOR[l] for l in comp["ligne"]],
    hovertemplate="%{x}<br>Disponibilité : %{y:.2f} %%<extra></extra>",
))
fig.update_layout(
    height=340, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", paper_bgcolor="white",
    yaxis_title="Disponibilité (%)", yaxis_range=[0, 100],
)
fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig, width='stretch')

st.dataframe(
    comp.rename(columns={"ligne": "Ligne", "mtbf_h": "MTBF (h)", "mttr_h": "MTTR (h)",
                          "disponibilite": "Disponibilité (%)", "nb_pannes": "Nb pannes"}),
    width='stretch', hide_index=True,
)
