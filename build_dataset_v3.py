# -*- coding: utf-8 -*-
"""Génère Dataset_Ecarts_Production_SEVAM.csv à partir du catalogue réel SEVAM."""
import csv
import random
from datetime import date, timedelta
from collections import Counter

import catalogue_sevam as c

random.seed(21)

causes = {
    "FOUR": "Arret four non planifie",
    "APPRO": "Retard livraison matiere premiere",
    "SERIE": "Changement de serie non anticipe",
    "QUALITE": "Rebuts / non-conformites",
    "DECOR": "Incident atelier decor (casse, defaut d'impression)",
    "AUTRE": "Cause diverse",
}
cause_codes_prod = ["FOUR", "APPRO", "SERIE", "QUALITE", "AUTRE"]
cause_weights_prod = [0.30, 0.22, 0.18, 0.20, 0.10]

start = date(2026, 7, 1)
end = date(2026, 8, 31)
n_days = (end - start).days + 1

articles_gob = c.ARTICLES_BY_FAMILLE["Gobeleterie (verres)"]
articles_vc = c.ARTICLES_BY_FAMILLE["Verre creux (bouteilles / pots)"]

rows = []
of_counter = 400
for day_offset in range(n_days):
    d = start + timedelta(days=day_offset)
    if d.weekday() == 6:
        continue
    n_of_today = random.choice([3, 4, 4, 5])
    for _ in range(n_of_today):
        of_counter += 1
        of_num = f"OF-2026-{of_counter}"
        ligne, four = random.choice(c.LIGNES)
        four_info = c.FOURS[four]
        site = four_info["site"]
        departement = four_info["departement"]

        # article cohérent avec le département du four
        pool = articles_gob if departement == "Gobeleterie" else articles_vc
        art = random.choice(pool)
        ref = art["article"]
        poids = art["poids"] or 200

        planifiee = random.choice([6000, 8000, 9000, 10000, 12000, 15000, 18000])

        # passage éventuel à l'atelier décor (transverse, indépendant du four)
        decore = random.random() < 0.30

        en_ecart = random.random() < 0.42
        if en_ecart:
            if decore and random.random() < 0.35:
                cause = "DECOR"
            else:
                cause = random.choices(cause_codes_prod, weights=cause_weights_prod, k=1)[0]
            ecart_pct_base = {
                "FOUR": -0.11, "APPRO": -0.07, "SERIE": -0.05,
                "QUALITE": -0.04, "DECOR": -0.06, "AUTRE": -0.025,
            }[cause]
            ecart_pct = ecart_pct_base + random.uniform(-0.02, 0.015)
        else:
            cause = ""
            ecart_pct = random.uniform(-0.02, 0.01)

        realisee = max(0, round(planifiee * (1 + ecart_pct)))
        ecart = realisee - planifiee
        statut = "A traiter" if abs(ecart_pct) > 0.05 else "OK"

        rows.append({
            "N_OF": of_num,
            "Date": d.isoformat(),
            "Annee": d.year,
            "Mois": d.strftime("%Y-%m"),
            "Semaine": d.isocalendar()[1],
            "Ligne": ligne,
            "Four": four,
            "Site": site,
            "Departement": departement,
            "Reference_Article": ref,
            "Famille_Article": art["famille"],
            "Decore": "OUI" if decore else "NON",
            "Marque_Decor": art["marque"] if (decore and art["marque"]) else ("" if not decore else ""),
            "Qte_Planifiee": planifiee,
            "Qte_Realisee": realisee,
            "Ecart_Unites": ecart,
            "Ecart_Pct": round(ecart_pct * 100, 2),
            "Code_Cause": cause,
            "Libelle_Cause": causes.get(cause, ""),
            "Statut": statut,
        })

fieldnames = list(rows[0].keys())
out_path = "Dataset_Ecarts_Production_SEVAM.csv"
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
    w.writeheader()
    w.writerows(rows)

print(f"{len(rows)} lignes generees, du {start} au {end}")
print("Par four:", Counter(r["Four"] for r in rows))
print("Par departement:", Counter(r["Departement"] for r in rows))
n_ecart = sum(1 for r in rows if r["Code_Cause"])
print(f"{n_ecart} OF en ecart sur {len(rows)} ({n_ecart/len(rows)*100:.1f}%)")
n_decore = sum(1 for r in rows if r["Decore"] == "OUI")
print(f"{n_decore} OF passes par l'atelier decor ({n_decore/len(rows)*100:.1f}%)")
