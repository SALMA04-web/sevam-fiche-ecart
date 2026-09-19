"""
Moteur de calcul — indicateurs de fiabilité, Pareto, criticité AMDEC-lite.

Toutes les fonctions sont pures (DataFrame en entrée, résultat en sortie, aucun
accès disque ni à Streamlit) pour rester testables unitairement — voir
tests/test_kpi.py, qui rejoue notamment l'exemple du Four U2 (92 jours, 3 lignes,
14 pannes, 63,9 h d'arrêt) pour vérifier que MTBF/MTTR/disponibilité retombent
bien sur les valeurs déjà validées lors de la soutenance PFA.

Convention retenue (cohérente avec la méthode déjà présentée) :
  - heures d'ouverture = nb_jours x 24 x nb_lignes considérées (fonctionnement continu)
  - temps de fonctionnement = heures d'ouverture - temps d'arrêt cumulé
  - MTBF = temps de fonctionnement / nombre de pannes
  - MTTR = temps d'arrêt cumulé (heures) / nombre de pannes
  - Disponibilité = temps de fonctionnement / heures d'ouverture  (= MTBF / (MTBF + MTTR))
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class Fiabilite:
    date_debut: pd.Timestamp
    date_fin: pd.Timestamp
    lignes: list
    nb_jours: int
    nb_lignes: int
    heures_ouverture: float
    nb_pannes: int
    temps_arret_h: float
    temps_fonctionnement_h: float
    mtbf_h: float | None
    mttr_h: float | None
    disponibilite: float | None


def _filter_periode(df: pd.DataFrame, date_from, date_to, lignes=None) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    if date_from is not None:
        out = out[out["date"] >= pd.Timestamp(date_from)]
    if date_to is not None:
        out = out[out["date"] <= pd.Timestamp(date_to)]
    if lignes:
        out = out[out["ligne"].isin(lignes)]
    return out


def calc_fiabilite(events: pd.DataFrame, date_from, date_to, lignes: list[str]) -> Fiabilite:
    """Calcule MTBF / MTTR / disponibilité sur une période et un ensemble de lignes.

    `events` doit contenir au moins les colonnes : date, ligne, duree_min.
    Les événements sans durée exploitable (NaN) sont comptés comme pannes
    (ils ont bien eu lieu) mais n'entrent pas dans le temps d'arrêt cumulé —
    ce choix est documenté et cohérent avec le rapport de qualité des données.
    """
    date_from = pd.Timestamp(date_from)
    date_to = pd.Timestamp(date_to)
    nb_jours = (date_to - date_from).days + 1
    nb_lignes = len(lignes)
    heures_ouverture = nb_jours * 24 * nb_lignes

    sub = _filter_periode(events, date_from, date_to, lignes)
    nb_pannes = len(sub)
    temps_arret_h = sub["duree_min"].fillna(0).sum() / 60.0
    temps_fonctionnement_h = heures_ouverture - temps_arret_h

    mtbf = temps_fonctionnement_h / nb_pannes if nb_pannes else None
    mttr = temps_arret_h / nb_pannes if nb_pannes else None
    dispo = temps_fonctionnement_h / heures_ouverture if heures_ouverture else None

    return Fiabilite(
        date_debut=date_from, date_fin=date_to, lignes=lignes, nb_jours=nb_jours,
        nb_lignes=nb_lignes, heures_ouverture=heures_ouverture, nb_pannes=nb_pannes,
        temps_arret_h=temps_arret_h, temps_fonctionnement_h=temps_fonctionnement_h,
        mtbf_h=mtbf, mttr_h=mttr, disponibilite=dispo,
    )


def pareto_table(events: pd.DataFrame, date_from, date_to, lignes: list[str],
                  group_col: str = "famille") -> pd.DataFrame:
    """Table de Pareto (nombre de pannes + durée cumulée) par famille d'équipement,
    triée par durée cumulée décroissante, avec pourcentage cumulé."""
    sub = _filter_periode(events, date_from, date_to, lignes)
    sub = sub.dropna(subset=[group_col, "duree_min"])
    if sub.empty:
        return pd.DataFrame(columns=[group_col, "nb_pannes", "duree_totale_min", "pct", "pct_cumule"])
    g = sub.groupby(group_col).agg(
        nb_pannes=("duree_min", "size"),
        duree_totale_min=("duree_min", "sum"),
    ).reset_index()
    g = g.sort_values("duree_totale_min", ascending=False).reset_index(drop=True)
    total = g["duree_totale_min"].sum()
    g["pct"] = g["duree_totale_min"] / total * 100
    g["pct_cumule"] = g["pct"].cumsum()
    return g


def amdec_table(events: pd.DataFrame, date_from, date_to, lignes: list[str],
                 group_col: str = "equipement", n_bins: int = 5) -> pd.DataFrame:
    """Grille de criticité Fréquence x Gravité par équipement, sur données réelles.

    NB : le troisième facteur AMDEC classique, la Détection, n'est pas calculé —
    aucune donnée de détection automatique n'existe aujourd'hui chez SEVAM
    (c'est justement une des actions proposées). La grille combine donc
    Fréquence x Gravité moyenne, sur une échelle 1-5 par quantiles.
    """
    sub = _filter_periode(events, date_from, date_to, lignes)
    sub = sub.dropna(subset=[group_col, "duree_min"])
    if sub.empty:
        return pd.DataFrame(columns=[group_col, "frequence", "gravite_moyenne_min",
                                      "duree_totale_min", "rang_f", "rang_g", "criticite"])
    g = sub.groupby(group_col).agg(
        frequence=("duree_min", "size"),
        gravite_moyenne_min=("duree_min", "mean"),
        duree_totale_min=("duree_min", "sum"),
    ).reset_index()

    def _qbin(series: pd.Series) -> pd.Series:
        try:
            return pd.qcut(series, n_bins, labels=range(1, n_bins + 1), duplicates="drop").astype(int)
        except ValueError:
            # pas assez de valeurs distinctes pour n_bins quantiles
            ranks = series.rank(method="dense")
            return np.ceil(ranks / ranks.max() * n_bins).astype(int)

    g["rang_f"] = _qbin(g["frequence"])
    g["rang_g"] = _qbin(g["gravite_moyenne_min"])
    g["criticite"] = g["rang_f"] * g["rang_g"]
    return g.sort_values(["criticite", "duree_totale_min"], ascending=[False, False]).reset_index(drop=True)


def simuler_incident(events: pd.DataFrame, date_from, date_to, lignes: list[str],
                      duree_min_supplementaire: float) -> tuple[Fiabilite, Fiabilite]:
    """Compare la fiabilité de la période avec / sans une panne hypothétique
    supplémentaire (même lignes, même période), pour le simulateur d'incident."""
    avant = calc_fiabilite(events, date_from, date_to, lignes)
    hypothese = pd.concat([
        _filter_periode(events, date_from, date_to, lignes),
        pd.DataFrame([{"date": date_to, "ligne": lignes[0] if lignes else None,
                        "duree_min": duree_min_supplementaire}]),
    ], ignore_index=True)
    apres = calc_fiabilite(hypothese, date_from, date_to, lignes)
    return avant, apres


def cout_arrets(events: pd.DataFrame, date_from, date_to, lignes: list[str],
                 cout_par_minute: float) -> dict:
    sub = _filter_periode(events, date_from, date_to, lignes)
    total_min = sub["duree_min"].fillna(0).sum()
    return {
        "total_minutes": total_min,
        "total_heures": total_min / 60.0,
        "cout_estime": total_min * cout_par_minute,
    }
