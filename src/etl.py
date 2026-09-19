"""
ETL — nettoyage et unification des données réelles SEVAM.

Sources brutes (fournies par l'encadrant) :
  - data/raw/Arret_2024.xlsx            : journal détaillé des arrêts, 1 feuille par ligne
                                           (11, 12, 13, 21, 22, 23), 1 ligne = 1 événement.
  - data/raw/Suivi_arrets_2025.xlsx     : suivi quotidien agrégé (minutes d'arrêt par ligne
                                           et par jour), 1 feuille par mois (Janvier à
                                           Septembre 2025).

Ce script ne fait AUCUNE hypothèse silencieuse : chaque correction appliquée à une valeur
brute (date aberrante, texte à la place d'un nombre, cellule Excel mal typée) est journalisée
dans data/rapport_qualite_donnees.csv, avec la valeur d'origine et la valeur corrigée, pour que
le résultat reste vérifiable et présentable à SEVAM.

Sorties (dans data/) :
  - evenements_2024.csv          : journal détaillé unifié, 2024, 6 lignes de production.
  - suivi_quotidien_2025.csv     : format long (date, ligne, four, minutes), Jan-Sept 2025.
  - rapport_qualite_donnees.csv  : liste de toutes les corrections/exclusions appliquées.

Lancer avec :  python3 src/etl.py
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUT_DIR = BASE_DIR / "data"

ARRET_2024_XLSX = RAW_DIR / "Arret_2024.xlsx"
SUIVI_2025_XLSX = RAW_DIR / "Suivi_arrets_2025.xlsx"

# Mapping feuille -> (ligne, four). Les fours n'ont que 2 lignes de production réelles
# chez SEVAM sur ce périmètre : Four 1 (L11, L12, L13) et Four 2 (L21, L22, L23).
SHEET_TO_LIGNE = {
    "11": ("L11", "Four 1"),
    "12": ("L12", "Four 1"),
    "13": ("L13", "Four 1"),
    "21": ("L21", "Four 2"),
    "22": ("L22", "Four 2"),
    "23": ("L23", "Four 2"),
}

MOIS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "aout": 8, "août": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "décembre": 12, "decembre": 12,
}

EXCEL_EPOCH = datetime(1899, 12, 30)

quality_log: list[dict] = []


def log_fix(fichier, feuille, champ, ligne_excel, valeur_originale, valeur_corrigee, motif):
    quality_log.append({
        "fichier": fichier,
        "feuille": feuille,
        "champ": champ,
        "ligne_excel_index": ligne_excel,
        "valeur_originale": str(valeur_originale),
        "valeur_corrigee": str(valeur_corrigee),
        "motif": motif,
    })


# ---------------------------------------------------------------------------
# 1) Journal détaillé des arrêts — Arret_2024.xlsx
# ---------------------------------------------------------------------------

def _clean_duree(raw_val, feuille, excel_row):
    """Nettoie une valeur de durée (minutes) potentiellement mal saisie.

    Cas rencontrés dans le fichier réel :
      - valeur numérique correcte -> inchangée
      - lettre 'O' à la place du chiffre '0' (ex: "1O" -> 10)
      - cellule Excel mal typée en date (ex: 1900-05-04) -> le nombre de jours
        depuis l'époque Excel (1899-12-30) redonne la vraie valeur en minutes
      - valeur manquante / illisible -> NaN (exclue des totaux, événement conservé)
    """
    if pd.isna(raw_val):
        log_fix("Arret_2024.xlsx", feuille, "Temps d'arrêt (min)", excel_row,
                "(vide)", "NaN", "durée manquante dans le fichier source, événement conservé mais exclu des totaux")
        return None
    if isinstance(raw_val, (int, float)):
        return float(raw_val)
    if isinstance(raw_val, (pd.Timestamp, datetime)):
        serial = (raw_val - EXCEL_EPOCH).days
        log_fix("Arret_2024.xlsx", feuille, "Temps d'arrêt (min)", excel_row,
                raw_val, serial,
                "cellule interprétée comme une date par Excel : valeur reconvertie "
                "en nombre de minutes (jours depuis l'époque Excel 1899-12-30)")
        return float(serial)
    s = str(raw_val).strip()
    fixed = s.replace("O", "0").replace("o", "0").replace(",", ".")
    try:
        val = float(fixed)
    except ValueError:
        log_fix("Arret_2024.xlsx", feuille, "Temps d'arrêt (min)", excel_row,
                raw_val, "NaN", "valeur non numérique et non récupérable, exclue des totaux")
        return None
    if fixed != s:
        log_fix("Arret_2024.xlsx", feuille, "Temps d'arrêt (min)", excel_row,
                raw_val, val, "caractère non numérique corrigé (ex. lettre 'O' pour le chiffre '0')")
    return val


def _clean_date(raw_val, feuille, excel_row, expected_year=2024):
    """Corrige une date dont l'année est manifestement une erreur de saisie
    (le mois et le jour restent valides), en la ramenant à l'année attendue."""
    ts = pd.to_datetime(raw_val, errors="coerce")
    if pd.isna(ts):
        log_fix("Arret_2024.xlsx", feuille, "Date", excel_row, raw_val, "NaT",
                "date illisible, ligne exclue")
        return pd.NaT
    if ts.year != expected_year:
        try:
            corrected = ts.replace(year=expected_year)
        except ValueError:
            # 29 février sur une année non bissextile par ex.
            log_fix("Arret_2024.xlsx", feuille, "Date", excel_row, raw_val, "NaT",
                    f"année aberrante ({ts.year}) et jour/mois non reportable sur {expected_year}, ligne exclue")
            return pd.NaT
        log_fix("Arret_2024.xlsx", feuille, "Date", excel_row, ts.date(), corrected.date(),
                f"année de saisie aberrante ({ts.year} au lieu de {expected_year}), "
                "corrigée en conservant le jour et le mois")
        return corrected
    return ts


def _normalize_text(val):
    if pd.isna(val):
        return None
    return re.sub(r"\s+", " ", str(val)).strip()


def load_arrets_2024() -> pd.DataFrame:
    xl = pd.ExcelFile(ARRET_2024_XLSX)
    rows = []
    for sheet in xl.sheet_names:
        ligne, four = SHEET_TO_LIGNE[sheet]
        df = pd.read_excel(ARRET_2024_XLSX, sheet_name=sheet)
        df.columns = [str(c).strip() for c in df.columns]
        eq_col = "Équipement/N° section" if "Équipement/N° section" in df.columns else "Équipement"
        dur_col = "Temps d'arrêt (min)"
        for excel_row, r in df.iterrows():
            date_clean = _clean_date(r["Date"], sheet, excel_row + 2)  # +2 : entête + index 0
            duree_clean = _clean_duree(r[dur_col], sheet, excel_row + 2)
            if pd.isna(date_clean):
                continue
            rows.append({
                "date": date_clean.normalize(),
                "ligne": ligne,
                "four": four,
                "probleme": _normalize_text(r.get("Problème")),
                "equipement": _normalize_text(r.get(eq_col)),
                "famille": _normalize_text(r.get("Famille")),
                "duree_min": duree_clean,
                "source": "import_2024",
            })
    out = pd.DataFrame(rows)
    # clé normalisée pour regrouper "Section n°4" / "section n°4" / espaces multiples
    out["famille_norm"] = out["famille"].str.lower().str.strip()
    out["equipement_norm"] = out["equipement"].str.lower().str.strip()
    # étiquette d'affichage = variante la plus fréquente pour chaque clé normalisée
    for col in ["famille", "equipement"]:
        norm_col = f"{col}_norm"
        display_map = (
            out.dropna(subset=[col])
            .groupby(norm_col)[col]
            .agg(lambda s: s.value_counts().idxmax())
        )
        out[f"{col}_affichage"] = out[norm_col].map(display_map)
    out.insert(0, "id", range(1, len(out) + 1))
    return out


# ---------------------------------------------------------------------------
# 2) Suivi quotidien agrégé — Suivi_arrets_2025.xlsx
# ---------------------------------------------------------------------------

def _parse_mois_from_sheetname(sheet_name: str) -> tuple[int, int]:
    m = re.search(r"([A-Za-zéû]+)\s*25", sheet_name)
    mois_txt = m.group(1).lower()
    if mois_txt not in MOIS_FR:
        raise ValueError(f"Mois non reconnu dans le nom de feuille : {sheet_name!r}")
    return MOIS_FR[mois_txt], 2025


LINE_ROW_LABELS = {"L11": "L11", "L12": "L12", "L13": "L13", "L21": "L21", "L22": "L22", "L23": "L23"}
LIGNE_TO_FOUR = {"L11": "Four 1", "L12": "Four 1", "L13": "Four 1",
                 "L21": "Four 2", "L22": "Four 2", "L23": "Four 2"}


def load_suivi_2025() -> pd.DataFrame:
    xl = pd.ExcelFile(SUIVI_2025_XLSX)
    rows = []
    for sheet in xl.sheet_names:
        mois, annee = _parse_mois_from_sheetname(sheet)
        grid = pd.read_excel(SUIVI_2025_XLSX, sheet_name=sheet, header=None)
        date_row = grid.iloc[2]
        # colonnes de dates : toutes les cellules de la ligne d'entête qui sont des Timestamp
        date_cols = [c for c in grid.columns if isinstance(date_row[c], (pd.Timestamp, datetime))]
        for row_idx in range(grid.shape[0]):
            label = grid.iat[row_idx, 0]
            if not isinstance(label, str):
                continue
            label = label.strip()
            if label not in LINE_ROW_LABELS:
                continue
            ligne = LINE_ROW_LABELS[label]
            for c in date_cols:
                date_val = date_row[c]
                minute_val = grid.iat[row_idx, c]
                if pd.isna(minute_val):
                    continue
                if not isinstance(minute_val, (int, float)):
                    log_fix("Suivi_arrets_2025.xlsx", sheet, "minutes/jour", f"{label} col {c}",
                            minute_val, "NaN", "valeur non numérique dans le suivi quotidien, exclue")
                    continue
                rows.append({
                    "date": pd.Timestamp(date_val).normalize(),
                    "ligne": ligne,
                    "four": LIGNE_TO_FOUR[ligne],
                    "minutes_arret": float(minute_val),
                })
    out = pd.DataFrame(rows).drop_duplicates(subset=["date", "ligne"]).sort_values(["date", "ligne"])
    return out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def comparer_sources_2024(evt: pd.DataFrame) -> pd.DataFrame:
    """Compare, pour chaque ligne et sur Janvier-Septembre 2024 (période commune aux deux
    fichiers), le journal détaillé des arrêts (Arret_2024.xlsx, un événement = une ligne) à la
    colonne de référence "Total des arrêts 2024 (min)" intégrée dans le fichier de suivi
    quotidien 2025 (une valeur par ligne et par mois, sommée sur les 9 mois disponibles).

    Les deux totaux ne coïncident pas (voir pages/8_Qualite_des_donnees.py pour l'interprétation) :
    ce tableau sert de preuve chiffrée, reproductible depuis les fichiers bruts, plutôt que
    d'affirmation non vérifiable.
    """
    xl = pd.ExcelFile(SUIVI_2025_XLSX)
    ref_rows = []
    for sheet in xl.sheet_names:
        grid = pd.read_excel(SUIVI_2025_XLSX, sheet_name=sheet, header=None)
        header_row = grid.iloc[2]
        col_2024 = None
        for c in grid.columns:
            val = header_row[c]
            if (isinstance(val, str) and "2024" in val and "arr" in val.lower()
                    and "total" in val.lower() and "écart" not in val.lower() and "ecart" not in val.lower()
                    and "seuil" not in val.lower()):
                col_2024 = c
                break
        if col_2024 is None:
            continue
        for row_idx in range(grid.shape[0]):
            label = grid.iat[row_idx, 0]
            if not isinstance(label, str):
                continue
            label = label.strip()
            if label not in LINE_ROW_LABELS:
                continue
            val = grid.iat[row_idx, col_2024]
            if isinstance(val, (int, float)):
                ref_rows.append({"ligne": LINE_ROW_LABELS[label], "mois_feuille": sheet, "valeur_2024": val})

    ref = pd.DataFrame(ref_rows).groupby("ligne")["valeur_2024"].sum().rename("suivi_ref_2024_min")

    sub = evt[evt["date"] <= "2024-09-30"].copy()
    is_section = sub["famille_affichage"].fillna("").str.match(r"Section n°\d+")
    detail = sub.groupby("ligne")["duree_min"].sum().rename("journal_detaille_2024_min")
    detail_non_section = sub[~is_section].groupby("ligne")["duree_min"].sum().rename("journal_hors_section_min")
    detail_section = sub[is_section].groupby("ligne")["duree_min"].sum().rename("journal_section_min")

    out = pd.concat([detail, detail_non_section, detail_section, ref], axis=1).reset_index()
    out = out.rename(columns={"index": "ligne"})
    out["ecart_ratio"] = out["journal_detaille_2024_min"] / out["suivi_ref_2024_min"]
    return out.sort_values("ligne")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    evt = load_arrets_2024()
    evt.to_csv(OUT_DIR / "evenements_2024.csv", index=False)
    print(f"evenements_2024.csv : {len(evt)} événements, "
          f"{evt['duree_min'].notna().sum()} avec durée exploitable, "
          f"total {evt['duree_min'].sum():.0f} min")

    suivi = load_suivi_2025()
    suivi.to_csv(OUT_DIR / "suivi_quotidien_2025.csv", index=False)
    print(f"suivi_quotidien_2025.csv : {len(suivi)} lignes (jour x ligne), "
          f"total {suivi['minutes_arret'].sum():.0f} min")

    comparaison = comparer_sources_2024(evt)
    comparaison.to_csv(OUT_DIR / "comparaison_sources_2024.csv", index=False)
    print(f"comparaison_sources_2024.csv : écart journal détaillé / suivi de référence "
          f"= x{comparaison['journal_detaille_2024_min'].sum() / comparaison['suivi_ref_2024_min'].sum():.2f} "
          f"en cumulé sur Janvier-Septembre 2024")

    quality_df = pd.DataFrame(quality_log)
    quality_df.to_csv(OUT_DIR / "rapport_qualite_donnees.csv", index=False)
    print(f"rapport_qualite_donnees.csv : {len(quality_df)} corrections/exclusions journalisées")


if __name__ == "__main__":
    main()
