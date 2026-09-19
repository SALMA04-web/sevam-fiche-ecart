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

from src import config, db  # noqa: E402

SUIVI_2025_CSV = ROOT / "data" / "suivi_quotidien_2025.csv"
QUALITE_CSV = ROOT / "data" / "rapport_qualite_donnees.csv"
COMPARAISON_CSV = ROOT / "data" / "comparaison_sources_2024.csv"


def setup_page(title: str, icon: str = "🏭"):
    st.set_page_config(page_title=f"SEVAM — {title}", page_icon=icon, layout="wide")
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: #FFFFFF; }}
        h1, h2, h3 {{ color: {config.COLOR['anthracite']}; font-family: Georgia, 'Cambria', serif; }}
        div[data-testid="stMetricValue"] {{ color: {config.COLOR['amber_deep']}; font-weight: 700; }}
        section[data-testid="stSidebar"] {{ background-color: {config.COLOR['steel_pale']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Prototype SEVAM — suivi des arrêts de ligne — données réelles 2024-2025")


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
