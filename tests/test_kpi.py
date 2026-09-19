"""Tests unitaires du moteur de calcul (src/kpi.py).

Lancer avec : python3 -m pytest tests/ -v   (ou : python3 tests/test_kpi.py)
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import kpi  # noqa: E402


def make_events(rows):
    return pd.DataFrame(rows, columns=["date", "ligne", "duree_min", "famille", "equipement"])


def test_fiabilite_cas_four_u2_reference():
    """Rejoue l'exemple du Four U2 déjà présenté en soutenance : 92 jours,
    3 lignes, 14 pannes, 63,9 h d'arrêt cumulé -> MTBF ~468,6 h, MTTR ~4,6 h,
    disponibilité ~99,04 %. Sert de non-régression : si la formule change,
    ce test doit continuer à retomber sur des valeurs très proches."""
    date_from = "2024-06-01"
    date_to = "2024-08-31"  # 92 jours inclus
    total_min = 63.9 * 60  # 3834 minutes réparties sur 14 pannes
    par_panne = total_min / 14
    rows = [
        {"date": pd.Timestamp(date_from) + pd.Timedelta(days=i * 6), "ligne": "L21",
         "duree_min": par_panne, "famille": "test", "equipement": "test"}
        for i in range(14)
    ]
    events = make_events(rows)

    fiab = kpi.calc_fiabilite(events, date_from, date_to, lignes=["L21", "L22", "L23"])

    assert fiab.nb_jours == 92
    assert fiab.heures_ouverture == 92 * 24 * 3  # 6624
    assert fiab.nb_pannes == 14
    assert abs(fiab.temps_arret_h - 63.9) < 0.01
    assert abs(fiab.mtbf_h - 468.58) < 0.5
    assert abs(fiab.mttr_h - 4.564) < 0.01
    assert abs(fiab.disponibilite * 100 - 99.04) < 0.05


def test_fiabilite_aucune_panne():
    events = make_events([])
    fiab = kpi.calc_fiabilite(events, "2024-01-01", "2024-01-10", lignes=["L11"])
    assert fiab.nb_pannes == 0
    assert fiab.mtbf_h is None
    assert fiab.mttr_h is None
    assert fiab.disponibilite == 1.0  # aucun arrêt observé sur la période


def test_pareto_tri_et_pourcentage_cumule():
    rows = [
        {"date": "2024-01-01", "ligne": "L11", "duree_min": 100, "famille": "A", "equipement": "eqA"},
        {"date": "2024-01-02", "ligne": "L11", "duree_min": 300, "famille": "B", "equipement": "eqB"},
        {"date": "2024-01-03", "ligne": "L11", "duree_min": 100, "famille": "A", "equipement": "eqA"},
    ]
    events = make_events(rows)
    table = kpi.pareto_table(events, "2024-01-01", "2024-01-31", lignes=["L11"], group_col="famille")

    assert list(table["famille"]) == ["B", "A"]  # B (300) avant A (200)
    assert table.loc[0, "nb_pannes"] == 1
    assert table.loc[1, "nb_pannes"] == 2
    assert abs(table["pct"].sum() - 100) < 1e-9
    assert table.loc[len(table) - 1, "pct_cumule"] == 100.0


def test_amdec_criticite_favorise_frequence_et_gravite():
    rows = []
    # équipement "X" : pannes fréquentes et longues -> devrait dominer la criticité
    for i in range(10):
        rows.append({"date": f"2024-02-{i+1:02d}", "ligne": "L12", "duree_min": 120,
                     "famille": "f", "equipement": "X"})
    # équipement "Y" : une seule panne courte
    rows.append({"date": "2024-02-15", "ligne": "L12", "duree_min": 5,
                 "famille": "f", "equipement": "Y"})
    events = make_events(rows)

    table = kpi.amdec_table(events, "2024-02-01", "2024-02-28", lignes=["L12"], group_col="equipement")
    assert table.iloc[0]["equipement"] == "X"
    assert table.iloc[0]["criticite"] >= table.iloc[-1]["criticite"]


def test_cout_arrets_proportionnel():
    rows = [{"date": "2024-01-01", "ligne": "L11", "duree_min": 100, "famille": "f", "equipement": "e"}]
    events = make_events(rows)
    result = kpi.cout_arrets(events, "2024-01-01", "2024-01-31", lignes=["L11"], cout_par_minute=2.5)
    assert result["total_minutes"] == 100
    assert result["cout_estime"] == 250.0


def _run_all():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passés")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    _run_all()
