"""
Plateforme numérique SEVAM — Suivi des écarts de production & Maintenance
===========================================================================
Preuve de concept d'une saisie numérique de la fiche de déclaration d'écart
(chapitre 5 du rapport PFA), enrichie du suivi de fiabilité et de maintenance
du Four U2 (chapitre 6.2.4/6.2.5 : historique des pannes, MTBF/MTTR/
disponibilité, analyse 5M/5S, criticité AMDEC et simulateur d'incident), qui
alimenterait automatiquement un pilotage type Qlik Sense en remplacement de
la saisie papier actuelle.

Version 5 — ajoute un onglet d'accueil expliquant le périmètre de la
plateforme (retour du professeur encadrant : la page d'entrée ne permettait
pas de comprendre immédiatement de quoi il s'agissait), et un module complet
"Maintenance Four U2" (voir maintenance_sevam.py) déployant l'historique des
pannes, la fiabilité recalculée en direct, l'analyse des causes, la grille
AMDEC et un simulateur d'incident pas à pas ("un problème survient sur le
four, comment procède-t-on ?").

Catalogue produits et structure four/ligne reconstruits à partir de 3
fichiers réels transmis par SEVAM (voir catalogue_sevam.py pour le détail des
sources), atelier Décor modélisé comme un atelier transverse (pas de four
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
import io
import os
import re
import uuid
from datetime import date, datetime
from threading import Lock

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import catalogue_sevam as cat
import maintenance_sevam as maint

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

# Nombre de lignes de démarrage (données de base) : sert à savoir combien de
# déclarations ont été ajoutées PAR L'UTILISATEUR pendant cette session, pour
# ne jamais permettre d'annuler autre chose qu'une saisie qu'il vient de faire.
# Initialisé À PART (et pas seulement dans le bloc ci-dessus) : sur Streamlit
# Cloud, un redéploiement peut réutiliser une session déjà ouverte avant la
# mise à jour de l'application, où "declarations" existe déjà mais pas encore
# cette clé — sans quoi le bouton "Annuler" plantait avec un AttributeError.
if "declarations_len_initial" not in st.session_state:
    st.session_state.declarations_len_initial = len(st.session_state.declarations)

# Incidents Four U2 enregistrés depuis le simulateur d'incident (module Maintenance) —
# permettent de recalculer le MTBF/MTTR/disponibilité "en direct" en y intégrant les
# scénarios simulés par l'utilisateur, en plus des 14 pannes historisées.
if "incidents_simules" not in st.session_state:
    st.session_state.incidents_simules = []
if "sim_step_idx" not in st.session_state:
    st.session_state.sim_step_idx = 0
if "sim_organe_nom" not in st.session_state:
    st.session_state.sim_organe_nom = maint.AMDEC_ORGANES[1]["organe"]  # "Brûleurs" par défaut
if "sim_ligne" not in st.session_state:
    st.session_state.sim_ligne = maint.LIGNES_U2[0]

# =========================================================
# ÉTAT PARTAGÉ ENTRE TOUTES LES SESSIONS (flux d'activité temps réel)
# =========================================================
# st.session_state est propre à CHAQUE navigateur/onglet connecté : deux
# utilisateurs ne peuvent pas s'y voir l'un l'autre. st.cache_resource, lui,
# renvoie le MÊME objet Python à toutes les sessions tant que le processus
# Streamlit tourne — c'est le mécanisme officiellement recommandé pour de
# l'état partagé (voir doc Streamlit "Mutate a cached object"). On l'utilise
# ici pour que la déclaration d'un OF par une personne soit visible, en
# quelques secondes, par toutes les autres personnes connectées — sans base
# de données externe.
@st.cache_resource
def _shared_store():
    return {"feed": [], "next_id": 1, "presence": {}, "lock": Lock()}


SHARED = _shared_store()

# Identifiant stable pour CETTE session (un onglet/navigateur = un sid), pour
# savoir qui est "en ligne" et ne pas notifier une personne de ses propres
# actions.
if "sid" not in st.session_state:
    st.session_state.sid = uuid.uuid4().hex[:12]


def log_event(message, level="info", auteur=None):
    """Publie un événement dans le flux d'activité PARTAGÉ, visible par tous les
    postes connectés (Centre d'alertes de l'onglet Accueil), en quasi temps réel
    grâce à l'auto-rafraîchissement de la page."""
    with SHARED["lock"]:
        evt_id = SHARED["next_id"]
        SHARED["next_id"] += 1
        SHARED["feed"].insert(0, {
            "id": evt_id, "ts": datetime.now(), "message": message,
            "level": level, "auteur": auteur,
        })
        del SHARED["feed"][50:]
    return evt_id


NIVEAU_STYLE = {
    "critical": ("🚨", SEVAM_RED, "#FDECEA"),
    "warning": ("⚠️", AMBER, "#FBF3E0"),
    "success": ("✅", SEVAM_GREEN_DARK, "#EAF5EC"),
    "info": ("ℹ️", BLUE_ROLE, "#EEF2F9"),
}


def render_alert(level, text):
    icon, border_color, bg = NIVEAU_STYLE.get(level, NIVEAU_STYLE["info"])
    st.markdown(
        f"<div style='padding:10px 14px;border-left:4px solid {border_color};background:{bg};"
        f"border-radius:4px;margin-bottom:8px;font-size:13px;color:{GREY_TEXT};'>"
        f"{icon} {text}</div>",
        unsafe_allow_html=True,
    )


def temps_ecoule(ts):
    delta = datetime.now() - ts
    secondes = int(delta.total_seconds())
    if secondes < 60:
        return "à l'instant"
    minutes = secondes // 60
    if minutes < 60:
        return f"il y a {minutes} min"
    heures = minutes // 60
    return f"il y a {heures} h"


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


def scope_couvre_four(auth, four_code):
    """Indique si le périmètre d'un compte couvre un four donné (ex. U2) — utilisé
    pour décider si l'onglet Maintenance Four U2 doit être proposé à ce poste."""
    stype, sval = auth["scope_type"], auth["scope_value"]
    if stype == "all":
        return True
    if stype == "four":
        return sval == four_code
    if stype == "site":
        return four_code in SITES.get(sval, [])
    if stype == "dept":
        if sval == "Décor":
            return False
        return four_code in DEPARTEMENTS.get(sval, {}).get("fours", [])
    if stype == "ligne":
        return dict(LIGNES).get(sval) == four_code
    return False


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
    st.markdown(
        f"""
        <div style="background:linear-gradient(90deg, {SEVAM_RED_DARK} 0%, {SEVAM_RED} 100%);
                    padding:22px 28px;border-radius:8px;border-bottom:4px solid {SEVAM_GREEN};margin-bottom:22px;">
            <h1 style="color:white;margin:0;font-size:27px;">🏭 Plateforme numérique SEVAM — Suivi des
            écarts de production &amp; Maintenance</h1>
            <p style="color:#FBEAE8;margin:8px 0 0 0;font-size:14.5px;max-width:900px;">
            Prototype réalisé dans le cadre du PFA « Diagnostic des écarts de production et pilotage
            de la maintenance », en remplacement de la saisie papier et des historiques reconstitués
            manuellement décrits aux chapitres 5 et 6 du rapport.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_left, c_right = st.columns([1.35, 1])

    with c_left:
        st.markdown("#### Que trouve-t-on sur cette plateforme ?")
        st.markdown(
            "Elle numérise **deux livrables complémentaires** du PFA, présentés dans les onglets "
            "correspondants une fois connecté :"
        )
        st.markdown(
            f"""
            <div style="display:flex;flex-direction:column;gap:10px;margin:10px 0 18px 0;">
              <div style="padding:12px 14px;background:{WHITE};border:1px solid #E7DFD5;border-left:4px solid {SEVAM_RED};border-radius:6px;">
                <b>📝 Déclaration numérique des écarts de production</b> — chapitre 5<br>
                <span style="font-size:12.5px;color:{GREY_TEXT};">Saisie d'une déclaration d'écart (OF, quantités,
                cause), pilotage QCD et analyse Pareto des causes, impact économique chiffré — remplace la fiche
                papier actuelle et alimenterait automatiquement un pilotage type Qlik Sense.</span>
              </div>
              <div style="padding:12px 14px;background:{WHITE};border:1px solid #E7DFD5;border-left:4px solid {SEVAM_GREEN_DARK};border-radius:6px;">
                <b>🛠️ Fiabilité et maintenance du Four U2</b> — chapitre 6.2.4 / 6.2.5<br>
                <span style="font-size:12.5px;color:{GREY_TEXT};">Historique détaillé de 14 pannes réelles,
                MTBF/MTTR/disponibilité recalculés en direct, analyse des causes (5M/5S/5 Pourquoi), grille de
                criticité AMDEC des organes du four, et un <b>simulateur d'incident</b> qui rejoue pas à pas la
                procédure de traitement d'une panne, de la détection à la clôture.</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### Comment ça marche ?")
        st.markdown(
            "Connectez-vous avec un **nom de l'annuaire réel SEVAM** (panneau de droite) : la "
            "plateforme adapte automatiquement l'affichage et le périmètre de données visible à ce "
            "poste — un opérateur ne voit que sa ligne, un chef de service son four, un chef de "
            "département son département, la Direction Générale l'ensemble des sites. Aucune "
            "authentification réelle n'est requise (démonstration de principe) ; le détail est "
            "expliqué dans l'onglet Méthodologie une fois connecté."
        )
        st.caption(
            f"246 articles catalogués · 4 fours (U1 à U4) · 14 pannes historisées et 9 organes "
            f"analysés (AMDEC) sur le Four U2 · "
            f"{sum(1 for p in cat.ANNUAIRE_REEL if p['source'] == 'reel')} postes réels dans l'annuaire."
        )

    with c_right:
        st.write("")
        if LOGO_B64:
            st.markdown(
                f"<div style='text-align:center;'><img src='data:image/png;base64,{LOGO_B64}' "
                f"style='max-width:220px;height:auto;'/></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<h3 style='text-align:center;color:{SEVAM_RED_DARK};margin-top:6px;'>Connexion</h3>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Identification par nom et poste, comme le ferait un accès réel adossé à l'annuaire "
            "SEVAM / à l'ERP JD Edwards (SSO)."
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

# =========================================================
# TEMPS RÉEL — présence en ligne + auto-rafraîchissement
# =========================================================
# 1) Cette session "pointe" dans le registre partagé (on saura qui est
#    actuellement connecté), et on purge les postes inactifs depuis plus de
#    20 secondes (2 à 4 cycles d'auto-rafraîchissement manqués).
with SHARED["lock"]:
    SHARED["presence"][st.session_state.sid] = {"nom": auth["nom"], "poste": auth["poste"], "ts": datetime.now()}
    _cutoff = datetime.now()
    SHARED["presence"] = {
        sid: p for sid, p in SHARED["presence"].items() if (_cutoff - p["ts"]).total_seconds() < 20
    }

# 2) La page entière se relance automatiquement toutes les 5 secondes : c'est
#    ce qui permet à un poste resté ouvert, sans aucun clic, de voir apparaître
#    les déclarations faites entre-temps par d'autres postes connectés.
st_autorefresh(interval=5000, key="live_autorefresh")

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
    tab_names = ["🏠 Accueil", "📝 Saisie d'une déclaration", "📘 Méthodologie & note technique"]
elif role == "Chef de service":
    tab_names = ["🏠 Accueil", "📝 Saisie d'une déclaration", "📊 Pilotage QCD & Pareto", "📘 Méthodologie & note technique"]
else:  # Chef de département, DG
    tab_names = ["🏠 Accueil", "📝 Saisie d'une déclaration", "📊 Pilotage QCD & Pareto", "💰 Impact économique", "📘 Méthodologie & note technique"]

# Le module Maintenance ne porte que sur le Four U2 (seul four disposant d'un
# historique de pannes détaillé) : proposé aux postes non-opérateurs dont le
# périmètre couvre ce four, juste avant l'onglet Méthodologie.
montrer_maintenance = (role != "Opérateur") and scope_couvre_four(auth, "U2")
if montrer_maintenance:
    tab_names.insert(len(tab_names) - 1, "🛠️ Maintenance Four U2")

tabs = st.tabs(tab_names)
tab_map = dict(zip(tab_names, tabs))

TAB_DESCRIPTIONS = {
    "📝 Saisie d'une déclaration": "Déclarer un écart de production (OF, quantités, cause) — remplace la fiche papier.",
    "📊 Pilotage QCD & Pareto": "Suivre la Qualité, le Coût et le Délai des écarts, et leurs causes principales (Pareto).",
    "💰 Impact économique": "Traduire les écarts en coût estimé et simuler le gain d'un plan d'action.",
    "🛠️ Maintenance Four U2": "Historique des pannes, fiabilité (MTBF/MTTR), analyse des causes, AMDEC et simulateur d'incident.",
    "📘 Méthodologie & note technique": "Origine des données, limites assumées et pistes d'évolution — note à destination du jury.",
}

# =========================================================
# ONGLET — Accueil (vue d'ensemble de la plateforme)
# =========================================================
with tab_map["🏠 Accueil"]:
    st.markdown(f"#### Bienvenue, {auth['nom']}")
    st.markdown(
        "Cette plateforme numérise **deux livrables complémentaires** du PFA « Diagnostic des "
        "écarts de production et pilotage de la maintenance » : la **déclaration numérique des "
        "écarts** (chapitre 5, remplace la fiche papier) et le **suivi de fiabilité et de "
        "maintenance du Four U2** (chapitre 6.2, historique des pannes, MTBF/MTTR, AMDEC). "
        "L'affichage et le périmètre de données ci-dessous sont adaptés automatiquement à votre "
        f"poste : **{auth['poste']}** — périmètre **{scope_label}**."
    )

    # ---------------------------------------------------------------
    # Scénario de démonstration guidé : un enchaînement prêt à suivre pour la
    # soutenance, rédigé en phrases complètes pour ne rien avoir à improviser.
    # ---------------------------------------------------------------
    with st.expander("🎬 Scénario de démonstration suggéré (environ 5 minutes)"):
        st.markdown(
            "Cet enchaînement permet de montrer l'essentiel de la plateforme sans rien laisser "
            "au hasard devant le jury. Chaque étape peut être adaptée selon le temps disponible."
        )
        st.markdown(
            "**1. Présenter l'écran de connexion (30 secondes).** Expliquer que la connexion se "
            "fait par nom et poste, adossée au vrai annuaire SEVAM, et que le périmètre de "
            "données affiché ensuite dépend automatiquement du poste choisi — exactement comme "
            "le ferait un accès réel en entreprise.\n\n"
            "**2. Se connecter en tant qu'Adnane RAFIK et déclarer un OF (1 minute).** Aller dans "
            "l'onglet « 📝 Saisie d'une déclaration », choisir un OF confirmé dans la liste, "
            "modifier légèrement la quantité réalisée pour créer un écart visible, puis valider. "
            "Montrer que l'écart, le statut et l'impact économique estimé apparaissent "
            "immédiatement.\n\n"
            "**3. Ouvrir un second onglet du navigateur et se connecter avec un autre nom, par "
            "exemple Youssef HAFFOU (1 minute).** Revenir sur l'onglet Accueil : montrer le "
            "bandeau « 🟢 2 personne(s) connectée(s) » qui affiche les deux postes en direct — "
            "c'est le point qui démontre concrètement le fonctionnement en temps réel.\n\n"
            "**4. Depuis ce second onglet, déclarer un nouvel OF, puis revenir sur le premier "
            "onglet (1 minute).** Sans rien recharger manuellement, un message « toast » apparaît "
            "en bas de l'écran avec le nom du déclarant et l'écart constaté, et le flux "
            "d'activité de l'onglet Accueil se met à jour — la preuve que l'information circule "
            "réellement entre les postes connectés.\n\n"
            "**5. Ouvrir l'onglet « 📊 Pilotage QCD & Pareto » (1 minute).** Montrer l'analyse "
            "Pareto des causes d'écart et la règle des 80 %, puis l'onglet « 💰 Impact économique » "
            "pour traduire ces écarts en dirhams et simuler le gain d'un plan d'action.\n\n"
            "**6. Terminer sur l'onglet « 🛠️ Maintenance Four U2 » (1 minute, si le temps le "
            "permet).** Montrer rapidement le calcul de fiabilité (MTBF/MTTR), la grille de "
            "criticité AMDEC, et éventuellement lancer une étape du simulateur d'incident pour "
            "illustrer la procédure de traitement d'une panne de A à Z."
        )
        st.caption(
            "Astuce : garder ce panneau replié pendant la présentation et ne l'ouvrir qu'en "
            "préparation, juste avant de passer devant le jury."
        )

    # ---------------------------------------------------------------
    # Centre d'alertes : ce que l'utilisateur doit savoir AVANT d'aller
    # cliquer dans les onglets. Combine des alertes calculées en direct
    # (écarts, disponibilité Four U2, criticité AMDEC) et le journal des
    # événements de la session (déclarations traitées, incidents simulés).
    # ---------------------------------------------------------------
    _df_accueil = filtrer_par_perimetre(st.session_state.declarations, auth)

    _alertes = []
    if not _df_accueil.empty:
        _nb_ecart = int((_df_accueil["Ecart_Pct"].abs() > seuil_alerte).sum())
        if _nb_ecart > 0:
            _pire = _df_accueil.loc[_df_accueil["Ecart_Pct"].abs().idxmax()]
            _cout_total = _df_accueil.loc[_df_accueil["Ecart_Pct"].abs() > seuil_alerte, "Ecart_Unites"].abs().sum() * cout_unitaire
            _cout_total_fmt = f"{_cout_total:,.0f}".replace(",", " ")
            _alertes.append((
                "warning" if _nb_ecart < 3 else "critical",
                f"<b>{_nb_ecart} OF en écart</b> au-delà du seuil de vigilance ({seuil_alerte}%) dans votre "
                f"périmètre — cas le plus marqué : OF <b>{_pire['N_OF']}</b> ({_pire['Ecart_Pct']:+.1f}%). "
                f"Impact économique cumulé estimé à <b>{_cout_total_fmt} MAD</b>.",
            ))
        else:
            _alertes.append(("success", "Aucun OF au-delà du seuil de vigilance dans votre périmètre : tous les écarts déclarés restent dans la tolérance fixée."))

    if montrer_maintenance:
        _fiab_accueil = maint.compute_fiabilite(
            maint.PANNES, incidents_extra=st.session_state.incidents_simules or None
        )
        _dispo = _fiab_accueil["dispo"] * 100
        if _dispo < 97:
            _alertes.append((
                "critical",
                f"Disponibilité du Four U2 à <b>{_dispo:.1f}%</b>, en dessous du seuil de vigilance (97%) — "
                "voir l'onglet « 🛠️ Maintenance Four U2 » pour le détail des causes (MTBF/MTTR).",
            ))
        elif _dispo < 99:
            _alertes.append((
                "warning",
                f"Disponibilité du Four U2 : <b>{_dispo:.1f}%</b> — à surveiller, proche du seuil de vigilance (97%).",
            ))
        _nb_critiques = sum(1 for o in maint.AMDEC_ORGANES if o["C"] >= 25)
        if _nb_critiques:
            _alertes.append((
                "warning",
                f"<b>{_nb_critiques} organe(s)</b> classé(s) « Critique » dans l'analyse AMDEC du Four U2 "
                "(criticité ≥ 25) — voir l'onglet « 🛠️ Maintenance Four U2 » &gt; AMDEC.",
            ))
        if st.session_state.incidents_simules:
            _alertes.append((
                "info",
                f"<b>{len(st.session_state.incidents_simules)} incident(s) simulé(s)</b> enregistré(s) dans "
                "cette session de démonstration — ils sont inclus dans les indicateurs de fiabilité ci-dessus.",
            ))

    # ---------------------------------------------------------------
    # Présence en direct : qui d'autre est connecté à l'instant, tous
    # postes confondus (calculé plus haut, mis à jour à chaque battement
    # de l'auto-rafraîchissement de 5 secondes).
    # ---------------------------------------------------------------
    with SHARED["lock"]:
        _noms_presence = sorted(
            (
                f"{p['nom']} ({p['poste']})" + (" — vous" if _sid == st.session_state.sid else "")
                for _sid, p in SHARED["presence"].items()
            ),
            key=lambda s: (" — vous" not in s, s),
        )
    st.markdown(
        f"<div style='display:inline-block;padding:5px 12px;background:#E9F7EF;"
        f"border:1px solid #A9DFBF;border-radius:14px;font-size:12.5px;color:#1E6B3C;margin-bottom:8px;'>"
        f"🟢 <b>{len(_noms_presence)} personne(s) connectée(s)</b> en ce moment — {', '.join(_noms_presence)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------
    # Notifications temps réel : dès qu'un AUTRE poste publie un nouvel
    # événement dans le flux partagé (déclaration d'un OF, incident simulé),
    # un toast apparaît ici dans les ~5 secondes qui suivent — sans recharger
    # la page manuellement — grâce à st_autorefresh.
    # ---------------------------------------------------------------
    if "last_seen_feed_id" not in st.session_state:
        with SHARED["lock"]:
            st.session_state.last_seen_feed_id = SHARED["feed"][0]["id"] if SHARED["feed"] else 0

    with SHARED["lock"]:
        _feed = list(SHARED["feed"])
    _nouveaux = [
        e for e in _feed
        if e["id"] > st.session_state.last_seen_feed_id and e["auteur"] != auth["nom"]
    ]
    for _evt in reversed(_nouveaux[:3]):
        _txt_toast = re.sub("<[^>]+>", "", _evt["message"])
        _icone_toast = {"critical": "🔴", "warning": "🟠", "success": "🟢"}.get(_evt["level"], "🔔")
        st.toast(_txt_toast, icon=_icone_toast)
    if _feed:
        st.session_state.last_seen_feed_id = _feed[0]["id"]

    st.write("")
    with st.container():
        st.markdown("**🔔 Centre d'alertes — à consulter avant de naviguer dans l'application**")
        if _alertes:
            for _niveau, _texte in _alertes:
                render_alert(_niveau, _texte)
        else:
            render_alert("info", "Aucune alerte pour le moment : commencez par déclarer un OF dans l'onglet « 📝 Saisie d'une déclaration ».")

        if _feed:
            with st.expander(
                f"🕘 Flux d'activité en temps réel — tous postes connectés ({len(_feed)} événement(s))",
                expanded=bool(_nouveaux),
            ):
                for _evt in _feed[:8]:
                    _icon, _bc, _bg = NIVEAU_STYLE.get(_evt["level"], NIVEAU_STYLE["info"])
                    _tag_vous = " <b>(vous)</b>" if _evt["auteur"] == auth["nom"] else ""
                    st.markdown(
                        f"<div style='padding:6px 10px;border-left:3px solid {_bc};background:{_bg};"
                        f"border-radius:3px;margin-bottom:5px;font-size:12px;color:{GREY_TEXT};'>"
                        f"{_icon} {_evt['message']}{_tag_vous} "
                        f"<span style='color:#8892A0;'>— {temps_ecoule(_evt['ts'])}</span></div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("Le flux d'activité se remplit au fil des actions de TOUS les postes connectés (déclaration "
                       "d'un OF, simulation d'un incident maintenance) et est visible en temps réel par tout le monde ici.")

    st.write("")
    st.markdown(f"**Onglets disponibles pour votre poste ({role})**")
    autres_tabs = [t for t in tab_names if t != "🏠 Accueil"]
    cols_desc = st.columns(len(autres_tabs))
    for col, t in zip(cols_desc, autres_tabs):
        with col:
            st.markdown(
                f"<div style='padding:10px 12px;background:{WHITE};border:1px solid #E7DFD5;"
                f"border-left:4px solid {SEVAM_RED};border-radius:6px;height:150px;font-size:12.5px;color:{GREY_TEXT};'>"
                f"<b style='color:{SEVAM_RED_DARK};font-size:13px;'>{t}</b><br><br>"
                f"{TAB_DESCRIPTIONS.get(t, '')}</div>",
                unsafe_allow_html=True,
            )

    st.write("")
    st.markdown("**Aperçu en direct de votre périmètre**")
    _df_accueil = filtrer_par_perimetre(st.session_state.declarations, auth)
    a1, a2, a3, a4 = st.columns(4)
    if not _df_accueil.empty:
        _taux = _df_accueil["Qte_Realisee"].sum() / _df_accueil["Qte_Planifiee"].sum()
        a1.metric("Taux de service", f"{_taux*100:.1f}%")
        a2.metric("OF suivis", int(_df_accueil["N_OF"].nunique()))
        a3.metric(
            f"OF en écart (> {seuil_alerte}%)",
            int((_df_accueil["Ecart_Pct"].abs() > seuil_alerte).sum()),
        )
    else:
        a1.metric("Taux de service", "—")
        a2.metric("OF suivis", 0)
        a3.metric(f"OF en écart (> {seuil_alerte}%)", 0)
    if montrer_maintenance:
        _fiab_accueil = maint.compute_fiabilite(maint.PANNES)
        a4.metric("Disponibilité Four U2", f"{_fiab_accueil['dispo']*100:.1f}%",
                   help="MTBF / (MTBF + MTTR) sur les 14 pannes historisées, juin-août 2026.")
    else:
        a4.metric("Articles catalogués", len(cat.ARTICLES))

    st.write("")
    st.markdown(
        f"<div style='padding:12px 16px;background:{WHITE};border:1px solid #E7DFD5;"
        f"border-left:4px solid {SEVAM_GREEN};border-radius:6px;font-size:12.5px;color:{GREY_TEXT};'>"
        f"💡 Cette plateforme est un <b>prototype de démonstration</b> : elle illustre la faisabilité "
        f"technique des pistes proposées dans le rapport (fiche numérique, historique centralisé des "
        f"pannes, criticité AMDEC) plutôt qu'un outil déjà déployé en production chez SEVAM. Le détail "
        f"des sources de données et les limites assumées sont présentés dans l'onglet « 📘 Méthodologie "
        f"&amp; note technique »."
        f"</div>",
        unsafe_allow_html=True,
    )

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
                if statut == "A traiter":
                    explication = (
                        f"L'écart dépasse le seuil de vigilance fixé à {seuil_alerte}% (panneau de "
                        "gauche) : ce dossier mérite d'être examiné — cause principale, actions déjà "
                        "engagées, impact sur le client."
                    )
                else:
                    explication = f"L'écart reste dans la tolérance fixée ({seuil_alerte}%) : rien à signaler."
                # On stocke le message de confirmation dans le session_state plutôt que de
                # l'afficher tout de suite : l'onglet Accueil est codé AVANT cet onglet Saisie
                # et s'exécute donc en premier à chaque run. Sans un rerun immédiat, son Centre
                # d'alertes afficherait encore l'ancien état tant qu'aucune autre interaction
                # n'aurait provoqué un nouveau run (même logique que le simulateur d'incident).
                st.session_state.dernier_msg_declaration = (
                    f"<div style='padding:10px 14px;border-left:4px solid {color};background:{WHITE};'>"
                    f"<b>Déclaration enregistrée.</b> Écart calculé : <b>{ecart_unites:+d} unités "
                    f"({ecart_pct:+.1f}%)</b> — statut : <b style='color:{color}'>{statut}</b> "
                    f"(seuil actuel : {seuil_alerte}%). Impact économique estimé : <b>{cout_est:,.0f} MAD</b>."
                    f"<br><span style='font-size:12px;color:{GREY_TEXT};'>{explication}</span>"
                    f"</div>"
                )
                log_event(
                    f"<b>{auth['nom']}</b> a déclaré l'OF <b>{n_of}</b> sur {LIGNE_LABELS[ligne_choice]} — "
                    f"écart de <b>{ecart_pct:+.1f}%</b> ({statut}), impact estimé {cout_est:,.0f} MAD.",
                    level="warning" if statut == "A traiter" else "success",
                    auteur=auth["nom"],
                )
                st.rerun()

        if st.session_state.get("dernier_msg_declaration"):
            st.markdown(st.session_state.dernier_msg_declaration, unsafe_allow_html=True)
            st.session_state.dernier_msg_declaration = None

        st.write("")
        df_perimetre = filtrer_par_perimetre(st.session_state.declarations, auth)

        rech_c, undo_c = st.columns([3, 1.3])
        with rech_c:
            recherche_of = st.text_input(
                "🔍 Rechercher un N° OF",
                placeholder="ex. OF-2026-0458",
                help="Filtre le tableau ci-dessous sur les déclarations dont le N° OF contient ce texte.",
            )
        with undo_c:
            _nb_ajoutees = len(st.session_state.declarations) - st.session_state.declarations_len_initial
            st.write("")
            if st.button(
                "↩️ Annuler ma dernière déclaration",
                disabled=_nb_ajoutees == 0,
                help="Retire uniquement la dernière déclaration que VOUS venez d'ajouter pendant "
                     "cette session — jamais les données de démonstration de départ.",
                use_container_width=True,
            ):
                st.session_state.declarations = st.session_state.declarations.iloc[:-1].reset_index(drop=True)
                st.rerun()

        df_affiche = df_perimetre
        if recherche_of:
            df_affiche = df_affiche[df_affiche["N_OF"].astype(str).str.contains(recherche_of, case=False, na=False)]

        st.caption(
            f"{len(df_affiche)} déclaration(s) affichée(s) sur {len(df_perimetre)} visibles dans votre "
            f"périmètre ({role} — {scope_label})."
            + (f" Filtré sur « {recherche_of} »." if recherche_of else "")
        )
        st.dataframe(
            df_affiche.sort_values("Date", ascending=False).head(15),
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

            st.write("")
            st.markdown("**Export**")
            st.caption(
                "Télécharger un bilan Excel prêt à distribuer (jury, contrôle de gestion) : indicateurs "
                "clés, coût estimé par cause et détail des OF de votre périmètre."
            )
            _taux_service_export = (
                df["Qte_Realisee"].sum() / df["Qte_Planifiee"].sum() * 100
                if df["Qte_Planifiee"].sum() else 0
            )
            _n_of_ecart_export = int((df["Ecart_Pct"].abs() > seuil_alerte).sum())
            _synthese_rows = [
                ("Périmètre", scope_label),
                ("Poste", role),
                ("Date d'export", date.today().strftime("%d/%m/%Y")),
                ("Taux de service", f"{_taux_service_export:.1f}%"),
                ("OF suivis", int(df["N_OF"].nunique())),
                (f"OF en écart (seuil {seuil_alerte}%)", _n_of_ecart_export),
                ("Coût total estimé des écarts (MAD)", round(cout_total)),
            ]
            if not cout_par_cause.empty:
                _synthese_rows.append(("Cause la plus coûteuse", cout_par_cause.index[0]))
                _synthese_rows.append(("Coût de cette cause (MAD)", round(cout_par_cause.iloc[0])))
            _synthese_df = pd.DataFrame(_synthese_rows, columns=["Indicateur", "Valeur"])

            _excel_buffer = io.BytesIO()
            with pd.ExcelWriter(_excel_buffer, engine="openpyxl") as _writer:
                _synthese_df.to_excel(_writer, sheet_name="Synthèse", index=False)
                if not cout_par_cause.empty:
                    cout_par_cause.rename("Coût estimé (MAD)").round(0).to_excel(
                        _writer, sheet_name="Coût par cause"
                    )
                df.sort_values("Date", ascending=False).to_excel(
                    _writer, sheet_name="Détail des OF", index=False
                )
            _excel_buffer.seek(0)

            st.download_button(
                "📥 Exporter la synthèse (Excel)",
                data=_excel_buffer,
                file_name=f"Synthese_Impact_Economique_SEVAM_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

# =========================================================
# ONGLET — Maintenance Four U2 (historique des pannes, fiabilité, AMDEC,
# simulateur d'incident) — chapitre 6.2.4 / 6.2.5 du rapport PFA
# =========================================================
if "🛠️ Maintenance Four U2" in tab_map:
    with tab_map["🛠️ Maintenance Four U2"]:
        st.markdown("#### Fiabilité et maintenance — Four U2 (site de Tit Mellil)")
        st.caption(
            "Ce module porte sur le Four U2, seul four disposant d'un historique de pannes détaillé "
            "à ce stade (voir l'onglet Méthodologie). Il répond à la remarque du professeur encadrant "
            "demandant un cas réel permettant de maîtriser la procédure de traitement d'une panne de "
            "A à Z, le calcul du MTBF et les méthodes d'analyse des causes."
        )

        sous_tabs = st.tabs([
            "📋 Historique des pannes", "📈 Fiabilité (MTBF/MTTR)", "🧩 Analyse des causes",
            "🛑 AMDEC — Criticité", "🧮 Calcul de besoin", "🚨 Simulateur d'incident",
        ])
        (tab_hist, tab_fiab, tab_causes, tab_amdec, tab_besoin, tab_simu) = sous_tabs

        # -------------------------------------------------------------
        # Sous-onglet — Historique des pannes
        # -------------------------------------------------------------
        with tab_hist:
            h1, h2, h3, h4 = st.columns(4)
            h1.metric("Pannes recensées", len(maint.PANNES))
            h2.metric("Total heures d'arrêt", f"{maint.TOTAL_HEURES_ARRET:.1f} h")
            h3.metric("Quantité totale perdue", f"{maint.TOTAL_QTE_PERDUE:,}".replace(",", " ") + " u")
            h4.metric(
                "Période observée",
                f"{maint.PERIOD_START.strftime('%d/%m')} → {maint.PERIOD_END.strftime('%d/%m/%Y')}",
            )

            df_pannes = pd.DataFrame([
                {
                    "N°": i + 1, "Date": p["date"], "Ligne": p["ligne"], "Article": p["article"],
                    "Catégorie": maint.CAUSE_PANNE_LABELS[p["cause"]], "Description": p["description"],
                    "Durée (h)": p["duree_h"], "Cadence (u/h)": p["cadence"],
                    "Qté perdue (u)": p["qte_perdue"], "Intervenant": p["intervenant"], "Statut": p["statut"],
                }
                for i, p in enumerate(maint.PANNES)
            ])
            st.dataframe(df_pannes, use_container_width=True, hide_index=True)
            st.caption(
                "Relevé détaillé reconstitué à partir de vraies lignes du journal de production ERP de "
                "SEVAM (\"BD des changements\"), filtrées sur le Four U2 puis replacées sur la période "
                "du stage — voir l'onglet Méthodologie pour le détail de la source."
            )

            st.write("")
            st.markdown("**Analyse Pareto des causes de panne (heures d'arrêt cumulées)**")
            mttr_cause = maint.mttr_par_cause(maint.PANNES)
            causes_pareto = sorted(mttr_cause, key=lambda c: -c["heures"])
            total_h = sum(c["heures"] for c in causes_pareto)
            cum = 0.0
            cum_pct = []
            for c in causes_pareto:
                cum += c["heures"]
                cum_pct.append(cum / total_h * 100)

            fig_pareto = go.Figure()
            fig_pareto.add_bar(
                x=[c["libelle"] for c in causes_pareto], y=[c["heures"] for c in causes_pareto],
                name="Heures d'arrêt cumulées",
                marker_color=[maint.CAUSE_PANNE_COLOR[c["cause"]] for c in causes_pareto],
            )
            fig_pareto.add_trace(go.Scatter(
                x=[c["libelle"] for c in causes_pareto], y=cum_pct, name="% cumulé", yaxis="y2",
                mode="lines+markers", line=dict(color=SEVAM_GREEN_DARK, width=3),
            ))
            fig_pareto.add_hline(y=80, line_dash="dot", line_color="#888", yref="y2",
                                  annotation_text="Seuil des 80% (règle de Pareto)", annotation_position="bottom right")
            fig_pareto.update_layout(
                yaxis=dict(title="Heures d'arrêt cumulées"),
                yaxis2=dict(title="% cumulé", overlaying="y", side="right", range=[0, 105]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(t=40, b=20), height=380, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
            )
            st.plotly_chart(fig_pareto, use_container_width=True)
            st.caption(
                f"Les pannes {causes_pareto[0]['libelle'].lower()} et {causes_pareto[1]['libelle'].lower()} "
                f"concentrent à elles seules {cum_pct[1]:.0f}% des heures d'arrêt cumulées sur la période."
            )

        # -------------------------------------------------------------
        # Sous-onglet — Fiabilité (MTBF / MTTR / Disponibilité)
        # -------------------------------------------------------------
        with tab_fiab:
            inclure_simules = False
            if st.session_state.incidents_simules:
                inclure_simules = st.checkbox(
                    f"Inclure les {len(st.session_state.incidents_simules)} incident(s) simulé(s) "
                    "dans le calcul (onglet Simulateur d'incident)",
                    value=True,
                )
            extra = st.session_state.incidents_simules if inclure_simules else None
            fiab = maint.compute_fiabilite(maint.PANNES, incidents_extra=extra)
            fiab_base = maint.compute_fiabilite(maint.PANNES)

            f1, f2, f3 = st.columns(3)
            f1.metric("MTBF (temps moyen entre pannes)", f"{fiab['mtbf']:.1f} h",
                      delta=(f"{fiab['mtbf']-fiab_base['mtbf']:.1f} h" if extra else None))
            f2.metric("MTTR (temps moyen de réparation)", f"{fiab['mttr']:.1f} h",
                      delta=(f"{fiab['mttr']-fiab_base['mttr']:.1f} h" if extra else None))
            f3.metric("Disponibilité", f"{fiab['dispo']*100:.2f}%",
                      delta=(f"{(fiab['dispo']-fiab_base['dispo'])*100:.2f} pt" if extra else None),
                      delta_color="inverse" if extra else "normal")
            st.caption(
                f"Calculé sur {fiab['nb_pannes']} panne(s), {fiab['heures_arret']:.1f} h d'arrêt cumulées, "
                f"pour un temps d'ouverture total de {fiab['temps_ouverture_total']:.0f} h "
                f"({maint.NB_LIGNES_U2} lignes × {maint.PERIODE_JOURS} jours × 24 h)."
            )

            st.write("")
            st.markdown("**MTTR moyen par catégorie de panne**")
            df_mttr = pd.DataFrame(mttr_cause if not extra else maint.mttr_par_cause(maint.PANNES + list(extra)))
            df_mttr = df_mttr.rename(columns={
                "libelle": "Catégorie de panne", "occurrences": "Occurrences",
                "heures": "Heures d'arrêt cumulées", "mttr_moyen": "MTTR moyen (h)",
            })[["Catégorie de panne", "Occurrences", "Heures d'arrêt cumulées", "MTTR moyen (h)"]]
            st.dataframe(df_mttr, use_container_width=True, hide_index=True)

            st.markdown(
                f"<div style='padding:12px 16px;background:{WHITE};border:1px solid #E7DFD5;"
                f"border-left:4px solid {SEVAM_GREEN};border-radius:6px;font-size:12.5px;color:{GREY_TEXT};'>"
                f"Avec une disponibilité de <b>{fiab['dispo']*100:.1f}%</b>, le Four U2 reste globalement "
                f"fiable sur la période observée. L'enjeu principal ne porte pas sur la fréquence des "
                f"pannes mais sur la gravité (durée) de certaines pannes rares — en particulier la panne "
                f"four/brûleur du 29/07/2026 (18,2 h), qui à elle seule représente près de 29% du total "
                f"des heures d'arrêt de la période (voir l'onglet Simulateur d'incident pour rejouer ce cas)."
                f"</div>", unsafe_allow_html=True,
            )

        # -------------------------------------------------------------
        # Sous-onglet — Analyse des causes (5M / 5S / 5 Pourquoi)
        # -------------------------------------------------------------
        with tab_causes:
            st.caption(
                "Analyse appliquée au cas réel le plus grave de la période : panne four/brûleur du "
                "29/07/2026, ligne L11 (voir la chronologie complète dans l'onglet Simulateur d'incident)."
            )
            st.markdown("**1. Méthode des 5M (diagnostic Ishikawa)**")
            df_5m = pd.DataFrame(maint.M5_ROWS).rename(columns={
                "categorie": "Catégorie (5M)", "cause": "Cause potentielle identifiée",
                "constat": "Constat", "action": "Action corrective proposée",
            })
            st.dataframe(df_5m, use_container_width=True, hide_index=True)

            st.write("")
            st.markdown("**2. Démarche 5S — pistes d'amélioration terrain associées**")
            df_5s = pd.DataFrame(maint.S5_ROWS).rename(columns={
                "etape": "Étape 5S", "signification": "Signification",
                "action": "Action proposée pour le Four U2",
            })
            st.dataframe(df_5s, use_container_width=True, hide_index=True)

            st.write("")
            st.markdown("**3. Méthode des 5 Pourquoi (approfondissement de la cause racine)**")
            for i, (q, rep) in enumerate(maint.POURQUOI_5, start=1):
                st.markdown(f"**Pourquoi {i}.** {q} → {rep}")

        # -------------------------------------------------------------
        # Sous-onglet — AMDEC / Criticité
        # -------------------------------------------------------------
        with tab_amdec:
            st.markdown("**Échelles utilisées**")
            st.caption(
                "Fréquence (F) : 1 = très rare (> 1 an) … 5 = fréquent (hebdomadaire). "
                "Gravité (G) : 1 = impact mineur … 5 = arrêt total du four / risque sécurité. "
                "Détection (D) : 1 = détection immédiate (alarme automatique) … 5 = dégradation "
                "progressive difficile à détecter. Criticité C = F × G × D — seuils : C ≥ 25 = critique, "
                "12 ≤ C < 25 = à surveiller, C < 12 = maîtrisé."
            )

            df_amdec = pd.DataFrame([
                {
                    "Rang": i + 1, "Organe": o["organe"], "Fonction": o["fonction"],
                    "Mode de défaillance": o["mode"], "F": o["F"], "G": o["G"], "D": o["D"],
                    "Criticité": o["C"], "Niveau": maint.criticite_niveau(o["C"])[0],
                    "MTTR estimé": o["mttr_label"], "Commentaire": o["commentaire"],
                }
                for i, o in enumerate(maint.AMDEC_ORGANES)
            ])

            def _style_criticite(val):
                for o in maint.AMDEC_ORGANES:
                    if o["C"] == val:
                        _, color = maint.criticite_niveau(val)
                        return f"background-color:{color};color:white;font-weight:bold;"
                return ""

            _styler = df_amdec.style
            _styler = (
                _styler.map(_style_criticite, subset=["Criticité"])
                if hasattr(_styler, "map") else
                _styler.applymap(_style_criticite, subset=["Criticité"])
            )
            st.dataframe(_styler, use_container_width=True, hide_index=True)

            st.write("")
            st.markdown("**Criticité par organe**")
            fig_amdec = go.Figure(go.Bar(
                x=[o["C"] for o in maint.AMDEC_ORGANES][::-1],
                y=[o["organe"] for o in maint.AMDEC_ORGANES][::-1],
                orientation="h",
                marker_color=[maint.criticite_niveau(o["C"])[1] for o in maint.AMDEC_ORGANES][::-1],
                text=[o["C"] for o in maint.AMDEC_ORGANES][::-1], textposition="outside",
            ))
            fig_amdec.update_layout(
                margin=dict(t=10, b=20), height=380, plot_bgcolor=WHITE, paper_bgcolor=WHITE,
                xaxis_title="Criticité C = F × G × D",
            )
            st.plotly_chart(fig_amdec, use_container_width=True)

            top = maint.AMDEC_ORGANES[0]
            st.markdown(
                f"<div style='padding:12px 16px;background:{WHITE};border:1px solid #E7DFD5;"
                f"border-left:4px solid {SEVAM_RED};border-radius:6px;font-size:12.5px;color:{GREY_TEXT};'>"
                f"L'organe le plus critique est le <b>{top['organe']}</b> (C = {top['C']}) : sa réparation "
                f"est rapide ({top['mttr_label']}) mais c'est un point unique de défaillance qui alimente "
                f"les {maint.NB_LIGNES_U2} lignes du Four U2 — sa panne bloque instantanément toute la "
                f"production. Une politique de maintenance préventive ciblée sur cet organe et sur les "
                f"brûleurs (2e position) réduirait fortement le risque global d'arrêt du four."
                f"</div>", unsafe_allow_html=True,
            )

        # -------------------------------------------------------------
        # Sous-onglet — Calcul de besoin de production
        # -------------------------------------------------------------
        with tab_besoin:
            st.caption(
                "Calculateur reprenant la logique de la fiche de calcul de besoin de production "
                "(chapitre 6.2.4) — valeurs par défaut : article Steine 100 VA, ligne L12 (Four U2). "
                "Modifiez les champs pour recalculer instantanément."
            )
            bd = maint.BESOIN_DEFAUT
            b1, b2 = st.columns(2)
            with b1:
                besoin_client = st.number_input("Besoin client (unités)", min_value=0, value=bd["besoin_client"], step=1000)
                stock_actuel = st.number_input("Stock actuel (unités)", min_value=0, value=bd["stock_actuel"], step=1000)
                stock_rz = st.number_input(
                    "Stock R+Z — emballage, marge 15% incluse (unités)", min_value=0, value=bd["stock_rz"], step=100,
                )
            with b2:
                ventes_realisees = st.number_input("Ventes réalisées (unités)", min_value=0, value=bd["ventes_realisees"], step=1000)
                palettes_dispo = st.number_input("Palettes déjà disponibles", min_value=0, value=bd["palettes_dispo"], step=1)
                capacite_palette = st.number_input("Capacité palette (unités/palette)", min_value=1, value=bd["capacite_palette"], step=1)

            res = maint.calc_besoin(besoin_client, stock_actuel, stock_rz, ventes_realisees, palettes_dispo, capacite_palette)
            st.write("")

            def _fmt(n):
                return f"{n:,.0f}".replace(",", " ")

            with st.expander("🔍 Détail du calcul, chiffre par chiffre (pour vérifier vous-même)"):
                st.markdown(
                    f"<div style='font-size:13px;line-height:2;color:{GREY_TEXT};'>"
                    f"Besoin net à couvrir = {_fmt(besoin_client)} − {_fmt(stock_actuel)} − {_fmt(stock_rz)} "
                    f"− {_fmt(ventes_realisees)} (ventes déjà réalisées) = <b>{_fmt(res['besoin_net'])} u</b><br>"
                    f"Équivalent des palettes déjà disponibles = {_fmt(palettes_dispo)} × {_fmt(capacite_palette)} "
                    f"= <b>{_fmt(res['equiv_palettes_dispo'])} u</b><br>"
                    f"Reste à produire = {_fmt(res['besoin_net'])} − {_fmt(res['equiv_palettes_dispo'])} = "
                    f"<b>{_fmt(res['besoin_net'] - res['equiv_palettes_dispo'])} u</b>"
                    + (" (négatif → ramené à 0, il y a déjà plus de palettes que nécessaire)"
                       if res["besoin_net"] - res["equiv_palettes_dispo"] < 0 else "") +
                    f"<br>Palettes à produire = partie entière de {_fmt(res['reste_a_produire'])} ÷ "
                    f"{_fmt(capacite_palette)} = <b>{res['palettes_a_produire']} palettes</b>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.caption(
                    "⚠️ Si vous avez déjà déduit les ventes réalisées à la main pour obtenir le besoin client "
                    "ou le stock ci-dessus, ne les remettez pas une seconde fois dans « Ventes réalisées » — "
                    "sinon elles seraient soustraites deux fois. Ce champ n'est à remplir que si les ventes "
                    "déjà réalisées ne sont PAS encore incluses dans les autres champs."
                )

            r1, r2 = st.columns(2)
            r1.metric("Besoin net à couvrir", f"{res['besoin_net']:,.0f}".replace(",", " ") + " u")
            r2.metric("Reste à produire", f"{res['reste_a_produire']:,.0f}".replace(",", " ") + " u")

            if res["besoin_net"] <= 0:
                # Le calcul recalcule bel et bien à chaque changement de champ (ce n'est jamais
                # l'exemple Steine figé) : un résultat à 0 est un cas normal du calculateur, quand
                # le stock déjà disponible couvre entièrement le besoin client — pas un blocage.
                st.markdown(
                    f"<div style='padding:14px 18px;background:#E9F7EF;border:1px solid #A9DFBF;"
                    f"border-radius:6px;margin-top:8px;font-size:13.5px;color:#1E6B3C;'>"
                    f"✅ <b>Stock déjà suffisant</b> — avec ces valeurs, le stock actuel, le stock R+Z "
                    f"et les ventes déjà réalisées couvrent entièrement le besoin client à eux seuls "
                    f"(besoin net ≤ 0) : aucune production supplémentaire n'est nécessaire, d'où "
                    f"<b>0 palette</b> ci-dessous.</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<div style='padding:18px;background:{SEVAM_GREEN_DARK};border-radius:6px;text-align:center;margin-top:8px;'>"
                f"<span style='color:white;font-size:14px;'>PALETTES À PRODUIRE</span><br>"
                f"<span style='color:white;font-size:30px;font-weight:bold;'>{res['palettes_a_produire']:,}".replace(",", " ") +
                f" palettes</span></div>",
                unsafe_allow_html=True,
            )
            st.caption(
                "Besoin net à couvrir = Besoin client − Stock actuel − Stock R+Z − Ventes réalisées. "
                "Reste à produire = Besoin net − (Palettes disponibles × Capacité palette). "
                "Palettes à produire = partie entière de Reste à produire ÷ Capacité palette. "
                "Le calcul se met à jour instantanément dès qu'un champ ci-dessus change — l'exemple "
                "Steine 100 VA n'est que la valeur de départ, pas un résultat figé."
            )

        # -------------------------------------------------------------
        # Sous-onglet — Simulateur d'incident temps réel
        # -------------------------------------------------------------
        with tab_simu:
            st.markdown(
                "**Rejouez, étape par étape, la procédure de traitement d'un incident sur le Four U2** "
                "— de la détection à la clôture, comme le ferait une équipe de terrain en temps réel."
            )
            sc1, sc2 = st.columns(2)
            with sc1:
                organe_choisi = st.selectbox(
                    "Organe concerné par l'incident",
                    options=[o["organe"] for o in maint.AMDEC_ORGANES],
                    index=[o["organe"] for o in maint.AMDEC_ORGANES].index(st.session_state.sim_organe_nom),
                    help="Choisissez un organe de la grille AMDEC pour simuler un incident réaliste — "
                         "les Brûleurs rejouent le cas réel détaillé du 29/07/2026.",
                )
            with sc2:
                ligne_choisie = st.selectbox(
                    "Ligne concernée", options=maint.LIGNES_U2,
                    index=maint.LIGNES_U2.index(st.session_state.sim_ligne),
                )

            if organe_choisi != st.session_state.sim_organe_nom or ligne_choisie != st.session_state.sim_ligne:
                st.session_state.sim_organe_nom = organe_choisi
                st.session_state.sim_ligne = ligne_choisie
                st.session_state.sim_step_idx = 0

            organe = maint.organe_par_nom(organe_choisi)
            scenario = maint.generer_scenario(organe)
            total_min = sum(s["duree_min"] for s in scenario)
            idx = st.session_state.sim_step_idx

            badge_niveau, badge_color = maint.criticite_niveau(organe["C"])
            st.markdown(
                f"<div style='padding:10px 14px;border-left:4px solid {badge_color};background:#F5F8FC;"
                f"border-radius:4px;font-size:13px;margin-bottom:10px;'>"
                f"🚨 <b>Incident simulé — {organe['organe']}</b> ({organe['fonction']}) sur <b>{ligne_choisie}</b><br>"
                f"Mode de défaillance : {organe['mode']}<br>"
                f"<span style='font-size:11.5px;color:#8892A0;'>Criticité AMDEC : {organe['C']} "
                f"(<b style='color:{badge_color}'>{badge_niveau}</b>) — durée totale estimée du scénario : "
                f"{total_min//60}h{total_min%60:02d}</span></div>",
                unsafe_allow_html=True,
            )

            elapsed = sum(s["duree_min"] for s in scenario[:idx])
            st.progress(min(elapsed / total_min, 1.0) if total_min else 0.0)
            st.caption(f"⏱️ Temps écoulé depuis la détection : {elapsed//60}h{elapsed%60:02d}  /  {total_min//60}h{total_min%60:02d}")

            for s in scenario[:idx]:
                horaire = f"{s['horaire']} · " if s.get("horaire") else ""
                st.markdown(
                    f"<div style='padding:10px 14px;background:{WHITE};border:1px solid #E7DFD5;"
                    f"border-left:4px solid {SEVAM_RED};border-radius:4px;margin-bottom:6px;'>"
                    f"<b>Étape {s['n']} — {s['etape']}</b> <span style='font-size:11.5px;color:#8892A0;'>"
                    f"({horaire}{s['duree_min']} min)</span><br>"
                    f"<span style='font-size:13px;'>{s['action']}</span><br>"
                    f"<span style='font-size:11.5px;color:{GREY_TEXT};'>👤 {s['acteur']}"
                    + (f" — {s['observation']}" if s.get("observation") and s["observation"] != "—" else "")
                    + "</span></div>",
                    unsafe_allow_html=True,
                )

            bc1, bc2, bc3 = st.columns([1, 1, 2])
            with bc1:
                if idx < len(scenario):
                    if st.button("▶ Étape suivante", type="primary", use_container_width=True):
                        st.session_state.sim_step_idx += 1
                        st.rerun()
            with bc2:
                if st.button("🔄 Réinitialiser", use_container_width=True):
                    st.session_state.sim_step_idx = 0
                    st.rerun()

            if idx >= len(scenario):
                duree_h = total_min / 60
                cadence_est = maint.cadence_moyenne_ligne(ligne_choisie)
                qte_perdue_est = round(duree_h * cadence_est)
                st.success("Scénario complet — incident traité de la détection à la clôture.")
                s1, s2, s3 = st.columns(3)
                s1.metric("Durée totale", f"{duree_h:.1f} h")
                s2.metric("Cadence retenue", f"{cadence_est:.0f} u/h")
                s3.metric("Quantité perdue estimée", f"{qte_perdue_est:,}".replace(",", " ") + " u")
                with bc3:
                    if st.button("✅ Enregistrer cet incident dans l'historique (simulation)", use_container_width=True):
                        st.session_state.incidents_simules.append({
                            "date": date.today(), "ligne": ligne_choisie,
                            "article": "Article en cours (incident simulé)",
                            "cause": organe["cause_associee"],
                            "description": f"{organe['organe']} — {organe['mode']} (scénario simulé)",
                            "duree_h": round(duree_h, 1), "cadence": round(cadence_est),
                            "intervenant": scenario[-1]["acteur"], "statut": "Résolu (simulation)",
                            "estimee": True, "qte_perdue": qte_perdue_est,
                        })
                        _qte_perdue_fmt = f"{qte_perdue_est:,}".replace(",", " ")
                        log_event(
                            f"<b>{auth['nom']}</b> a enregistré un incident simulé sur "
                            f"{LIGNE_LABELS.get(ligne_choisie, ligne_choisie)} — "
                            f"<b>{organe['organe']}</b> ({organe['mode']}), durée {duree_h:.1f} h, "
                            f"~{_qte_perdue_fmt} u perdues. Impact visible immédiatement "
                            "sur la disponibilité du Four U2.",
                            level="critical",
                            auteur=auth["nom"],
                        )
                        # Rerun immédiatement : sans cela, l'onglet Fiabilité (déjà calculé plus haut
                        # dans ce même script run) afficherait encore l'ancien MTBF/MTTR tant qu'aucune
                        # autre interaction n'a provoqué de nouveau rerun.
                        st.session_state.sim_incident_enregistre = True
                        st.rerun()
                if st.session_state.get("sim_incident_enregistre"):
                    st.success(
                        "Incident ajouté ! Consultez l'onglet « 📈 Fiabilité (MTBF/MTTR) » pour voir "
                        "l'effet immédiat sur la disponibilité du Four U2."
                    )
                    st.session_state.sim_incident_enregistre = False
                st.caption(
                    f"{len(st.session_state.incidents_simules)} incident(s) simulé(s) enregistré(s) "
                    "dans cette session." if st.session_state.incidents_simules else ""
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
        "10 des postes proposés dans l'annuaire proviennent de personnes et fonctions **réelles**, "
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
        "« nom à confirmer ».\n\n"
        "Un 11e compte, **Pr. Bellahkim — Encadrant pédagogique (École)**, a été ajouté avec un accès "
        "complet (tous sites, tous départements) pour permettre à l'encadrant pédagogique d'explorer "
        "librement la plateforme en soutenance. Il ne fait pas partie de l'annuaire réel SEVAM — "
        "contrairement aux dix postes ci-dessus, dont chaque nom et poste est directement issu de la "
        "fiche de validation transmise par l'entreprise."
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

    st.markdown("**10. Module Maintenance Four U2 — origine des données**")
    st.markdown(
        "Les 14 pannes de l'historique, la chronologie détaillée du cas réel (panne du 29/07/2026) "
        "et la grille de criticité AMDEC (module `maintenance_sevam.py`) reprennent exactement les "
        "chiffres du classeur *Historique_Pannes_Four2_U2.xlsx* joint au rapport (chapitre 6.2.4 et "
        "6.2.5) : lignes, cadences et durées d'arrêt tirées du journal de production ERP réel de "
        "SEVAM (\"BD des changements\"), filtrées sur le Four U2 et replacées sur la période du "
        "stage. Le MTBF, le MTTR et la disponibilité affichés dans l'onglet Fiabilité sont "
        "**recalculés en direct** à partir de ce relevé (et, si activé, des incidents ajoutés depuis "
        "le simulateur), plutôt que d'être des valeurs figées recopiées du rapport. Le calculateur de "
        "besoin reprend de la même façon la fiche de calcul de besoin de production (article Steine "
        "100 VA, ligne L12)."
    )

    st.markdown("**11. Limites assumées de ce prototype**")
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

    st.markdown("**12. Pistes d'évolution vers un outil de production**")
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
