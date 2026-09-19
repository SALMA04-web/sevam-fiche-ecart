import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (
    load_budget_commercial, load_catalogue, load_commandes_clients, load_events,
    load_rendement_of, load_stock, load_suivi_2025, load_suivi_commandes, setup_page,
)
from src import config, db, kpi

setup_page("Accueil", icon="🏭")
db.init_db()

user = st.session_state.get("_sevam_user")

st.title("SEVAM — Outil de pilotage")
st.markdown(
    "Application unique regroupant, sur des **données réelles** transmises par "
    "l'encadrant : le suivi des arrêts de ligne (2024-2025), le rendement de "
    "production (2012-2024), le catalogue produits, le suivi commercial "
    "(commandes clients et prospection 2025-2026) et le stock/planification "
    "Gobeleterie 2026. Un rôle (Opérateur, Chef de service, Chef de département, "
    "Direction Générale) donne accès aux modules pertinents — voir le menu de "
    "gauche."
)

events = load_events()
suivi = load_suivi_2025()
of = load_rendement_of()
catalogue = load_catalogue()
commandes = load_commandes_clients()
suivi_com = load_suivi_commandes()
stock = load_stock()
budget = load_budget_commercial()

date_min = pd.to_datetime(events["date"]).min()
date_max = pd.to_datetime(events["date"]).max()
fiab = kpi.calc_fiabilite(events, date_min, date_max, lignes=config.LIGNES)

st.subheader("🏭 Production — arrêts de ligne (2024-2025)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Événements enregistrés", f"{len(events):,}".replace(",", " "))
c2.metric("Temps d'arrêt cumulé", f"{fiab.temps_arret_h:,.0f} h".replace(",", " "))
c3.metric("Disponibilité globale (6 lignes)", f"{fiab.disponibilite * 100:.2f} %")
c4.metric("Déclarations saisies dans l'app", f"{db.count_manual_declarations()}")

st.subheader("📉 Rendement de production (2012-2024)")
if not of.empty:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ordres de fabrication réels", f"{len(of):,}".replace(",", " "))
    c2.metric("Rendement réel moyen (RDT)", f"{of['rdt_pct'].mean():.1f} %")
    c3.metric("Écart moyen RDT − PTM", f"{of['ecart_rdt_pct'].mean():+.1f} pt")
    c4.metric("Articles distincts produits", of["article"].nunique())
else:
    st.info("Module rendement non disponible — lancer `python3 src/etl_erp.py`.")

st.subheader("💼 Commercial (2026)")
if not suivi_com.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Clients suivis", f"{len(suivi_com):,}".replace(",", " "))
    c2.metric("Valeur des BC reçus", f"{suivi_com['valeur_bc_recus'].sum():,.0f} DH".replace(",", " "))
    taux = suivi_com["taux_realisation"].dropna()
    c3.metric("Taux de réalisation moyen", f"{taux.mean() * 100:.1f} %" if len(taux) else "n/d")
else:
    st.info("Module commercial non disponible — lancer `python3 src/etl_erp.py`.")

st.subheader("🗃️ Stock & catalogue")
if not stock.empty or not catalogue.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Articles au catalogue", f"{len(catalogue):,}".replace(",", " ") if not catalogue.empty else "n/d")
    c2.metric("Références en stock (Gobeleterie)", stock["article"].nunique() if not stock.empty else 0)
    c3.metric("Quantité totale en stock", f"{stock['stock_qte'].sum():,.0f}".replace(",", " ") if not stock.empty else "n/d")
else:
    st.info("Module stock non disponible — lancer `python3 src/etl_erp.py`.")

st.divider()
st.subheader("Évolution mensuelle du temps d'arrêt cumulé (arrêts de ligne)")
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
    height=360, margin=dict(l=10, r=10, t=10, b=10),
    plot_bgcolor="white", paper_bgcolor="white",
    yaxis_title="Heures d'arrêt / mois", xaxis_title=None,
    showlegend=False,
)
fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Modules disponibles (selon votre rôle)")
st.markdown(
    "**Production**\n"
    "- **Nouvelle déclaration** — enregistrer un nouvel arrêt (ligne, équipement, durée).\n"
    "- **Historique** — rechercher/filtrer tous les événements enregistrés.\n"
    "- **Suivi quotidien 2025** — reprise du suivi journalier réel, comparé au seuil SEVAM.\n"
    "- **Analyse Pareto** — causes qui concentrent le plus de temps d'arrêt.\n"
    "- **Fiabilité** — MTBF, MTTR, disponibilité par ligne/four et par période.\n"
    "- **AMDEC** — grille de criticité des équipements et simulateur d'incident.\n"
    "- **Rendement & écarts** — écarts RDT/PTM réels par ordre de fabrication (2012-2024).\n"
    "- **Catalogue produits** — référentiel articles réel (poids, usine, ligne).\n\n"
    "**Commercial & stock**\n"
    "- **Suivi commercial** — commandes clients 2026 et prospection (noms réels).\n"
    "- **Stock & planification** — stock Gobeleterie, budget commercial, ventes mensuelles.\n\n"
    "**Pilotage**\n"
    "- **Impact économique** — estimation du coût des arrêts (paramètre réglable).\n"
    "- **Qualité des données** — transparence totale sur toutes les sources et leurs limites.\n"
    "- **Connexion** — changer de rôle, voir qui est connecté actuellement."
)
