"""
Prototype — Fiche de déclaration d'écart numérique (SEVAM)
===========================================================
Preuve de concept d'une saisie numérique de la fiche de déclaration
d'écart (chapitre 5 du rapport PFA) qui alimenterait automatiquement
un pilotage type Qlik Sense / Power BI, en remplacement de la saisie
papier actuelle.

Version 2 — enrichie de :
  - un pilotage structuré selon les 3 critères Qualité / Coût / Délai (QCD),
  - un onglet Impact économique avec simulation de gain,
  - des notes explicatives intégrées à chaque écran,
  - un onglet Méthodologie & note technique pour le jury.

Lancement local : streamlit run app.py
Auteur : SALMA — PFA SEVAM 2026
"""

import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Fiche de déclaration d'écart — SEVAM",
    page_icon="🏭",
    layout="wide",
)

NAVY = "#1F3864"
BLUE = "#2E5395"
RED = "#C0392B"
GREEN = "#1E7145"
AMBER = "#B8860B"

CSV_PATH = os.path.join(os.path.dirname(__file__), "Dataset_Ecarts_Production_SEVAM.csv")

CAUSES = {
    "FOUR": "Arrêt four non planifié",
    "APPRO": "Retard livraison matière première",
    "SERIE": "Changement de série non anticipé",
    "QUALITE": "Rebuts / non-conformités",
    "AUTRE": "Cause diverse",
}
LIGNES = [
    ("Ligne 11", "Four 1"), ("Ligne 12", "Four 1"), ("Ligne 13", "Four 2"),
    ("Ligne 14", "Four 2"), ("Ligne 15", "Four 3"),
]


@st.cache_data
def load_base_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8-sig")
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    return pd.DataFrame(columns=[
        "N_OF", "Date", "Ligne", "Four", "Reference_Article", "Qte_Planifiee",
        "Qte_Realisee", "Ecart_Unites", "Ecart_Pct", "Code_Cause", "Libelle_Cause", "Statut",
    ])


if "declarations" not in st.session_state:
    st.session_state.declarations = load_base_data().copy()

# =========================================================
# SIDEBAR — identité, paramètres de pilotage, à propos
# =========================================================
with st.sidebar:
    st.markdown(
        f"<div style='background:{NAVY};padding:14px;border-radius:6px;'>"
        f"<h3 style='color:white;margin:0;'>🏭 SEVAM</h3>"
        f"<p style='color:#D9E2F3;margin:4px 0 0 0;font-size:12.5px;'>Pilotage numérique des écarts de production</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown("**Paramètres de pilotage**")
    seuil_alerte = st.slider(
        "Seuil d'alerte écart (%)", min_value=1, max_value=20, value=5,
        help="Au-delà de ce pourcentage d'écart, un OF est classé « À traiter ». Paramétrable pour s'adapter à la tolérance retenue par SEVAM.",
    )
    cout_unitaire = st.number_input(
        "Coût moyen estimé par unité non produite (MAD)", min_value=0.0, value=8.0, step=0.5,
        help="Valeur à ajuster avec le contrôle de gestion SEVAM — utilisée uniquement pour illustrer l'ordre de grandeur financier des écarts dans l'onglet Impact économique.",
    )
    st.caption("Ces deux paramètres recalculent en direct tous les indicateurs de l'application.")

    st.write("")
    st.markdown("**Résumé rapide**")
    _df_all = st.session_state.declarations
    if not _df_all.empty:
        st.metric("OF suivis", int(_df_all["N_OF"].nunique()))
        st.metric("Taux de service", f"{(_df_all['Qte_Realisee'].sum()/_df_all['Qte_Planifiee'].sum()*100):.1f}%")

    st.write("")
    with st.expander("ℹ️ À propos de ce prototype"):
        st.caption(
            "Développé en Python (Streamlit, Pandas, Plotly) dans le cadre du PFA "
            "« Diagnostic des écarts de production — SEVAM ». Ce prototype illustre "
            "la faisabilité technique de la digitalisation de la fiche de déclaration "
            "d'écart (chapitre 5 du rapport) et son exploitation analytique "
            "(chapitre 4 — vote pondéré des causes)."
        )

# =========================================================
# EN-TÊTE
# =========================================================
st.markdown(
    f"""
    <div style="background-color:{NAVY};padding:18px 24px;border-radius:6px;">
        <h1 style="color:white;margin:0;font-size:26px;">Fiche de déclaration d'écart — SEVAM</h1>
        <p style="color:#D9E2F3;margin:4px 0 0 0;font-size:14px;">
        Prototype numérique — remplace la saisie papier proposée au chapitre 5 du rapport PFA,
        alimente en direct l'analyse Pareto des causes et son impact économique.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

tab_saisie, tab_dashboard, tab_eco, tab_methodo = st.tabs(
    ["📝 Saisie d'une déclaration", "📊 Pilotage QCD & Pareto", "💰 Impact économique", "📘 Méthodologie & note technique"]
)

# =========================================================
# ONGLET 1 — Saisie
# =========================================================
with tab_saisie:
    col_form, col_help = st.columns([2, 1])

    with col_form:
        st.subheader("Nouvelle déclaration")
        with st.form("form_declaration", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_of = st.text_input("N° OF concerné", placeholder="OF-2026-0458")
                d = st.date_input("Date", value=date(2026, 7, 1))
            with c2:
                ligne_four = st.selectbox("Ligne / Four", [f"{l} / {f}" for l, f in LIGNES])
                ref = st.text_input("Référence article", placeholder="APO 65 CL VA SACO")
            with c3:
                qte_plan = st.number_input("Quantité planifiée", min_value=0, value=10000, step=100)
                qte_real = st.number_input("Quantité réalisée", min_value=0, value=9200, step=100)

            cause = st.selectbox(
                "Code cause",
                options=list(CAUSES.keys()),
                format_func=lambda c: f"{c} — {CAUSES[c]}",
            )
            commentaire = st.text_area("Commentaire libre", placeholder="Arrêt non planifié du four 2 — remise en route à 14h20...")
            declare_par = st.text_input("Déclaré par", placeholder="Nom, prénom")

            submitted = st.form_submit_button("Enregistrer la déclaration", type="primary")

        if submitted:
            if not n_of or qte_plan == 0:
                st.error("Merci de renseigner au moins le N° OF et une quantité planifiée non nulle.")
            else:
                ligne, four = ligne_four.split(" / ")
                ecart_unites = qte_real - qte_plan
                ecart_pct = round((ecart_unites / qte_plan) * 100, 2) if qte_plan else 0
                statut = "A traiter" if abs(ecart_pct) > seuil_alerte else "OK"
                new_row = {
                    "N_OF": n_of, "Date": pd.to_datetime(d), "Ligne": ligne, "Four": four,
                    "Reference_Article": ref, "Qte_Planifiee": qte_plan, "Qte_Realisee": qte_real,
                    "Ecart_Unites": ecart_unites, "Ecart_Pct": ecart_pct, "Code_Cause": cause,
                    "Libelle_Cause": CAUSES[cause], "Statut": statut,
                }
                st.session_state.declarations = pd.concat(
                    [st.session_state.declarations, pd.DataFrame([new_row])], ignore_index=True
                )
                color = RED if statut == "A traiter" else GREEN
                cout_est = abs(ecart_unites) * cout_unitaire
                st.markdown(
                    f"<div style='padding:10px 14px;border-left:4px solid {color};background:#F2F2F2;'>"
                    f"<b>Déclaration enregistrée.</b> Écart calculé : <b>{ecart_unites:+d} unités "
                    f"({ecart_pct:+.1f}%)</b> — statut : <b style='color:{color}'>{statut}</b> "
                    f"(seuil actuel : {seuil_alerte}%). Impact économique estimé : <b>{cout_est:,.0f} MAD</b>. "
                    f"Consultable immédiatement dans les onglets Pilotage et Impact économique."
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.write("")
        st.caption(f"{len(st.session_state.declarations)} déclarations dans la base (données de démonstration + saisies de cette session).")
        st.dataframe(
            st.session_state.declarations.sort_values("Date", ascending=False).head(15),
            use_container_width=True, hide_index=True,
        )

    with col_help:
        st.markdown("**ℹ️ Ce qu'il faut savoir**")
        st.info(
            "Ce formulaire numérise exactement les champs de la fiche papier proposée "
            "au chapitre 5 : OF, ligne/four, quantités planifiée/réalisée, code cause "
            "(FOUR / APPRO / SERIE / QUALITE / AUTRE) et commentaire libre.",
            icon="📋",
        )
        with st.expander("Comment l'écart est calculé"):
            st.markdown(
                "- **Écart (unités)** = Quantité réalisée − Quantité planifiée\n"
                "- **Écart (%)** = Écart ÷ Quantité planifiée\n"
                "- **Statut** = « À traiter » si │Écart %│ dépasse le seuil défini dans le panneau "
                "de gauche (5 % par défaut, ajustable)."
            )
        with st.expander("Pourquoi digitaliser cette fiche ?"):
            st.markdown(
                "- Élimine la ressaisie manuelle dans l'ERP JD Edwards.\n"
                "- Rend la donnée exploitable immédiatement (zéro délai entre déclaration et analyse).\n"
                "- Standardise les codes cause, condition indispensable à un Pareto fiable.\n"
                "- Prépare l'alimentation automatique de Qlik Sense (nouvelle dimension « cause »)."
            )

# =========================================================
# ONGLET 2 — Pilotage QCD & Pareto
# =========================================================
with tab_dashboard:
    df = st.session_state.declarations.copy()
    df["Statut"] = df.apply(
        lambda r: "A traiter" if pd.notna(r["Ecart_Pct"]) and abs(r["Ecart_Pct"]) > seuil_alerte else "OK", axis=1
    )

    if df.empty:
        st.info("Aucune déclaration disponible pour l'instant.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            lignes_dispo = sorted(df["Ligne"].dropna().unique().tolist())
            sel_lignes = st.multiselect("Filtrer par ligne", lignes_dispo, default=lignes_dispo)
        with col_f2:
            min_d, max_d = df["Date"].min(), df["Date"].max()
            sel_dates = st.date_input("Période", value=(min_d, max_d))

        dff = df[df["Ligne"].isin(sel_lignes)]
        if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
            dff = dff[(dff["Date"] >= pd.to_datetime(sel_dates[0])) & (dff["Date"] <= pd.to_datetime(sel_dates[1]))]

        taux_service = dff["Qte_Realisee"].sum() / dff["Qte_Planifiee"].sum() if dff["Qte_Planifiee"].sum() else 0
        nb_of = dff["N_OF"].nunique()
        nb_ecart = (dff["Statut"] == "A traiter").sum()
        ecart_cumule = int(dff["Ecart_Unites"].sum())
        taux_conformite = 1 - (nb_ecart / nb_of if nb_of else 0)
        causes_qualite = dff[dff["Code_Cause"] == "QUALITE"]["Ecart_Unites"].abs().sum()

        st.markdown("#### Pilotage selon les 3 critères Qualité — Coût — Délai (QCD)")
        st.caption(
            "Structure de lecture classique en ingénierie industrielle : chaque écart de production "
            "se lit à travers son impact sur la qualité livrée, son coût, et le respect du planning."
        )
        q1, q2, q3 = st.columns(3)
        with q1:
            st.markdown(f"<div style='border-left:5px solid {BLUE};padding:8px 12px;background:#F2F2F2;'>"
                        f"<b>QUALITÉ</b><br><span style='font-size:22px;color:{NAVY}'>{taux_conformite*100:.1f}%</span>"
                        f"<br><span style='font-size:12px;color:#555;'>OF conformes au seuil de {seuil_alerte}%</span></div>",
                        unsafe_allow_html=True)
        with q2:
            st.markdown(f"<div style='border-left:5px solid {AMBER};padding:8px 12px;background:#F2F2F2;'>"
                        f"<b>COÛT</b><br><span style='font-size:22px;color:{NAVY}'>{abs(ecart_cumule)*cout_unitaire:,.0f} MAD</span>"
                        f"<br><span style='font-size:12px;color:#555;'>Impact estimé (voir onglet Impact économique)</span></div>",
                        unsafe_allow_html=True)
        with q3:
            st.markdown(f"<div style='border-left:5px solid {RED};padding:8px 12px;background:#F2F2F2;'>"
                        f"<b>DÉLAI</b><br><span style='font-size:22px;color:{NAVY}'>{nb_ecart} / {nb_of}</span>"
                        f"<br><span style='font-size:12px;color:#555;'>OF n'ayant pas atteint la quantité planifiée dans le temps imparti</span></div>",
                        unsafe_allow_html=True)

        st.write("")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Taux de service", f"{taux_service*100:.1f}%",
                   help="Quantité totale réalisée ÷ Quantité totale planifiée, sur la période et les lignes filtrées.")
        k2.metric("Nb OF suivis", nb_of, help="Nombre d'ordres de fabrication distincts sur la sélection.")
        k3.metric(f"OF en écart (> {seuil_alerte}%)", nb_ecart,
                   help="Nombre d'OF dont l'écart absolu dépasse le seuil d'alerte défini dans le panneau de gauche.")
        k4.metric("Écart cumulé (unités)", f"{ecart_cumule:+d}",
                   help="Somme des écarts (réalisé − planifié) sur la sélection ; négatif = sous-production.")

        st.write("")
        col_a, col_b = st.columns([1.3, 1])

        with col_a:
            st.markdown("**Analyse Pareto des causes d'écart**")
            causes_df = dff[dff["Code_Cause"].notna() & (dff["Code_Cause"] != "")]
            if not causes_df.empty:
                pareto = (
                    causes_df.groupby("Code_Cause")["Ecart_Unites"]
                    .apply(lambda s: s.abs().sum())
                    .sort_values(ascending=False)
                    .reset_index()
                )
                pareto["cum_pct"] = pareto["Ecart_Unites"].cumsum() / pareto["Ecart_Unites"].sum() * 100

                fig = go.Figure()
                fig.add_bar(x=pareto["Code_Cause"], y=pareto["Ecart_Unites"], name="Écart cumulé (unités)", marker_color=BLUE)
                fig.add_trace(go.Scatter(
                    x=pareto["Code_Cause"], y=pareto["cum_pct"], name="% cumulé",
                    yaxis="y2", mode="lines+markers", line=dict(color=RED, width=3),
                ))
                fig.add_hline(y=80, line_dash="dot", line_color="#888", yref="y2",
                               annotation_text="Seuil des 80% (règle de Pareto)", annotation_position="bottom right")
                fig.update_layout(
                    yaxis=dict(title="Écart cumulé (unités)"),
                    yaxis2=dict(title="% cumulé", overlaying="y", side="right", range=[0, 105]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    margin=dict(t=40, b=20), height=380,
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"Cause n°1 : **{pareto.iloc[0]['Code_Cause']}** — {CAUSES.get(pareto.iloc[0]['Code_Cause'], '')}")
                with st.expander("ℹ️ Comment lire ce graphique (règle des 80/20)"):
                    st.markdown(
                        "Le principe de Pareto suppose qu'environ 80% des écarts proviennent de 20% des causes. "
                        "Les barres bleues classent les causes par volume d'écart cumulé décroissant ; la courbe "
                        "rouge cumule leur poids relatif. La cause dont la courbe franchit le repère des 80% "
                        "constitue la priorité d'action — c'est directement la logique du vote pondéré des "
                        "causes du chapitre 4, ici recalculée automatiquement à partir des données terrain "
                        "plutôt qu'estimée par les équipes."
                    )
            else:
                st.info("Aucun écart avec cause renseignée sur la période filtrée.")

        with col_b:
            st.markdown("**Écart cumulé par ligne / four**")
            par_ligne = dff.groupby("Ligne")["Ecart_Unites"].sum().sort_values()
            fig2 = px.bar(
                par_ligne, orientation="h", labels={"value": "Écart cumulé", "Ligne": ""},
                color_discrete_sequence=[RED],
            )
            fig2.update_layout(showlegend=False, margin=dict(t=10, b=20), height=380)
            st.plotly_chart(fig2, use_container_width=True)
            with st.expander("ℹ️ Comment lire ce graphique"):
                st.markdown(
                    "Chaque barre cumule les écarts (en unités) des OF associés à une ligne/four. "
                    "Une ligne nettement plus négative que les autres signale un point chaud à "
                    "investiguer en priorité (maintenance préventive, réglages, formation opérateurs)."
                )

# =========================================================
# ONGLET 3 — Impact économique
# =========================================================
with tab_eco:
    df = st.session_state.declarations.copy()
    st.markdown("#### Traduction financière des écarts")
    st.caption(
        "Un diagnostic industriel se défend aussi en langage financier. Cet onglet convertit "
        "les écarts de production en ordre de grandeur monétaire, pour appuyer l'argumentaire "
        "auprès de la direction — le coût unitaire est paramétrable dans le panneau de gauche "
        "et doit être confirmé avec le contrôle de gestion SEVAM avant toute utilisation réelle."
    )

    if df.empty:
        st.info("Aucune donnée disponible.")
    else:
        cout_total = df["Ecart_Unites"].abs().sum() * cout_unitaire
        causes_df = df[df["Code_Cause"].notna() & (df["Code_Cause"] != "")]
        cout_par_cause = (
            causes_df.groupby("Code_Cause")["Ecart_Unites"].apply(lambda s: s.abs().sum() * cout_unitaire)
            .sort_values(ascending=False)
        )

        e1, e2, e3 = st.columns(3)
        e1.metric("Coût total estimé des écarts", f"{cout_total:,.0f} MAD",
                   help="Somme des écarts absolus (en unités) × coût unitaire paramétré.")
        if not cout_par_cause.empty:
            e2.metric("Cause la plus coûteuse", cout_par_cause.index[0],
                       help=CAUSES.get(cout_par_cause.index[0], ""))
            e3.metric("Coût de cette cause", f"{cout_par_cause.iloc[0]:,.0f} MAD")

        st.write("")
        col_c, col_d = st.columns([1.2, 1])
        with col_c:
            st.markdown("**Coût estimé par cause**")
            if not cout_par_cause.empty:
                fig3 = px.bar(
                    cout_par_cause, orientation="h", labels={"value": "Coût estimé (MAD)", "index": ""},
                    color_discrete_sequence=[AMBER],
                )
                fig3.update_layout(showlegend=False, margin=dict(t=10, b=20), height=340)
                st.plotly_chart(fig3, use_container_width=True)

        with col_d:
            st.markdown("**Simulation de gain — plan d'action**")
            st.caption("Estime l'économie réalisable si la cause n°1 est réduite grâce aux actions proposées.")
            if not cout_par_cause.empty:
                objectif_reduction = st.slider(
                    f"Objectif de réduction de la cause « {cout_par_cause.index[0]} » (%)",
                    min_value=0, max_value=100, value=30, step=5,
                )
                gain_estime = cout_par_cause.iloc[0] * (objectif_reduction / 100)
                st.markdown(
                    f"<div style='padding:14px;border-left:4px solid {GREEN};background:#F2F2F2;margin-top:8px;'>"
                    f"Réduire la cause <b>{cout_par_cause.index[0]}</b> de <b>{objectif_reduction}%</b> "
                    f"représenterait une économie estimée de <br>"
                    f"<span style='font-size:24px;color:{GREEN};font-weight:bold;'>{gain_estime:,.0f} MAD</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                with st.expander("ℹ️ Comment utiliser cet argument en soutenance"):
                    st.markdown(
                        "Ce chiffre n'est pas une prévision garantie — c'est un **ordre de grandeur** "
                        "qui répond à la question que pose souvent un jury : « et concrètement, "
                        "ça rapporte quoi ? ». Il montre que le diagnostic (chapitre 3-4) débouche "
                        "sur un plan d'action chiffrable, pas seulement descriptif."
                    )

# =========================================================
# ONGLET 4 — Méthodologie & note technique
# =========================================================
with tab_methodo:
    st.markdown("#### Note méthodologique — à destination du jury")

    st.markdown("**1. Contexte et objectif**")
    st.markdown(
        "Ce prototype répond à une limite identifiée dans le diagnostic du rapport PFA : la fiche "
        "de déclaration d'écart proposée au chapitre 5 est conçue pour une saisie papier, ce qui "
        "retarde son exploitation et empêche tout pilotage en temps réel. L'objectif de ce prototype "
        "est de démontrer, de façon fonctionnelle et testable, que cette fiche peut être digitalisée "
        "et alimenter automatiquement une analyse des causes (chapitre 4) et un pilotage économique."
    )

    st.markdown("**2. Architecture technique**")
    st.markdown(
        "- **Python** — langage utilisé pour toute la logique de calcul.\n"
        "- **Streamlit** — framework qui transforme le code Python en application web interactive, "
        "sans développement front-end séparé (pas de HTML/CSS/JavaScript à écrire).\n"
        "- **Pandas** — manipulation des données tabulaires (équivalent programmatique d'un tableur).\n"
        "- **Plotly** — génération des graphiques interactifs (zoom, survol, export).\n\n"
        "Schéma de circulation de la donnée :\n\n"
        "`Formulaire de saisie → validation → calcul de l'écart → ajout au tableau en mémoire "
        "→ recalcul automatique des indicateurs → mise à jour des graphiques`"
    )

    st.markdown("**3. Cohérence avec le rapport PFA**")
    st.markdown(
        "- Les champs du formulaire reprennent exactement ceux de la fiche du chapitre 5.\n"
        "- Les codes cause (FOUR / APPRO / SERIE / QUALITE / AUTRE) sont ceux utilisés dans le rapport.\n"
        "- Le graphique Pareto formalise numériquement la méthode de vote pondéré des causes du chapitre 4.\n"
        "- La mention d'intégration à l'ERP JD Edwards et à Qlik Sense reprend la piste d'amélioration "
        "décrite dans le rapport."
    )

    st.markdown("**4. Limites assumées de ce prototype**")
    st.markdown(
        "- Les données affichées par défaut sont **synthétiques** (générées pour la démonstration), "
        "et non les données réelles de production SEVAM.\n"
        "- Les données saisies pendant une session ne sont pas conservées après fermeture de "
        "l'application (pas de base de données persistante) — un choix volontaire pour rester "
        "un prototype léger et facilement démontrable, pas un développement de production.\n"
        "- Le coût unitaire utilisé dans l'onglet Impact économique est un paramètre à ajuster, "
        "pas une donnée validée par le contrôle de gestion."
    )

    st.markdown("**5. Pistes d'évolution vers un outil de production**")
    st.markdown(
        "- Connexion réelle à l'ERP JD Edwards (au lieu d'une saisie manuelle indépendante).\n"
        "- Base de données persistante (ex. SQL Server déjà utilisé par SEVAM) à la place du "
        "stockage en mémoire.\n"
        "- Authentification des utilisateurs et traçabilité des déclarations (qui a saisi, quand).\n"
        "- Publication automatique vers Qlik Sense via connecteur API plutôt qu'un tableau de bord "
        "Streamlit autonome."
    )

    st.write("")
    st.markdown(
        f"<div style='padding:12px 16px;background:#F2F2F2;border-radius:6px;font-size:12.5px;color:#555;'>"
        f"Prototype développé en Python — PFA « Diagnostic des écarts de production, SEVAM » — 2026. "
        f"Ce document et l'application associée constituent une preuve de concept à visée pédagogique."
        f"</div>",
        unsafe_allow_html=True,
    )

st.write("")
st.caption(
    "Prototype de démonstration — l'intégration réelle se ferait dans l'ERP JD Edwards, "
    "avec alimentation automatique de la plateforme Qlik Sense (dimension « cause »), "
    "comme décrit au chapitre 5 du rapport PFA."
)
