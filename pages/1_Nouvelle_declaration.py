import pandas as pd
import streamlit as st

from common import load_events, setup_page
from src import config, db

setup_page("Nouvelle déclaration", icon="📝")
st.title("Déclarer un arrêt")
st.markdown(
    "Cette déclaration est **enregistrée de façon permanente** (base locale `data/sevam.db`) : "
    "elle reste disponible après un redémarrage de l'application, et alimente immédiatement "
    "les pages Historique, Pareto, Fiabilité et AMDEC."
)

events = load_events()
equipements_connus = sorted(events["equipement"].dropna().unique().tolist())
familles_connues = sorted(events["famille"].dropna().unique().tolist())

with st.form("form_declaration", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        ligne = st.selectbox("Ligne", config.LIGNES)
        date = st.date_input("Date de l'arrêt", value=pd.Timestamp.today().date())
        duree_min = st.number_input("Durée d'arrêt (minutes)", min_value=1, max_value=2000, value=15, step=1)
    with col2:
        famille_choice = st.selectbox("Famille / section", familles_connues + ["Autre (préciser)"])
        famille = st.text_input("Préciser la famille") if famille_choice == "Autre (préciser)" else famille_choice
        equipement_choice = st.selectbox("Équipement", equipements_connus + ["Autre (préciser)"])
        equipement = st.text_input("Préciser l'équipement") if equipement_choice == "Autre (préciser)" else equipement_choice
        saisi_par = st.text_input("Déclaré par", value="")

    probleme = st.text_area("Description du problème", placeholder="Ex. : Changement bras de transfert, section n°4")
    submitted = st.form_submit_button("Enregistrer la déclaration", type="primary")

    if submitted:
        if not equipement or not famille:
            st.error("Merci de préciser au moins l'équipement et la famille concernés.")
        else:
            new_id = db.insert_evenement(
                date=date, ligne=ligne, probleme=probleme or None, equipement=equipement,
                famille=famille, duree_min=duree_min, saisi_par=saisi_par or "—",
            )
            load_events(force_refresh=True)
            st.success(f"Déclaration n°{new_id} enregistrée pour {ligne} le {date.isoformat()}.")

st.divider()
st.subheader("Dernières déclarations saisies manuellement")
manuelles = load_events()
manuelles = manuelles[manuelles["source"] == "manuel"].sort_values("created_at", ascending=False)
if manuelles.empty:
    st.caption("Aucune déclaration manuelle pour l'instant — la première apparaîtra ici.")
else:
    st.dataframe(
        manuelles[["date", "ligne", "four", "equipement", "famille", "probleme", "duree_min", "saisi_par"]].head(20),
        width='stretch', hide_index=True,
    )
