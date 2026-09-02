"""
Prototype — Fiche de déclaration d'écart numérique (SEVAM)
===========================================================
Preuve de concept d'une saisie numérique de la fiche de déclaration
d'écart (chapitre 5 du rapport PFA) qui alimenterait automatiquement
un pilotage type Qlik Sense / Power BI, en remplacement de la saisie
papier actuelle.

Version 4 — catalogue produits et structure four/ligne reconstruits à partir
de 3 fichiers réels transmis par SEVAM (voir catalogue_sevam.py pour le détail
des sources), atelier Décor modélisé comme un atelier transverse (pas de four
dédié), et accès différencié par rôle :
  - Opérateur          -> saisie sur sa ligne uniquement
  - Chef de service     -> pilotage de son four (toutes lignes du four)
  - Chef de département -> pilotage de son département (Gobeleterie / Verre
                            creux / Décor), y compris impact économique
  - Directeur Général    -> accès complet, tous départements, vue comparative

Lancement local : streamlit run app.py
Auteur : SALMA — PFA SEVAM 2026
"""

import base64
import os
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import catalogue_sevam as cat

st.set_page_config(
    page_title="Fiche de déclaration d'écart — SEVAM",
    page_icon="🏭",
    layout="wide",
)

# =========================================================
# IDENTITÉ VISUELLE SEVAM — palette extraite du logo officiel
# =========================================================
SEVAM_RED = "#B52F2F"
SEVAM_RED_DARK = "#8C2222"
SEVAM_GREEN = "#339848"
SEVAM_GREEN_DARK = "#1E6B31"
SAND = "#F7F3EE"
WHITE = "#FFFFFF"
GREY_TEXT = "#4A4A4A"
AMBER = "#B8860B"
BLUE_ROLE = "#2E5395"

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "Dataset_Ecarts_Production_SEVAM.csv")
LOGO_PATH = os.path.join(BASE_DIR, "logo_sevam.png")


@st.cache_data
def get_logo_base64():
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


LOGO_B64 = get_logo_base64()

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {SAND}; }}
    section[data-testid="stSidebar"] {{ background-color: {WHITE}; border-right: 1px solid #E7DFD5; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {WHITE}; border-radius: 6px 6px 0 0; padding: 8px 16px;
        border: 1px solid #E7DFD5; border-bottom: none;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {SEVAM_RED} !important; color: white !important;
    }}
    div.stButton > button[kind="primary"] {{
        background-color: {SEVAM_RED}; border-color: {SEVAM_RED};
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: {SEVAM_RED_DARK}; border-color: {SEVAM_RED_DARK};
    }}
    [data-testid="stMetricValue"] {{ color: {SEVAM_RED_DARK}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

FOURS = cat.FOURS
LIGNES = cat.LIGNES
LIGNE_LABELS = cat.LIGNE_LABELS
DEPARTEMENTS = cat.DEPARTEMENTS
CAUSES = cat.CAUSES
ROLES = cat.ROLES
ARTICLES = cat.ARTICLES


@st.cache_data
def load_base_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8-sig")
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    return pd.DataFrame(columns=[
        "N_OF", "Date", "Ligne", "Four", "Site", "Departement", "Reference_Article",
        "Famille_Article", "Decore", "Marque_Decor", "Qte_Planifiee", "Qte_Realisee",
        "Ecart_Unites", "Ecart_Pct", "Code_Cause", "Libelle_Cause", "Statut",
    ])


if "declarations" not in st.session_state:
    st.session_state.declarations = load_base_data().copy()


# =========================================================
# PÉRIMÈTRE DE DONNÉES SELON LE RÔLE (simulation d'accès — pas d'authentification réelle)
# =========================================================
def lignes_du_four(four_code):
    return [code for code, four in LIGNES if four == four_code]


def fours_du_departement(dep):
    return DEPARTEMENTS[dep]["fours"]


def filtrer_par_perimetre(df, role, scope):
    """Restreint un DataFrame au périmètre visible pour le rôle/scope choisis."""
    if df.empty or role == "Directeur Général (DG)":
        return df
    if role == "Opérateur":
        return df[df["Ligne"] == scope]
    if role == "Chef de service":
        return df[df["Four"] == scope]
    if role == "Chef de département":
        if scope == "Décor":
            return df[df["Decore"] == "OUI"]
        return df[df["Departement"] == scope]
    return df


with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f"<div style='background:{WHITE};padding:16px;border-radius:6px;border:1px solid #E7DFD5;text-align:center;'>"
            f"<img src='data:image/png;base64,{LOGO_B64}' style='max-width:100%;height:auto;'/>"
            f"<p style='color:{GREY_TEXT};margin:8px 0 0 0;font-size:12px;'>Pilotage numérique des écarts de production</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("### 🏭 SEVAM")

    st.write("")
    st.markdown("**Session (démonstration)**")
    st.caption(
        "Simule la connexion d'un utilisateur : chaque rôle voit une vue adaptée à son "
        "périmètre. Il ne s'agit pas d'une authentification réelle — voir onglet Méthodologie."
    )
    role = st.selectbox("Rôle", ROLES, index=0)

    scope = None
    scope_label = "Tous les départements"
    if role == "Opérateur":
        scope = st.selectbox(
            "Votre ligne", options=[code for code, _ in LIGNES],
            format_func=lambda code: LIGNE_LABELS[code],
        )
        scope_label = LIGNE_LABELS[scope]
    elif role == "Chef de service":
        scope = st.selectbox(
            "Votre four", options=list(FOURS.keys()),
            format_func=lambda f: f"{f} — {FOURS[f]['site']}",
        )
        scope_label = f"Four {scope} ({FOURS[scope]['site']})"
    elif role == "Chef de département":
        scope = st.selectbox("Votre département", options=list(DEPARTEMENTS.keys()))
        scope_label = f"Département {scope}"
    else:
        scope_label = "Tous les départements (DG)"

    st.markdown(
        f"<div style='padding:8px 10px;background:#EEF2F9;border-left:4px solid {BLUE_ROLE};"
        f"border-radius:4px;font-size:12.5px;color:{GREY_TEXT};margin-top:4px;'>"
        f"Connecté en tant que <b>{role}</b><br>Périmètre : <b>{scope_label}</b></div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("**Paramètres de pilotage**")
    seuil_alerte = st.slider(
        "Seuil d'alerte écart (%)", min_value=1, max_value=20, value=5,
        help="Au-delà de ce pourcentage d'écart, un OF est classé « À traiter ».",
    )
    cout_unitaire = st.number_input(
        "Coût moyen estimé par unité non produite (MAD)", min_value=0.0, value=8.0, step=0.5,
        help="Valeur à ajuster avec le contrôle de gestion SEVAM.",
    )
    st.caption("Ces deux paramètres recalculent en direct tous les indicateurs.")

    st.write("")
    st.markdown("**Résumé rapide (votre périmètre)**")
    _df_scope = filtrer_par_perimetre(st.session_state.declarations, role, scope)
    if not _df_scope.empty:
        st.metric("OF suivis", int(_df_scope["N_OF"].nunique()))
        st.metric("Taux de service", f"{(_df_scope['Qte_Realisee'].sum()/_df_scope['Qte_Planifiee'].sum()*100):.1f}%")

    st.write("")
    with st.expander("🏭 Parc de fours SEVAM"):
        for code, info in FOURS.items():
            st.caption(f"**{code}** — {info['site']} · {info['departement']} · {info['statut']}")
        st.caption(
            "Codification des lignes L11/L12/L13 (four U2) et L21/L22/L23 (four U3) confirmée "
            "par le journal de production réel de l'entreprise. Celle de U1 et U4 prolonge la "
            "même logique et reste à vérifier auprès de SEVAM (voir Méthodologie)."
        )

    with st.expander("ℹ️ À propos de ce prototype"):
        st.caption(
            "Développé en Python (Streamlit, Pandas, Plotly) dans le cadre du PFA "
            "« Diagnostic des écarts de production — SEVAM ». Catalogue produit et structure "
            "four/ligne reconstruits à partir de fichiers réels transmis par l'entreprise."
        )

# =========================================================
# EN-TÊTE
# =========================================================
logo_html = (
    f"<img src='data:image/png;base64,{LOGO_B64}' style='height:52px;background:white;padding:6px 10px;border-radius:6px;margin-right:16px;'/>"
    if LOGO_B64 else ""
)
st.markdown(
    f"""
    <div style="background:linear-gradient(90deg, {SEVAM_RED_DARK} 0%, {SEVAM_RED} 100%);
                padding:18px 24px;border-radius:6px;display:flex;align-items:center;justify-content:space-between;
                border-bottom:4px solid {SEVAM_GREEN};">
        <div style="display:flex;align-items:center;">
            {logo_html}
            <div>
                <h1 style="color:white;margin:0;font-size:26px;">Fiche de déclaration d'écart — SEVAM</h1>
                <p style="color:#FBEAE8;margin:4px 0 0 0;font-size:14px;">
                Prototype numérique — remplace la saisie papier proposée au chapitre 5 du rapport PFA,
                alimente en direct l'analyse Pareto des causes et son impact économique.
                </p>
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.15);padding:8px 14px;border-radius:6px;color:white;font-size:13px;text-align:right;">
            👤 <b>{role}</b><br><span style="font-size:11.5px;">{scope_label}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# =========================================================
# ONGLETS VISIBLES SELON LE RÔLE
# =========================================================
if role == "Opérateur":
    tab_names = ["📝 Saisie d'une déclaration", "📘 Méthodologie & note technique"]
elif role == "Chef de service":
    tab_names = ["📝 Saisie d'une déclaration", "📊 Pilotage QCD & Pareto", "📘 Méthodologie & note technique"]
else:  # Chef de département, DG
    tab_names = ["📝 Saisie d'une déclaration", "📊 Pilotage QCD & Pareto", "💰 Impact économique", "📘 Méthodologie & note technique"]

tabs = st.tabs(tab_names)
tab_map = dict(zip(tab_names, tabs))

# =========================================================
# ONGLET — Saisie
# =========================================================
with tab_map["📝 Saisie d'une déclaration"]:
    col_form, col_help = st.columns([2, 1])

    with col_form:
        st.subheader("Nouvelle déclaration")

        if role == "Opérateur":
            lignes_possibles = [scope]
        elif role == "Chef de service":
            lignes_possibles = lignes_du_four(scope)
        elif role == "Chef de département":
            fours_dep = fours_du_departement(scope) if scope != "Décor" else list(FOURS.keys())
            lignes_possibles = [code for code, four in LIGNES if four in fours_dep]
        else:
            lignes_possibles = [code for code, _ in LIGNES]

        with st.form("form_declaration", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_of = st.text_input("N° OF concerné", placeholder="OF-2026-0458")
                d = st.date_input("Date", value=date(2026, 7, 1))
            with c2:
                ligne_choice = st.selectbox(
                    "Ligne / Four", options=lignes_possibles,
                    format_func=lambda code: LIGNE_LABELS[code],
                )
                four_sel = dict(LIGNES)[ligne_choice]
                dep_sel = FOURS[four_sel]["departement"]
                famille_sel = "Gobeleterie (verres)" if dep_sel == "Gobeleterie" else "Verre creux (bouteilles / pots)"
                articles_dispo = cat.ARTICLES_BY_FAMILLE[famille_sel]
                article_choice = st.selectbox(
                    "Référence article", options=range(len(articles_dispo)),
                    format_func=lambda i: articles_dispo[i]["article"] + (" 🎨 (décor)" if articles_dispo[i]["decore"] else ""),
                )
                art_rec = articles_dispo[article_choice]
            with c3:
                qte_plan = st.number_input("Quantité planifiée", min_value=0, value=10000, step=100)
                qte_real = st.number_input("Quantité réalisée", min_value=0, value=9200, step=100)

            causes_possibles = list(CAUSES.keys()) if art_rec["decore"] else [k for k in CAUSES if k != "DECOR"]
            cause = st.selectbox(
                "Code cause", options=causes_possibles,
                format_func=lambda c: f"{c} — {CAUSES[c]}",
            )
            commentaire = st.text_area("Commentaire libre", placeholder="Arrêt non planifié — remise en route à 14h20...")
            declare_par = st.text_input("Déclaré par", placeholder="Nom, prénom")

            if art_rec["decore"]:
                st.caption(f"🎨 Article de l'atelier Décor — client/marque : **{art_rec['marque'] or 'personnalisation générique'}**")

            submitted = st.form_submit_button("Enregistrer la déclaration", type="primary")

        if submitted:
            if not n_of or qte_plan == 0:
                st.error("Merci de renseigner au moins le N° OF et une quantité planifiée non nulle.")
            else:
                site = FOURS[four_sel]["site"]
                ecart_unites = qte_real - qte_plan
                ecart_pct = round((ecart_unites / qte_plan) * 100, 2) if qte_plan else 0
                statut = "A traiter" if abs(ecart_pct) > seuil_alerte else "OK"
                new_row = {
                    "N_OF": n_of, "Date": pd.to_datetime(d), "Ligne": ligne_choice, "Four": four_sel,
                    "Site": site, "Departement": dep_sel, "Reference_Article": art_rec["article"],
                    "Famille_Article": art_rec["famille"], "Decore": "OUI" if art_rec["decore"] else "NON",
                    "Marque_Decor": art_rec["marque"] or "", "Qte_Planifiee": qte_plan, "Qte_Realisee": qte_real,
                    "Ecart_Unites": ecart_unites, "Ecart_Pct": ecart_pct, "Code_Cause": cause,
                    "Libelle_Cause": CAUSES[cause], "Statut": statut,
                }
                st.session_state.declarations = pd.concat(
                    [st.session_state.declarations, pd.DataFrame([new_row])], ignore_index=True
                )
                color = SEVAM_RED if statut == "A traiter" else SEVAM_GREEN
                cout_est = abs(ecart_unites) * cout_unitaire
                st.markdown(
                    f"<div style='padding:10px 14px;border-left:4px solid {color};background:{WHITE};'>"
                    f"<b>Déclaration enregistrée.</b> Écart calculé : <b>{ecart_unites:+d} unités "
                    f"({ecart_pct:+.1f}%)</b> — statut : <b style='color:{color}'>{statut}</b> "
                    f"(seuil actuel : {seuil_alerte}%). Impact économique estimé : <b>{cout_est:,.0f} MAD</b>."
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.write("")
        df_perimetre = filtrer_par_perimetre(st.session_state.declarations, role, scope)
        st.caption(f"{len(df_perimetre)} déclarations visibles dans votre périmètre ({role} — {scope_label}).")
        st.dataframe(
            df_perimetre.sort_values("Date", ascending=False).head(15),
            use_container_width=True, hide_index=True,
        )

        if role == "Opérateur" and not df_perimetre.empty:
            st.write("")
            st.markdown("**Votre performance récente (ligne " + scope + ")**")
            o1, o2, o3 = st.columns(3)
            taux = df_perimetre["Qte_Realisee"].sum() / df_perimetre["Qte_Planifiee"].sum() if df_perimetre["Qte_Planifiee"].sum() else 0
            o1.metric("Taux de service", f"{taux*100:.1f}%")
            o2.metric("OF déclarés", df_perimetre["N_OF"].nunique())
            o3.metric("OF en écart", int((df_perimetre["Statut"] == "A traiter").sum()))
            st.caption(
                "Vue volontairement simplifiée : un opérateur suit sa ligne au quotidien, pas les "
                "coûts consolidés ni les autres lignes/départements — accès complet réservé aux "
                "chefs de service, chefs de département et à la Direction Générale."
            )

    with col_help:
        st.markdown("**ℹ️ Ce qu'il faut savoir**")
        st.info(
            "Ce formulaire numérise exactement les champs de la fiche papier proposée "
            "au chapitre 5 : OF, ligne/four, article, quantités planifiée/réalisée, code cause "
            "et commentaire libre. Le champ Référence article vient du vrai catalogue SEVAM.",
            icon="📋",
        )
        with st.expander("Structure réelle des fours et lignes SEVAM"):
            st.markdown(
                "- **U1** — Roches Noires, le plus ancien four, dédié à la **Gobeleterie** (verres à thé/café/jus).\n"
                "- **U2, U3, U4** — Tit Mellil, dédiés au **Verre creux** (bouteilles, pots, bocaux).\n\n"
                "Codes de ligne réellement observés dans le journal de production SEVAM : "
                "**U2 → L11/L12/L13**, **U3 → L21/L22/L23**. Ceux de U1 et U4 prolongent la même "
                "logique (rang du four → dizaine, n° de ligne → unité) et restent à confirmer."
            )
        with st.expander("L'atelier Décor"):
            st.markdown(
                "La personnalisation (logos clients, motifs décoratifs) est réalisée dans un "
                "**atelier unique**, en sortie de four — quel que soit le four d'origine. Ce n'est "
                "donc pas une ligne de production supplémentaire mais une étape transverse, "
                "rattachée à l'article (champ *décor* du catalogue) plutôt qu'à une ligne."
            )
        with st.expander("Comment l'écart est calculé"):
            st.markdown(
                "- **Écart (unités)** = Quantité réalisée − Quantité planifiée\n"
                "- **Écart (%)** = Écart ÷ Quantité planifiée\n"
                "- **Statut** = « À traiter » si │Écart %│ dépasse le seuil défini dans le panneau de gauche."
            )

# =========================================================
# ONGLET — Pilotage QCD & Pareto
# =========================================================
if "📊 Pilotage QCD & Pareto" in tab_map:
    with tab_map["📊 Pilotage QCD & Pareto"]:
        df = filtrer_par_perimetre(st.session_state.declarations, role, scope).copy()
        df["Statut"] = df.apply(
            lambda r: "A traiter" if pd.notna(r["Ecart_Pct"]) and abs(r["Ecart_Pct"]) > seuil_alerte else "OK", axis=1
        )

        if df.empty:
            st.info("Aucune déclaration disponible pour votre périmètre.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                fours_dispo = sorted(df["Four"].dropna().unique().tolist())
                sel_fours = st.multiselect("Filtrer par four", fours_dispo, default=fours_dispo)
            with col_f2:
                lignes_dispo = sorted(df[df["Four"].isin(sel_fours)]["Ligne"].dropna().unique().tolist())
                sel_lignes = st.multiselect("Filtrer par ligne", lignes_dispo, default=lignes_dispo)
            with col_f3:
                min_d, max_d = df["Date"].min(), df["Date"].max()
                sel_dates = st.date_input("Période", value=(min_d, max_d))

            dff = df[df["Four"].isin(sel_fours) & df["Ligne"].isin(sel_lignes)]
            if isinstance(sel_dates, tuple) and len(sel_dates) == 2:
                dff = dff[(dff["Date"] >= pd.to_datetime(sel_dates[0])) & (dff["Date"] <= pd.to_datetime(sel_dates[1]))]

            taux_service = dff["Qte_Realisee"].sum() / dff["Qte_Planifiee"].sum() if dff["Qte_Planifiee"].sum() else 0
            nb_of = dff["N_OF"].nunique()
            nb_ecart = (dff["Statut"] == "A traiter").sum()
            ecart_cumule = int(dff["Ecart_Unites"].sum())
            taux_conformite = 1 - (nb_ecart / nb_of if nb_of else 0)

            st.markdown("#### Pilotage selon les 3 critères Qualité — Coût — Délai (QCD)")
            st.caption(f"Périmètre affiché : **{role} — {scope_label}**.")
            q1, q2, q3 = st.columns(3)
            with q1:
                st.markdown(f"<div style='border-left:5px solid {SEVAM_GREEN};padding:8px 12px;background:{WHITE};'>"
                            f"<b>QUALITÉ</b><br><span style='font-size:22px;color:{SEVAM_RED_DARK}'>{taux_conformite*100:.1f}%</span>"
                            f"<br><span style='font-size:12px;color:{GREY_TEXT};'>OF conformes au seuil de {seuil_alerte}%</span></div>",
                            unsafe_allow_html=True)
            with q2:
                st.markdown(f"<div style='border-left:5px solid {AMBER};padding:8px 12px;background:{WHITE};'>"
                            f"<b>COÛT</b><br><span style='font-size:22px;color:{SEVAM_RED_DARK}'>{abs(ecart_cumule)*cout_unitaire:,.0f} MAD</span>"
                            f"<br><span style='font-size:12px;color:{GREY_TEXT};'>Impact estimé (voir onglet Impact économique)</span></div>",
                            unsafe_allow_html=True)
            with q3:
                st.markdown(f"<div style='border-left:5px solid {SEVAM_RED};padding:8px 12px;background:{WHITE};'>"
                            f"<b>DÉLAI</b><br><span style='font-size:22px;color:{SEVAM_RED_DARK}'>{nb_ecart} / {nb_of}</span>"
                            f"<br><span style='font-size:12px;color:{GREY_TEXT};'>OF n'ayant pas atteint la quantité planifiée dans le temps imparti</span></div>",
                            unsafe_allow_html=True)

            st.write("")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Taux de service", f"{taux_service*100:.1f}%")
            k2.metric("Nb OF suivis", nb_of)
            k3.metric(f"OF en écart (> {seuil_alerte}%)", nb_ecart)
            k4.metric("Écart cumulé (unités)", f"{ecart_cumule:+d}")

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
                    fig.add_bar(x=pareto["Code_Cause"], y=pareto["Ecart_Unites"], name="Écart cumulé (unités)", marker_color=SEVAM_RED)
                    fig.add_trace(go.Scatter(
                        x=pareto["Code_Cause"], y=pareto["cum_pct"], name="% cumulé",
                        yaxis="y2", mode="lines+markers", line=dict(color=SEVAM_GREEN_DARK, width=3),
                    ))
                    fig.add_hline(y=80, line_dash="dot", line_color="#888", yref="y2",
                                   annotation_text="Seuil des 80% (règle de Pareto)", annotation_position="bottom right")
                    fig.update_layout(
                        yaxis=dict(title="Écart cumulé (unités)"),
                        yaxis2=dict(title="% cumulé", overlaying="y", side="right", range=[0, 105]),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02),
                        margin=dict(t=40, b=20), height=380,
                        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(f"Cause n°1 : **{pareto.iloc[0]['Code_Cause']}** — {CAUSES.get(pareto.iloc[0]['Code_Cause'], '')}")
                else:
                    st.info("Aucun écart avec cause renseignée sur la période filtrée.")

            with col_b:
                st.markdown("**Écart cumulé par ligne**")
                par_ligne = dff.groupby("Ligne")["Ecart_Unites"].sum().sort_values()
                fig2 = px.bar(
                    par_ligne, orientation="h", labels={"value": "Écart cumulé", "Ligne": ""},
                    color_discrete_sequence=[SEVAM_GREEN_DARK],
                )
                fig2.update_layout(showlegend=False, margin=dict(t=10, b=20), height=380,
                                    plot_bgcolor=WHITE, paper_bgcolor=WHITE)
                st.plotly_chart(fig2, use_container_width=True)

            st.write("")
            st.markdown("**Répartition par article et atelier Décor**")
            col_c, col_d = st.columns(2)
            with col_c:
                top_art = dff.groupby("Reference_Article")["Ecart_Unites"].apply(lambda s: s.abs().sum()).sort_values(ascending=False).head(8)
                fig4 = px.bar(top_art, orientation="h", labels={"value": "Écart cumulé (abs.)", "Reference_Article": ""},
                              color_discrete_sequence=[SEVAM_RED_DARK])
                fig4.update_layout(showlegend=False, margin=dict(t=10, b=20), height=320,
                                    plot_bgcolor=WHITE, paper_bgcolor=WHITE, yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig4, use_container_width=True)
                st.caption("Top 8 des articles les plus touchés par les écarts (toutes causes confondues).")
            with col_d:
                decor_share = dff["Decore"].value_counts(normalize=True).reindex(["NON", "OUI"]).fillna(0) * 100
                fig5 = px.pie(values=decor_share.values, names=["Nu", "Décoré (atelier Décor)"],
                              color_discrete_sequence=[SEVAM_GREEN, AMBER])
                fig5.update_layout(margin=dict(t=10, b=10), height=320)
                st.plotly_chart(fig5, use_container_width=True)
                st.caption("Part des OF ayant transité par l'atelier Décor sur le périmètre affiché.")

# =========================================================
# ONGLET — Impact économique
# =========================================================
if "💰 Impact économique" in tab_map:
    with tab_map["💰 Impact économique"]:
        df = filtrer_par_perimetre(st.session_state.declarations, role, scope).copy()
        st.markdown("#### Traduction financière des écarts")
        st.caption(
            f"Périmètre affiché : **{role} — {scope_label}**. Le coût unitaire est paramétrable "
            "dans le panneau de gauche et doit être confirmé avec le contrôle de gestion SEVAM."
        )

        if df.empty:
            st.info("Aucune donnée disponible pour votre périmètre.")
        else:
            cout_total = df["Ecart_Unites"].abs().sum() * cout_unitaire
            causes_df = df[df["Code_Cause"].notna() & (df["Code_Cause"] != "")]
            cout_par_cause = (
                causes_df.groupby("Code_Cause")["Ecart_Unites"].apply(lambda s: s.abs().sum() * cout_unitaire)
                .sort_values(ascending=False)
            )

            e1, e2, e3 = st.columns(3)
            e1.metric("Coût total estimé des écarts", f"{cout_total:,.0f} MAD")
            if not cout_par_cause.empty:
                e2.metric("Cause la plus coûteuse", cout_par_cause.index[0], help=CAUSES.get(cout_par_cause.index[0], ""))
                e3.metric("Coût de cette cause", f"{cout_par_cause.iloc[0]:,.0f} MAD")

            st.write("")
            col_c, col_d = st.columns([1.2, 1])
            with col_c:
                st.markdown("**Coût estimé par cause**")
                if not cout_par_cause.empty:
                    fig3 = px.bar(cout_par_cause, orientation="h", labels={"value": "Coût estimé (MAD)", "index": ""},
                                  color_discrete_sequence=[AMBER])
                    fig3.update_layout(showlegend=False, margin=dict(t=10, b=20), height=340,
                                        plot_bgcolor=WHITE, paper_bgcolor=WHITE)
                    st.plotly_chart(fig3, use_container_width=True)

            with col_d:
                st.markdown("**Simulation de gain — plan d'action**")
                if not cout_par_cause.empty:
                    objectif_reduction = st.slider(
                        f"Objectif de réduction de la cause « {cout_par_cause.index[0]} » (%)",
                        min_value=0, max_value=100, value=30, step=5,
                    )
                    gain_estime = cout_par_cause.iloc[0] * (objectif_reduction / 100)
                    st.markdown(
                        f"<div style='padding:14px;border-left:4px solid {SEVAM_GREEN};background:{WHITE};margin-top:8px;'>"
                        f"Réduire la cause <b>{cout_par_cause.index[0]}</b> de <b>{objectif_reduction}%</b> "
                        f"représenterait une économie estimée de <br>"
                        f"<span style='font-size:24px;color:{SEVAM_GREEN_DARK};font-weight:bold;'>{gain_estime:,.0f} MAD</span>"
                        f"</div>", unsafe_allow_html=True,
                    )

            if role == "Directeur Général (DG)":
                st.write("")
                st.markdown("**Vue comparative inter-départements (réservée à la DG)**")
                df_all = st.session_state.declarations.copy()
                comp = df_all.groupby("Departement").apply(
                    lambda g: pd.Series({
                        "Taux de service": g["Qte_Realisee"].sum() / g["Qte_Planifiee"].sum() * 100 if g["Qte_Planifiee"].sum() else 0,
                        "Coût estimé des écarts (MAD)": g["Ecart_Unites"].abs().sum() * cout_unitaire,
                        "Nb OF": g["N_OF"].nunique(),
                    })
                ).reset_index()
                st.dataframe(comp, use_container_width=True, hide_index=True)
                st.caption(
                    "Seule la Direction Générale voit l'ensemble des départements sur un même écran — "
                    "les chefs de département ne voient que leur propre périmètre."
                )

# =========================================================
# ONGLET — Méthodologie
# =========================================================
with tab_map["📘 Méthodologie & note technique"]:
    st.markdown("#### Note méthodologique — à destination du jury")

    st.markdown("**1. Contexte et objectif**")
    st.markdown(
        "Ce prototype répond à une limite identifiée dans le diagnostic du rapport PFA : la fiche "
        "de déclaration d'écart proposée au chapitre 5 est conçue pour une saisie papier, ce qui "
        "retarde son exploitation et empêche tout pilotage en temps réel."
    )

    st.markdown("**2. Origine des données — catalogue produits réel**")
    st.markdown(
        "Le catalogue d'articles (246 références) et la structure four/ligne ont été reconstruits "
        "à partir de **3 fichiers réels transmis par SEVAM** (extraits ERP au format .xlsm) :\n\n"
        "- *F.P.A.S POT DELICIA 37* (et sa version corrigée) : fiche de production réelle de "
        "l'article « POT DELICIA 37 » (client CONSERV.MAROC DOHA), et surtout la feuille "
        "**« BD des changements »** — le vrai journal de production SEVAM (2308 lignes, 2013-2024) "
        "avec OF réels, rendement, cadence, poids moyen et temps d'arrêt.\n"
        "- *Planner Gobeleterie 2026* : catalogue réel des verres nus (34 articles) et des articles "
        "**décorés/personnalisés** (39 articles, dont les marques Shell, TotalEnergies, Carte Noire, "
        "Nescafé, Butagaz identifiées dans les libellés), avec stocks par zone.\n\n"
        "**207 des 246 articles du catalogue sont réels** (source `\"reel\"` dans `catalogue_sevam.py`) ; "
        "39 ont été ajoutés par l'étudiante pour élargir le choix disponible dans le formulaire, en "
        "conservant le style de nommage SEVAM — ils sont identifiés `source=\"genere\"` et clairement "
        "séparables des données réelles."
    )

    st.markdown("**3. Parc industriel et correction de la codification des lignes**")
    st.markdown(
        "- **U1** (Roches Noires, le plus ancien) — département **Gobeleterie**, verres à thé/café/jus.\n"
        "- **U2, U3, U4** (Tit Mellil) — département **Verre creux**, bouteilles/pots/bocaux.\n\n"
        "Le journal réel « BD des changements » a permis de corriger la codification des lignes : "
        "**U2 → L11/L12/L13** et **U3 → L21/L22/L23** (observées sur 2308 lignes réelles), et non "
        "« Lx-du-four » comme initialement supposé. U1 et U4 n'apparaissant pas dans ce fichier "
        "(POT DELICIA n'y est pas fabriqué), leur codification (**U1 → L01/L02/L03**, "
        "**U4 → L31/L32/L33**) prolonge la même logique observée et reste **à vérifier auprès de "
        "SEVAM** avant tout usage hors cadre pédagogique."
    )

    st.markdown("**4. L'atelier Décor**")
    st.markdown(
        "Confirmé par l'entreprise : la personnalisation est un **atelier unique et transverse**, "
        "en sortie de four, quel que soit le four d'origine — il n'existe pas de four dédié au décor. "
        "Il est donc modélisé comme un attribut de l'article (`decore`, `marque`) plutôt que comme "
        "une ligne de production supplémentaire, avec un code cause dédié (« DECOR ») pour les "
        "incidents propres à cette étape (casse, défaut d'impression)."
    )

    st.markdown("**5. Accès différencié par rôle**")
    st.markdown(
        "Quatre rôles sont simulés via le sélecteur en haut de la barre latérale, chacun avec un "
        "périmètre de données et un jeu d'onglets adaptés :\n\n"
        "- **Opérateur** : voit uniquement la saisie, restreinte à sa ligne, et un résumé simplifié "
        "de sa propre performance (pas de coûts consolidés, pas de vue des autres lignes).\n"
        "- **Chef de service** : pilote un four (toutes ses lignes) — saisie + tableau de bord QCD/Pareto.\n"
        "- **Chef de département** : pilote un département (Gobeleterie, Verre creux ou Décor) — "
        "accès en plus à l'impact économique de son département.\n"
        "- **Directeur Général** : accès complet à tous les départements, toutes les lignes, "
        "tous les coûts, avec une vue comparative inter-départements réservée à ce rôle.\n\n"
        "⚠️ Il s'agit d'une **démonstration de principe** (un simple sélecteur de rôle dans la "
        "barre latérale) : aucune authentification réelle n'est implémentée dans ce prototype."
    )

    st.markdown("**6. Cohérence avec le rapport PFA**")
    st.markdown(
        "- Les champs du formulaire reprennent ceux de la fiche du chapitre 5, enrichis du champ Décor.\n"
        "- Le graphique Pareto formalise numériquement le vote pondéré des causes du chapitre 4.\n"
        "- L'intégration à l'ERP JD Edwards et à Qlik Sense reprend la piste d'amélioration du rapport."
    )

    st.markdown("**7. Limites assumées de ce prototype**")
    st.markdown(
        "- Les déclarations affichées par défaut restent des **données de démonstration** générées "
        "(quantités, dates, causes) — seuls les **noms d'articles, les marques et la structure "
        "four/ligne U2/U3** sont directement issus des fichiers réels.\n"
        "- Pas de base de données persistante ni d'authentification réelle (voir point 5).\n"
        "- Le coût unitaire est un paramètre à ajuster, pas une donnée validée par le contrôle de gestion.\n"
        "- La codification des lignes de U1 et U4 est une extrapolation à confirmer avec SEVAM."
    )

    st.markdown("**8. Pistes d'évolution vers un outil de production**")
    st.markdown(
        "- Connexion réelle à l'ERP JD Edwards et authentification SSO par rôle (Active Directory).\n"
        "- Base de données persistante (ex. SQL Server déjà utilisé par SEVAM).\n"
        "- Traçabilité fine des déclarations (qui a saisi, quand, depuis quel poste).\n"
        "- Publication automatique vers Qlik Sense via connecteur API, avec des vues déjà filtrées "
        "par rôle comme dans ce prototype."
    )

    st.write("")
    st.markdown(
        f"<div style='padding:12px 16px;background:{WHITE};border:1px solid #E7DFD5;border-left:4px solid {SEVAM_GREEN};border-radius:6px;font-size:12.5px;color:{GREY_TEXT};'>"
        f"Prototype développé en Python — PFA « Diagnostic des écarts de production, SEVAM » — 2026. "
        f"Catalogue et structure four/ligne construits à partir de fichiers réels transmis par l'entreprise."
        f"</div>",
        unsafe_allow_html=True,
    )

st.write("")
st.caption(
    "Prototype de démonstration — l'intégration réelle se ferait dans l'ERP JD Edwards, "
    "avec alimentation automatique de la plateforme Qlik Sense, comme décrit au chapitre 5 du rapport PFA."
)
