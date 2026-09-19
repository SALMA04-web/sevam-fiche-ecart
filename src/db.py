"""
Base de données persistante (SQLite) pour les événements d'arrêt.

Contrairement au prototype de démonstration (données en mémoire, perdues à chaque
redémarrage), cette base est un vrai fichier sur disque (data/sevam.db) : toute
déclaration saisie dans l'application reste enregistrée, et est visible par tous les
postes qui pointent vers le même fichier. Le journal historique 2024 est importé une
seule fois dans cette même table, afin que les calculs de fiabilité (MTBF, MTTR,
Pareto, AMDEC) s'appuient toujours sur une source unique, qu'il s'agisse d'un
événement historique ou d'une déclaration saisie aujourd'hui.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "sevam.db"
EVENEMENTS_2024_CSV = BASE_DIR / "data" / "evenements_2024.csv"

LIGNES = ["L11", "L12", "L13", "L21", "L22", "L23"]
LIGNE_TO_FOUR = {"L11": "Four 1", "L12": "Four 1", "L13": "Four 1",
                 "L21": "Four 2", "L22": "Four 2", "L23": "Four 2"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS evenements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    ligne TEXT NOT NULL,
    four TEXT NOT NULL,
    probleme TEXT,
    equipement TEXT,
    famille TEXT,
    duree_min REAL,
    source TEXT NOT NULL DEFAULT 'manuel',
    saisi_par TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evenements_date ON evenements(date);
CREATE INDEX IF NOT EXISTS idx_evenements_ligne ON evenements(ligne);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    conn = conn or get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    _seed_from_csv_if_empty(conn)
    if own:
        conn.close()


def _seed_from_csv_if_empty(conn: sqlite3.Connection) -> None:
    (count,) = conn.execute("SELECT COUNT(*) FROM evenements").fetchone()
    if count > 0:
        return
    if not EVENEMENTS_2024_CSV.exists():
        return
    df = pd.read_csv(EVENEMENTS_2024_CSV, parse_dates=["date"])
    now = datetime.now().isoformat(timespec="seconds")
    records = [
        (
            row["date"].strftime("%Y-%m-%d"),
            row["ligne"],
            row["four"],
            row.get("probleme"),
            row.get("equipement_affichage") or row.get("equipement"),
            row.get("famille_affichage") or row.get("famille"),
            None if pd.isna(row.get("duree_min")) else float(row["duree_min"]),
            "import_2024",
            "import_initial",
            now,
        )
        for _, row in df.iterrows()
    ]
    conn.executemany(
        "INSERT INTO evenements (date, ligne, four, probleme, equipement, famille, "
        "duree_min, source, saisi_par, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        records,
    )
    conn.commit()


def insert_evenement(*, date, ligne, probleme, equipement, famille, duree_min, saisi_par="—") -> int:
    if ligne not in LIGNE_TO_FOUR:
        raise ValueError(f"Ligne inconnue : {ligne!r}. Lignes valides : {LIGNES}")
    if duree_min is not None and duree_min <= 0:
        raise ValueError("La durée d'arrêt doit être un nombre positif de minutes.")
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO evenements (date, ligne, four, probleme, equipement, famille, "
            "duree_min, source, saisi_par, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                pd.Timestamp(date).strftime("%Y-%m-%d"),
                ligne,
                LIGNE_TO_FOUR[ligne],
                probleme,
                equipement,
                famille,
                float(duree_min) if duree_min is not None else None,
                "manuel",
                saisi_par,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def fetch_evenements(date_from=None, date_to=None, lignes: list[str] | None = None) -> pd.DataFrame:
    conn = get_connection()
    try:
        query = "SELECT * FROM evenements WHERE 1=1"
        params: list = []
        if date_from is not None:
            query += " AND date >= ?"
            params.append(pd.Timestamp(date_from).strftime("%Y-%m-%d"))
        if date_to is not None:
            query += " AND date <= ?"
            params.append(pd.Timestamp(date_to).strftime("%Y-%m-%d"))
        if lignes:
            placeholders = ",".join("?" * len(lignes))
            query += f" AND ligne IN ({placeholders})"
            params.extend(lignes)
        df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
        return df
    finally:
        conn.close()


def count_manual_declarations() -> int:
    conn = get_connection()
    try:
        (n,) = conn.execute("SELECT COUNT(*) FROM evenements WHERE source = 'manuel'").fetchone()
        return n
    finally:
        conn.close()
