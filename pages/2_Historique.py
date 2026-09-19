import streamlit as st

from common import load_events, sidebar_filters, setup_page

setup_page("Historique", icon="📜")
st.title("Historique des arrêts")

events = load_events()
date_from, date_to, lignes = sidebar_filters(events, key_prefix="hist")

recherche = st.text_input("Rechercher dans la description du problème", "")

mask = (
    (events["date"] >= date_from) & (events["date"] <= date_to) & (events["ligne"].isin(lignes))
)
sub = events[mask].copy()
if recherche:
    sub = sub[sub["probleme"].fillna("").str.contains(recherche, case=False, na=False)]

sub = sub.sort_values("date", ascending=False)

c1, c2, c3 = st.columns(3)
c1.metric("Événements trouvés", len(sub))
c2.metric("Temps d'arrêt cumulé", f"{sub['duree_min'].fillna(0).sum() / 60:.1f} h")
c3.metric("Durée moyenne / événement", f"{sub['duree_min'].mean():.0f} min" if len(sub) else "—")

st.dataframe(
    sub[["date", "ligne", "four", "equipement", "famille", "probleme", "duree_min", "source"]],
    width='stretch', hide_index=True, height=520,
)

st.download_button(
    "Télécharger cette sélection (CSV)",
    data=sub.to_csv(index=False).encode("utf-8"),
    file_name="historique_arrets_sevam.csv",
    mime="text/csv",
)
