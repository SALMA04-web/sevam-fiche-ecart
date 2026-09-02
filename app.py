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
import hashlib
import os
from datetime import date, datetime

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
SITES = cat.SITES
ANNUAIRE_REEL = cat.ANNUAIRE_REEL
OF_CONFIRMES = cat.OF_CONFIRMES

# Lignes triées en mettant Tit Mellil (site principal de la stagiaire) en avant,
# sans jamais masquer Roches Noires.
LIGNES_TIT_MELLIL_DABORD = (
    [c for c, f in LIGNES if FOURS[f]["site"] == "Tit Mellil"]
    + [c for c, f in LIGNES if FOURS[f]["site"] == "Roches Noires"]
)
FOURS_TIT_MELLIL_DABORD = (
    [f for f in FOURS if FOURS[f]["site"] == "Tit Mellil"]
    + [f for f in FOURS if FOURS[f]["site"] == "Roches Noires"]
)


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


def filtrer_par_perimetre(df, auth):
    """Restreint un DataFrame au périmètre réellement accessible au compte connecté.

    Le périmètre est déterminé par scope_type/scope_value (dérivés automatiquement
    du poste, à la connexion) plutôt que par un simple choix manuel de rôle+scope :
      - "ligne" : une ligne précise (Opérateur)
      - "four"  : un four et ses lignes (ex. Abderrahim BELKHDIM -> Four 2)
      - "site"  : tous les fours d'un site (ex. Tit Mellil = U2+U3+U4)
      - "dept"  : un département (Gobeleterie / Verre creux / Décor)
      - "all"   : aucune restriction (Direction, Contrôle de gestion)
    """
    if df.empty or auth is None:
        return df
    stype, sval = auth["scope_type"], auth["scope_value"]
    if stype == "all":
        return df
    if stype == "ligne":
        return df[df["Ligne"] == sval]
    if stype == "four":
        return df[df["Four"] == sval]
    if stype == "site":
        return df[df["Site"] == sval]
    if stype == "dept":
        if sval == "Décor":
            return df[df["Decore"] == "OUI"]
        return df[df["Departement"] == sval]
    return df


def filtrer_of_confirmes(of_list, auth):
    """Restreint la base des OF confirmés au même périmètre que filtrer_par_perimetre."""
    if auth is None:
        return of_list
    stype, sval = auth["scope_type"], auth["scope_value"]
    if stype == "all":
        return of_list
    if stype == "ligne":
        return [o for o in of_list if o["ligne"] == sval]
    if stype == "four":
        return [o for o in of_list if o["four"] == sval]
    if stype == "site":
        return [o for o in of_list if o["site"] == sval]
    if stype == "dept":
        if sval == "Décor":
            return [o for o in of_list if o["decore"]]
        deps_ok = {sval}
        return [o for o in of_list if FOURS[o["four"]]["departement"] in deps_ok or (sval == "Décor" and o["decore"])]
    return of_list


# =========================================================
# CONNEXION — nom + poste (annuaire réel SEVAM), plutôt qu'un simple sélecteur
# =========================================================
if "auth" not in st.session_state:
    st.session_state.auth = None

if st.session_state.auth is None:
    c_left, c_mid, c_right = st.columns([1, 1.3, 1])
    with c_mid:
        st.write("")
        st.write("")
        if LOGO_B64:
            st.markdown(
                f"<div style='text-align:center;'><img src='data:image/png;base64,{LOGO_B64}' "
                f"style='max-width:260px;height:auto;'/></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<h3 style='text-align:center;color:{SEVAM_RED_DARK};margin-top:6px;'>Connexion — "
            f"Fiche de déclaration d'écart</h3>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Identification par nom et poste, comme le ferait un accès réel adossé à l'annuaire "
            "SEVAM / à l'ERP JD Edwards (SSO). Voir l'onglet Méthodologie une fois connecté pour le détail."
        )

        noms_annuaire = [p["nom"] for p in ANNUAIRE_REEL]
        AUTRE = "Autre — opérateur / poste non listé dans l'annuaire"
        choix_nom = st.selectbox("Nom", options=noms_annuaire + [AUTRE])

        if choix_nom != AUTRE:
            fiche = next(p for p in ANNUAIRE_REEL if p["nom"] == choix_nom)
            st.text_input("Poste (rempli automatiquement depuis l'annuaire)", value=fiche["poste"], disabled=True)
            st.caption(f"🗂️ Source : {fiche['note']}")
            nom_final, poste_final = fiche["nom"], fiche["poste"]
            tier_final, stype_final, sval_final = fiche["tier"], fiche["scope_type"], fiche["scope_value"]
        else:
            nom_final = st.text_input("Nom et prénom", placeholder="ex. Karim Benali")
            postes_operateur = [(f"Opérateur — {LIGNE_LABELS[c]}", "Opérateur", "ligne", c) for c in LIGNES_TIT_MELLIL_DABORD]
            postes_chef_four = [
                (lbl, "Chef de service", "four", four)
                for four, lbl in cat.POSTES_FOUR_NON_CONFIRMES.items()
            ]
            options_poste = postes_operateur + postes_chef_four
            choix_poste = st.selectbox(
                "Poste", options=range(len(options_poste)),
                format_func=lambda i: options_poste[i][0],
            )
            poste_final, tier_final, stype_final, sval_final = options_poste[choix_poste]
            if stype_final == "four":
                st.caption(
                    "⚠️ Aucun nom réel confirmé pour ce poste dans les documents transmis par "
                    "SEVAM (seul le Four 2 a un signataire réel sur la fiche de validation "
                    "disponible) — poste affiché tel quel, sans nom inventé."
                )

        st.write("")
        connecte = st.button("Se connecter", type="primary", use_container_width=True)
        if connecte:
            if not nom_final:
                st.error("Merci de renseigner un nom.")
            else:
                jeton = hashlib.sha256(f"{nom_final}-{datetime.now().isoformat()}".encode()).hexdigest()[:10].upper()
                st.session_state.auth = {
                    "nom": nom_final, "poste": poste_final, "tier": tier_final,
                    "scope_type": stype_final, "scope_value": sval_final,
                    "login_time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "session_token": jeton,
                }
                st.rerun()
    st.stop()

auth = st.session_state.auth
role = auth["tier"]

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

    # Libellé du périmètre, dérivé de auth (scope_type/scope_value)
    _stype, _sval = auth["scope_type"], auth["scope_value"]
    if _stype == "ligne":
        scope_label = LIGNE_LABELS[_sval]
    elif _stype == "four":
        scope_label = f"Four {_sval} ({FOURS[_sval]['site']})"
    elif _stype == "site":
        scope_label = f"Site {_sval} (fours {', '.join(SITES[_sval])})"
    elif _stype == "dept":
        scope_label = f"Département {_sval}"
    else:
        scope_label = "Tous les sites, tous les départements"

    st.write("")
    st.markdown("**Session**")
    st.markdown(
        f"<div style='padding:10px 12px;background:#EEF2F9;border-left:4px solid {BLUE_ROLE};"
        f"border-radius:4px;font-size:12.5px;color:{GREY_TEXT};'>"
        f"👤 <b>{auth['nom']}</b><br>{auth['poste']}<br>"
        f"Périmètre : <b>{scope_label}</b><br>"
        f"<span style='font-size:11px;color:#8892A0;'>Connecté le {auth['login_time']} · "
        f"jeton de session {auth['session_token']}</span></div>",
        unsafe_allow_html=True,
    )
    if st.button("Se déconnecter", use_container_width=True):
        st.session_state.auth = None
        st.rerun()
    st.caption(
        "Connexion par nom + poste, adossée à l'annuaire réel SEVAM (fiche de validation avant "
        "lancement). Il ne s'agit pas d'une authentification réelle (pas de mot de passe / SSO) "
        "— voir l'onglet Méthodologie pour le détail et les limites."
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
    _df_scope = filtrer_par_perimetre(st.session_state.declarations, auth)
    if not _df_scope.empty:
        st.metric("OF suivis", int(_df_scope["N_OF"].nunique()))
        st.metric("Taux de service", f"{(_df_scope['Qte_Realisee'].sum()/_df_scope['Qte_Planifiee'].sum()*100):.1f}%")

    st.write("")
    with st.expander("🏭 Parc de fours SEVAM — Tit Mellil en priorité"):
        st.caption(f"📍 Site principal de la stagiaire : **{cat.SITE_PRINCIPAL}**")
        for code in FOURS_TIT_MELLIL_DABORD:
            info = FOURS[code]
            st.caption(f"**{code}** — {info['site']} · {info['departement']} · {info['statut']}")
        st.caption(
            "Codification des lignes L11/L12/L13 (four U2) et L21/L22/L23 (four U3) confirmée "
            "par le journal de production réel de l'entreprise. Celle de U1 et U4 prolonge la "
            "même logique et reste à vérifier auprès de SEVAM (voir Méthodologie)."
        )

    with st.expander("ℹ️ À propos de ce prototype"):
        st.caption(
            "Développé en Python (Streamlit, Pandas, Plotly) dans le cadre du PFA "
            "« Diagnostic des écarts de production — SEVAM ». Catalogue produit, structure "
            "four/ligne, annuaire des accès et base d'OF confirmés reconstruits à partir de "
            "fichiers réels transmis par l'entreprise."
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
            👤 <b>{auth['nom']}</b><br><span style="font-size:11.5px;">{auth['poste']}</span><br>
            <span style="font-size:11px;opacity:0.85;">{scope_label}</span>
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

        if auth["scope_type"] == "ligne":
            lignes_possibles = [auth["scope_value"]]
        elif auth["scope_type"] == "four":
            lignes_possibles = lignes_du_four(auth["scope_value"])
        elif auth["scope_type"] == "site":
            fours_site = SITES[auth["scope_value"]]
            lignes_possibles = [code for code, four in LIGNES if four in fours_site]
        elif auth["scope_type"] == "dept":
            if auth["scope_value"] == "Décor":
                lignes_possibles = [code for code, _ in LIGNES]
            else:
                fours_dep = fours_du_departement(auth["scope_value"])
                lignes_possibles = [code for code, four in LIGNES if four in fours_dep]
        else:
            lignes_possibles = LIGNES_TIT_MELLIL_DABORD

        of_dispo = filtrer_of_confirmes(OF_CONFIRMES, auth)
        of_dispo = [o for o in of_dispo if o["ligne"] in lignes_possibles]

        mode_saisie = st.radio(
            "Mode de saisie",
            options=["🔎 OF confirmé (base ERP du jour)", "✍️ Saisie manuelle (OF hors liste)"],
            horizontal=True,
            help="La base d'OF confirmés reprend les OF déjà planifiés — plus besoin de retaper "
                 "l'article, la ligne et la quantité planifiée à chaque déclaration.",
        )

        mode_of = mode_saisie.startswith("🔎")

        if mode_of and not of_dispo:
            st.warning(
                "Aucun OF confirmé disponible sur votre périmètre pour l'instant — bascule "
                "automatique en saisie manuelle."
            )
            mode_of = False

        if mode_of:
            # ---- Mode 1 : sélection d'un OF déjà confirmé (base ERP du jour) ----
            of_sel_idx = st.selectbox(
                "OF confirmé à déclarer", options=range(len(of_dispo)),
                format_func=lambda i: (
                    f"{of_dispo[i]['n_of']} — {of_dispo[i]['client']} — {of_dispo[i]['article']} "
                    f"({LIGNE_LABELS[of_dispo[i]['ligne']]})"
                ),
            )
            of_sel = of_dispo[of_sel_idx]
            art_rec = {
                "article": of_sel["article"], "famille": of_sel["famille"],
                "decore": of_sel["decore"], "marque": of_sel["marque"],
            }
            n_of, ligne_choice, four_sel = of_sel["n_of"], of_sel["ligne"], of_sel["four"]
            dep_sel = FOURS[four_sel]["departement"]
            qte_plan = of_sel["qte_planifiee"]
            d_defaut = of_sel["date"]

            badge_source = "🟢 donnée réelle (recoupée entre deux fichiers SEVAM)" if of_sel["source"] == "reel" else "🟡 OF de démonstration (élargissement de la base)"
            st.markdown(
                f"<div style='padding:10px 14px;border-left:4px solid {BLUE_ROLE};background:#F5F8FC;border-radius:4px;font-size:13px;'>"
                f"<b>{n_of}</b> — Client : <b>{of_sel['client']}</b><br>"
                f"Article : <b>{art_rec['article']}</b>{' 🎨 (décor — ' + (art_rec['marque'] or 'personnalisation générique') + ')' if art_rec['decore'] else ''}<br>"
                f"Ligne / Four : <b>{LIGNE_LABELS[ligne_choice]}</b> · Site : <b>{FOURS[four_sel]['site']}</b><br>"
                f"Quantité planifiée : <b>{qte_plan:,}</b> unités · Date prévue : <b>{d_defaut.strftime('%d/%m/%Y')}</b><br>"
                f"<span style='font-size:11px;color:#8892A0;'>{badge_source} — {of_sel['source_detail']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with st.form("form_declaration", clear_on_submit=not mode_of):
            if mode_of:
                c1, c2 = st.columns(2)
                with c1:
                    d = st.date_input("Date de déclaration", value=of_sel["date"])
                with c2:
                    qte_real = st.number_input("Quantité réalisée", min_value=0, value=int(qte_plan * 0.92), step=100)
            else:
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
            declare_par = st.text_input("Déclaré par", value=auth["nom"], disabled=True)

            if not mode_of and art_rec["decore"]:
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
        df_perimetre = filtrer_par_perimetre(st.session_state.declarations, auth)
        st.caption(f"{len(df_perimetre)} déclarations visibles dans votre périmètre ({role} — {scope_label}).")
        st.dataframe(
            df_perimetre.sort_values("Date", ascending=False).head(15),
            use_container_width=True, hide_index=True,
        )

        if role == "Opérateur" and not df_perimetre.empty:
            st.write("")
            st.markdown("**Votre performance récente (" + scope_label + ")**")
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
        df = filtrer_par_perimetre(st.session_state.declarations, auth).copy()
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
        df = filtrer_par_perimetre(st.session_state.declarations, auth).copy()
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

    st.markdown("**5. Connexion par nom + poste, adossée à un vrai annuaire SEVAM**")
    st.markdown(
        "La page de connexion demande un **nom** et affiche automatiquement le **poste** associé, "
        "plutôt qu'un simple sélecteur de rôle : le périmètre de données (tier + scope) est déduit "
        "du poste, comme le ferait un annuaire d'entreprise réel (Active Directory / SSO).\n\n"
        "Les 10 postes proposés dans l'annuaire proviennent tous de personnes et fonctions **réelles**, "
        "identifiées sur la **fiche de validation avant lancement** transmise par SEVAM "
        "(réf. FN-PR-121-05-V.00, client SACOFRINA SA, article APO 33 CL VA SACO, ligne L-23, site "
        "de Tit Mellil — Figure 3.4 du rapport) :\n\n"
        "- Adnane RAFIK — Chef Service Supply Chain\n"
        "- Youssef HAFFOU — Chef Département Supply Chain\n"
        "- Fatima Zahra AOUAB — Chef Département SMI\n"
        "- Abderrahim BELKHDIM — Chef Département Production, Four 2 (U2)\n"
        "- Abderrahim ZNIDI — Chef Département Qualité Process\n"
        "- Asmaa KDAH — Chef Département Contrôle de Gestion\n"
        "- Abderrahim EL ABBADI — Directeur Exploitation\n"
        "- Hassan TAHRI — Directeur Commercial & Marketing\n"
        "- Bouchra SNAIBI — Directeur Administratif et Financier\n"
        "- Karim AMMAR — Directeur Général Délégué\n\n"
        "⚠️ Seul le Four 2 a un signataire réel confirmé sur la fiche disponible : les postes "
        "« Chef Département Production » des Fours 1, 3 et 4 sont donc proposés dans l'option "
        "« Autre » du formulaire de connexion, sans nom inventé, avec la mention explicite "
        "« nom à confirmer »."
    )

    st.markdown("**6. Périmètre de données par poste (scope)**")
    st.markdown(
        "Le périmètre visible (tableau de bord, Pareto, impact économique, base d'OF confirmés) est "
        "calculé automatiquement selon le type de poste :\n\n"
        "- **Ligne** (opérateurs) : uniquement leur ligne.\n"
        "- **Four** (ex. Abderrahim BELKHDIM) : le four et ses 3 lignes.\n"
        "- **Site** (ex. Adnane RAFIK, Youssef HAFFOU, Fatima Zahra AOUAB, Abderrahim ZNIDI — postes "
        "Supply Chain / SMI / Qualité process) : tous les fours d'un site — **Tit Mellil (U2+U3+U4) "
        "ou Roches Noires (U1)** — puisque ces fonctions supervisent un site entier, pas un seul four.\n"
        "- **Département** : un département (Gobeleterie, Verre creux ou Décor).\n"
        "- **Tous les sites** (Contrôle de Gestion, Directions) : aucune restriction.\n\n"
        "⚠️ Il s'agit d'une **démonstration de principe** : le nom et le poste sont déclaratifs (pas "
        "de mot de passe, pas de vérification d'identité) — voir le point 9 pour l'évolution vers une "
        "authentification réelle."
    )

    st.markdown("**7. Site principal mis en avant : Tit Mellil**")
    st.markdown(
        "La stagiaire étant affectée au site de **Tit Mellil** (fours U2, U3, U4 — département Verre "
        "creux), l'interface met ce site en avant par défaut sans masquer Roches Noires (U1, "
        "Gobeleterie) : listes de lignes/fours triées avec Tit Mellil en premier, base d'OF confirmés "
        "élargie majoritairement sur Tit Mellil (2/3 des OF générés), et rappel du site principal dans "
        "l'expander « Parc de fours SEVAM »."
    )

    st.markdown("**8. Base d'OF confirmés — fin de la ressaisie manuelle**")
    st.markdown(
        "Besoin exprimé par l'entreprise : ne pas retaper article, ligne et quantité planifiée à "
        "chaque déclaration alors que l'OF est déjà confirmé côté planification. L'onglet Saisie "
        "propose donc deux modes :\n\n"
        "- **🔎 OF confirmé** (par défaut) : sélection dans une base d'OF déjà planifiés — l'article, "
        "le décor/la marque, la ligne/le four et la quantité planifiée se remplissent automatiquement ; "
        "il ne reste qu'à saisir la quantité réalisée et la cause d'écart.\n"
        "- **✍️ Saisie manuelle** : conservée pour les OF hors liste (formulaire d'origine).\n\n"
        f"La base contient **{len(cat.OF_CONFIRMES)} OF**, dont **{sum(1 for o in cat.OF_CONFIRMES if o['source']=='reel')} "
        "construits à partir de correspondances réelles vérifiables** entre deux sources transmises "
        "par SEVAM : la fiche de validation avant lancement (client SACOFRINA SA) et le fichier "
        "**« Copie de Suivi BC.xlsx »** (suivi des commandes clients 2026), recoupés avec les libellés "
        "exacts du catalogue produit (ex. AIN SAISS 75/50/33 CL / SOTHERMA, TROPICANA 1 L VB / JAD "
        "DISTRIBUTION, BLLE EAU DE ROSE 1L AVIS VV / FLEUR ATLAS BELAAMRI, OULMES FRUITE 25 VIS BAGUE "
        "EMO / LES EAUX MINERALES D'OULMES, BORDELAISE 500 VB ALMA RWS / ROSLANE WINE & SPIRITS — le "
        "suffixe RWS de l'article correspond au vrai client). Chaque OF affiche sa provenance "
        "(🟢 réel / 🟡 démonstration) directement dans le formulaire de saisie, dans la même logique "
        "de transparence que le champ `source` du catalogue produit."
    )

    st.markdown("**9. Cohérence avec le rapport PFA**")
    st.markdown(
        "- Les champs du formulaire reprennent ceux de la fiche du chapitre 5, enrichis du champ Décor.\n"
        "- Le graphique Pareto formalise numériquement le vote pondéré des causes du chapitre 4.\n"
        "- L'intégration à l'ERP JD Edwards et à Qlik Sense reprend la piste d'amélioration du rapport."
    )

    st.markdown("**10. Limites assumées de ce prototype**")
    st.markdown(
        "- Les déclarations affichées par défaut restent des **données de démonstration** générées "
        "(quantités réalisées, causes) — les **noms d'articles, les marques, la structure four/ligne "
        "U2/U3, l'annuaire des postes et une partie des OF confirmés** sont directement issus de "
        "fichiers réels transmis par l'entreprise.\n"
        "- Pas de base de données persistante ni d'authentification réelle (nom/poste déclaratifs, "
        "sans mot de passe ni vérification d'identité — voir points 5 et 6).\n"
        "- Le coût unitaire est un paramètre à ajuster, pas une donnée validée par le contrôle de gestion.\n"
        "- La codification des lignes de U1 et U4, et les noms des chefs Four 1/3/4, sont à confirmer "
        "avec SEVAM.\n"
        "- Les couples client/article des OF « démonstration » (🟡) sont illustratifs, pas garantis réels."
    )

    st.markdown("**11. Pistes d'évolution vers un outil de production**")
    st.markdown(
        "- Authentification réelle (mot de passe, SSO Active Directory) derrière l'écran de connexion "
        "nom + poste déjà en place dans ce prototype.\n"
        "- Base de données persistante (ex. SQL Server déjà utilisé par SEVAM) pour les déclarations "
        "et la base d'OF confirmés, alimentée automatiquement par l'ERP JD Edwards.\n"
        "- Traçabilité fine des déclarations (qui a saisi, quand, depuis quel poste) — déjà esquissée "
        "par le jeton de session affiché dans la barre latérale.\n"
        "- Publication automatique vers Qlik Sense via connecteur API, avec des vues déjà filtrées "
        "par poste comme dans ce prototype."
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
