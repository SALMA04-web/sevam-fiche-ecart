"""Bootstrap partagé par app.py et toutes les pages : configuration de page,
chargement des données (mis en cache), filtres de barre latérale réutilisables,
petit style visuel cohérent avec l'identité du rapport PFA.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import auth, config, db  # noqa: E402

SUIVI_2025_CSV = ROOT / "data" / "suivi_quotidien_2025.csv"
QUALITE_CSV = ROOT / "data" / "rapport_qualite_donnees.csv"
COMPARAISON_CSV = ROOT / "data" / "comparaison_sources_2024.csv"
LOGO_PATH = ROOT / "logo_sevam.png"


def setup_page(title: str, icon: str = "🏭", page_key: str | None = None, public: bool = False):
    """Bootstrap commun à toutes les pages : mise en page, style ERP, connexion.

    - page_key : nom de page tel qu'utilisé dans config.PAGE_ROLES, pour appliquer
      le contrôle d'accès par rôle. Laisser à None pour une page ouverte à tout
      utilisateur connecté (ex. Accueil).
    - public=True : ignore la connexion (uniquement pour la page Connexion elle-même).
    """
    st.set_page_config(page_title=f"SEVAM — {title}", page_icon=icon, layout="wide")
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: #FFFFFF; }}
        h1, h2, h3 {{ color: {config.COLOR['anthracite']}; font-family: Georgia, 'Cambria', serif; }}
        div[data-testid="stMetricValue"] {{ color: {config.COLOR['amber_deep']}; font-weight: 700; }}
        div[data-testid="stMetric"] {{
            background-color: {config.COLOR['steel_pale']};
            border: 1px solid {config.COLOR['steel_light']};
            border-radius: 10px;
            padding: 0.9rem 1rem 0.6rem 1rem;
        }}
        section[data-testid="stSidebar"] {{ background-color: {config.COLOR['anthracite']}; }}
        section[data-testid="stSidebar"] * {{ color: {config.COLOR['steel_pale']} !important; }}
        section[data-testid="stSidebar"] .stButton button {{
            background-color: {config.COLOR['amber_deep']}; color: {config.COLOR['white']} !important;
            border: none;
        }}
        .sevam-topbar {{
            display: flex; align-items: center; justify-content: space-between;
            background-color: {config.COLOR['anthracite']}; color: {config.COLOR['white']};
            padding: 0.6rem 1.1rem; border-radius: 8px; margin-bottom: 1.1rem;
        }}
        .sevam-topbar .sevam-brand {{ font-weight: 700; letter-spacing: 0.04em; font-size: 1.05rem; }}
        .sevam-topbar .sevam-module {{ color: {config.COLOR['amber_pale']}; font-size: 0.95rem; }}
        .sevam-badge {{
            display: inline-block; background-color: {config.COLOR['amber_deep']};
            color: {config.COLOR['white']}; border-radius: 999px; padding: 0.15rem 0.7rem;
            font-size: 0.8rem; font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    db.init_db()
    user = None
    if not public:
        user = auth.require_page_access(page_key) if page_key else auth.require_login()

    badge = f"<span class='sevam-badge'>{user['role']}</span> {user['nom']}" if user else ""
    st.markdown(
        f"""
        <div class="sevam-topbar">
            <div class="sevam-brand">🏭 SEVAM — Outil de pilotage (arrêts · production · commercial)</div>
            <div class="sevam-module">{title} &nbsp;·&nbsp; {badge}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Données réelles SEVAM (2012-2026, selon les modules) — voir la page "
        "**Qualité des données** pour la provenance et les limites de chaque source."
    )
    if not public:
        auth.render_sidebar_identity()


@st.cache_data(show_spinner=False)
def _load_events_cached(_version: int) -> pd.DataFrame:
    return db.fetch_evenements()


def load_events(force_refresh: bool = False) -> pd.DataFrame:
    """Événements (import 2024 + déclarations manuelles), avec invalidation du
    cache après une nouvelle saisie (voir pages/1_Nouvelle_declaration.py)."""
    if force_refresh:
        st.session_state["_events_version"] = st.session_state.get("_events_version", 0) + 1
    version = st.session_state.get("_events_version", 0)
    return _load_events_cached(version)


@st.cache_data(show_spinner=False)
def load_suivi_2025() -> pd.DataFrame:
    df = pd.read_csv(SUIVI_2025_CSV, parse_dates=["date"])
    return df


@st.cache_data(show_spinner=False)
def load_quality_report() -> pd.DataFrame:
    if not QUALITE_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(QUALITE_CSV)


@st.cache_data(show_spinner=False)
def load_comparaison_sources() -> pd.DataFrame:
    if not COMPARAISON_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(COMPARAISON_CSV)


# ---------------------------------------------------------------------------
# Modules ERP supplémentaires (production réelle 2012-2024, commercial 2025-2026,
# stock Gobeleterie 2026) — voir src/etl_erp.py pour la provenance exacte.
# ---------------------------------------------------------------------------
def _csv(name: str, parse_dates=None) -> pd.DataFrame:
    path = ROOT / "data" / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=parse_dates)


@st.cache_data(show_spinner=False)
def load_rendement_of() -> pd.DataFrame:
    return _csv("rendement_of.csv", parse_dates=["date_debut", "date_fin_prod", "date_fin"])


@st.cache_data(show_spinner=False)
def load_catalogue() -> pd.DataFrame:
    return _csv("catalogue_articles.csv", parse_dates=["derniere_production"])


@st.cache_data(show_spinner=False)
def load_commandes_clients() -> pd.DataFrame:
    return _csv("commandes_clients_2026.csv")


@st.cache_data(show_spinner=False)
def load_suivi_commandes() -> pd.DataFrame:
    return _csv("suivi_commandes_clients_2026.csv")


@st.cache_data(show_spinner=False)
def load_prospection() -> pd.DataFrame:
    return _csv("prospection_commerciale.csv")


@st.cache_data(show_spinner=False)
def load_stock() -> pd.DataFrame:
    return _csv("stock_gobeleterie.csv")


@st.cache_data(show_spinner=False)
def load_budget_commercial() -> pd.DataFrame:
    return _csv("budget_commercial_2026.csv")


@st.cache_data(show_spinner=False)
def load_ventes_mensuelles() -> pd.DataFrame:
    return _csv("ventes_mensuelles_2026.csv")


def _fmt_cell(v):
    if pd.isna(v):
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def display_df(df: pd.DataFrame) -> pd.DataFrame:
    """A appeler juste avant st.dataframe() sur une table issue d'une fusion de
    plusieurs sources (catalogue, rendement...) : les valeurs manquantes (NaN/NaT)
    s'affichent sinon comme le mot littéral "None" dans le tableau (comportement de
    cette version de Streamlit). Une colonne numérique sans aucune valeur manquante
    garde son type (triable/formatée normalement) ; une colonne avec des valeurs
    manquantes est convertie en texte de façon uniforme, pour éviter une colonne au
    type mixte que l'affichage (pyarrow) refuse de sérialiser. Ne touche qu'à
    l'affichage — pas aux données exportées en CSV."""
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].dt.strftime("%Y-%m-%d")
        if out[c].isna().any():
            out[c] = out[c].map(_fmt_cell)
    return out


def sidebar_filters(events: pd.DataFrame, key_prefix: str = ""):
    """Filtres réutilisables (période + lignes) affichés dans la barre latérale.
    Retourne (date_from, date_to, lignes_selectionnees)."""
    st.sidebar.header("Filtres")
    min_date = pd.to_datetime(events["date"]).min().date() if len(events) else pd.Timestamp("2024-01-01").date()
    max_date = pd.to_datetime(events["date"]).max().date() if len(events) else pd.Timestamp.today().date()

    perimetre = st.sidebar.radio(
        "Périmètre", ["Toutes les lignes", "Un four", "Une ligne"],
        key=f"{key_prefix}_perimetre",
    )
    if perimetre == "Toutes les lignes":
        lignes = config.LIGNES
    elif perimetre == "Un four":
        four = st.sidebar.selectbox("Four", config.FOURS, key=f"{key_prefix}_four")
        lignes = config.FOUR_TO_LIGNES[four]
    else:
        ligne = st.sidebar.selectbox("Ligne", config.LIGNES, key=f"{key_prefix}_ligne")
        lignes = [ligne]

    date_range = st.sidebar.date_input(
        "Période", value=(min_date, max_date), min_value=min_date, max_value=max_date,
        key=f"{key_prefix}_periode",
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        date_from, date_to = date_range
    else:
        date_from, date_to = min_date, max_date

    return pd.Timestamp(date_from), pd.Timestamp(date_to), lignes
