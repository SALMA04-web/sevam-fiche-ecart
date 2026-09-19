import plotly.graph_objects as go
import streamlit as st

from common import load_quality_report, load_comparaison_sources, setup_page
from src import config

setup_page("Qualité des données", icon="🔍")
st.title("Qualité des données et limites méthodologiques")
st.markdown(
    "Cette page documente, en toute transparence, ce qui a été corrigé dans les fichiers "
    "sources et les limites connues des analyses de cette application — pour que les résultats "
    "restent vérifiables et que SEVAM puisse juger elle-même de leur fiabilité."
)

st.header("1. Corrections appliquées lors du nettoyage (ETL)")
st.markdown(
    "Le journal détaillé des arrêts (`Arret_2024.xlsx`) contient quelques erreurs de saisie "
    "typiques d'une saisie manuelle répétée toute l'année. Chacune a été corrigée automatiquement "
    "et journalisée ci-dessous — **aucune valeur n'a été modifiée silencieusement**."
)
quality = load_quality_report()
if quality.empty:
    st.warning("Rapport de qualité introuvable — relancer `python3 src/etl.py`.")
else:
    st.dataframe(
        quality.rename(columns={
            "fichier": "Fichier", "feuille": "Feuille", "champ": "Champ",
            "ligne_excel_index": "Ligne Excel", "valeur_originale": "Valeur d'origine",
            "valeur_corrigee": "Valeur corrigée", "motif": "Motif",
        }),
        width='stretch', hide_index=True,
    )
    st.caption(f"{len(quality)} corrections/exclusions au total sur 3 260 événements — soit moins de 0,3 %.")

st.divider()
st.header("2. Écart entre les deux fichiers sources sur 2024")
st.markdown(
    "Les deux fichiers transmis ne couvrent pas exactement le même périmètre, et leurs totaux "
    "**ne coïncident pas** : le fichier `Suivi_arrets_2025.xlsx` intègre, pour comparaison "
    "mensuelle, une colonne *« Total des arrêts 2024 (min) »* par ligne — une valeur bien plus "
    "faible que le total obtenu en additionnant chaque événement du journal détaillé "
    "`Arret_2024.xlsx` sur la même période (Janvier-Septembre)."
)

comp = load_comparaison_sources()
if comp.empty:
    st.warning("Table de comparaison introuvable — relancer `python3 src/etl.py`.")
else:
    total_journal = comp["journal_detaille_2024_min"].sum()
    total_ref = comp["suivi_ref_2024_min"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Journal détaillé (Jan-Sept 2024)", f"{total_journal:,.0f} min".replace(",", " "))
    c2.metric("Référence du suivi 2025 (Jan-Sept 2024)", f"{total_ref:,.0f} min".replace(",", " "))
    c3.metric("Écart", f"x{total_journal / total_ref:.1f}")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=comp["ligne"], y=comp["journal_detaille_2024_min"], name="Journal détaillé (Arret_2024.xlsx)",
        marker_color=config.COLOR["anthracite"],
        hovertemplate="%{x}<br>Journal détaillé : %{y:,.0f} min<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=comp["ligne"], y=comp["suivi_ref_2024_min"], name="Référence suivi 2025 (Suivi_arrets_2025.xlsx)",
        marker_color=config.COLOR["amber"],
        hovertemplate="%{x}<br>Référence suivi : %{y:,.0f} min<extra></extra>",
    ))
    fig.update_layout(
        barmode="group", height=380, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white", paper_bgcolor="white", yaxis_title="Minutes d'arrêt, Jan-Sept 2024",
    )
    fig.update_yaxes(gridcolor=config.COLOR["steel_light"])
    st.plotly_chart(fig, width='stretch')

    st.subheader("Table détaillée, avec le test de l'hypothèse « arrêts de section »")
    st.markdown(
        "Une hypothèse naturelle a été testée : le journal détaillé compte séparément chaque "
        "section d'une machine IS (Individual Section) qui s'arrête (`Section n°1` à "
        "`Section n°10`), alors qu'un arrêt de section isolée ne stoppe pas forcément toute la "
        "ligne — peut-être que le suivi de production ne compte, lui, que les arrêts au niveau "
        "de la ligne entière (hors panne d'une section précise). En excluant les événements de "
        "type « Section n°X », l'écart se réduit fortement pour **L12** (rapport proche de 1) "
        "mais reste très marqué et **dans les deux sens** pour les autres lignes — trop nettes "
        "pour un même mécanisme, trop irrégulier pour être le seul facteur :"
    )
    display_comp = comp.copy()
    display_comp["ratio_hors_section"] = display_comp["journal_hors_section_min"] / display_comp["suivi_ref_2024_min"]
    st.dataframe(
        display_comp.rename(columns={
            "ligne": "Ligne", "journal_detaille_2024_min": "Journal détaillé (min)",
            "journal_hors_section_min": "…dont hors « Section n°X » (min)",
            "journal_section_min": "…dont « Section n°X » (min)",
            "suivi_ref_2024_min": "Référence suivi 2025 (min)",
            "ecart_ratio": "Écart (total / référence)",
            "ratio_hors_section": "Écart (hors section / référence)",
        }).style.format({
            "Journal détaillé (min)": "{:,.0f}", "…dont hors « Section n°X » (min)": "{:,.0f}",
            "…dont « Section n°X » (min)": "{:,.0f}", "Référence suivi 2025 (min)": "{:,.0f}",
            "Écart (total / référence)": "x{:.2f}", "Écart (hors section / référence)": "x{:.2f}",
        }),
        width='stretch', hide_index=True,
    )

    st.info(
        "**Interprétation la plus probable, après analyse approfondie des deux fichiers :** "
        "il s'agit très vraisemblablement de **deux pratiques de suivi indépendantes**, tenues "
        "par deux équipes différentes, avec des critères de saisie différents — un journal "
        "technique détaillé (probablement maintenance), qui enregistre chaque arrêt constaté "
        "quel qu'en soit la durée ou la portée, et un suivi de production plus synthétique, qui "
        "ne remonte au niveau ligne/jour qu'une partie de ces arrêts (par exemple à partir d'un "
        "certain seuil de durée, ou seulement les arrêts jugés significatifs par l'équipe de "
        "production ce jour-là). L'écart n'étant ni un facteur constant ni explicable par la "
        "seule hypothèse « section vs ligne », **cette explication reste la plus logique mais "
        "n'est pas confirmée** : elle est présentée comme une hypothèse de travail, pas comme un "
        "fait établi. Nous recommandons de la vérifier directement auprès des équipes "
        "maintenance et production de SEVAM — cette clarification serait d'ailleurs une "
        "première étape utile vers les codes cause standardisés proposés dans le rapport PFA.",
        icon="🧭",
    )
    st.caption(
        "Conséquence pratique pour la lecture de cette application : les pages Fiabilité, "
        "Pareto et AMDEC s'appuient sur le **journal détaillé** (le plus complet et le seul "
        "exploitable événement par événement), tandis que la page Suivi quotidien 2025 "
        "présente la donnée de production telle quelle, sans les recouper — c'est la source la "
        "plus adaptée à chaque usage, mais elles ne sont pas directement comparables."
    )

st.divider()
st.header("3. Autres limites méthodologiques assumées")
st.markdown(
    "- **Pareto sans codes cause standardisés** : SEVAM ne dispose pas encore de codes cause "
    "unifiés (type FOUR / APPRO / SÉRIE / QUALITÉ). L'analyse Pareto de cette application "
    "s'appuie donc sur la famille/l'équipement réellement renseigné dans le journal, qui reste "
    "une donnée fiable mais plus fine et moins directement actionnable qu'une vraie "
    "classification de causes — d'où l'action 1 proposée dans le rapport PFA.\n"
    "- **AMDEC à 2 facteurs, pas 3** : la grille de criticité combine Fréquence x Gravité "
    "moyenne. Le 3ᵉ facteur classique, la Détection, ne peut pas être calculé aujourd'hui : "
    "aucune détection automatique des pannes n'existe chez SEVAM (action 2 proposée dans le "
    "rapport PFA).\n"
    "- **Heures d'ouverture = fonctionnement continu supposé** : MTBF/MTTR/disponibilité "
    "supposent un fonctionnement 24h/24 (nb_jours x 24h x nb_lignes). Si certaines lignes "
    "s'arrêtent volontairement en dehors de pannes (arrêt planifié, maintenance préventive, "
    "absence de commande), ce temps n'est pas distingué d'un temps de fonctionnement effectif — "
    "c'est la même convention que celle déjà validée lors de la soutenance PFA (cas Four U2).\n"
    "- **113 catégories de famille et 143 d'équipement, après normalisation** de plus de "
    "variantes brutes (casse, espaces, fautes de frappe) en étiquettes uniques — un même "
    "équipement mal orthographié de deux façons différentes est bien compté comme un seul.\n"
    "- **3 258 événements sur 3 260 ont une durée exploitable** (2 événements ont une durée "
    "manquante dans le fichier source d'origine : ils sont conservés dans l'historique mais "
    "exclus des totaux de temps d'arrêt)."
)
