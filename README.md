# Suivi des arrêts de ligne — SEVAM

Application de suivi et d'analyse des arrêts de production, construite à partir des
**données réelles** transmises par l'encadrant (journal détaillé des arrêts 2024 et suivi
quotidien agrégé 2025). Elle prolonge le prototype présenté en soutenance PFA en remplaçant
les données de démonstration par les vraies données SEVAM, et le stockage en mémoire
temporaire par une base de données réellement persistante.

## 1. Ce que fait l'application

8 pages, accessibles depuis le menu de gauche :

| Page | Contenu |
|---|---|
| **Accueil** | Vue d'ensemble : événements enregistrés, temps d'arrêt cumulé, disponibilité globale, évolution mensuelle. |
| **Nouvelle déclaration** | Formulaire pour déclarer un nouvel arrêt (ligne, équipement, durée, description). Enregistrement **permanent** en base. |
| **Historique** | Recherche et filtrage de tous les événements (import 2024 + déclarations manuelles), export CSV. |
| **Suivi quotidien 2025** | Reprise du suivi journalier réel (Jan-Sept 2025), comparé au seuil de référence SEVAM (18 min/jour/ligne). |
| **Analyse Pareto** | Catégories (famille ou équipement) qui concentrent le plus de temps d'arrêt (règle des 80/20). |
| **Fiabilité** | MTBF, MTTR, disponibilité — même méthode de calcul que celle présentée et validée en soutenance. |
| **AMDEC** | Grille de criticité des équipements (Fréquence x Gravité) et simulateur d'impact d'un incident hypothétique. |
| **Impact économique** | Estimation du coût des arrêts, à partir d'un coût par minute **réglable** (aucun coût n'étant fourni dans les fichiers sources). |
| **Qualité des données** | Transparence totale : toutes les corrections appliquées aux données brutes, et l'écart constaté entre les deux fichiers sources, avec l'interprétation la plus probable. |

## 2. Installation et lancement

Prérequis : Python 3.10 ou plus récent.

```bash
# 1) installer les dépendances (une seule fois)
pip install -r requirements.txt

# 2) (re)générer les données nettoyées à partir des fichiers Excel bruts (une seule fois,
#    ou après avoir remplacé les fichiers dans data/raw/ par une version plus récente)
python3 src/etl.py

# 3) lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement dans le navigateur (par défaut sur
`http://localhost:8501`). Elle fonctionne aussi bien sur le poste de l'encadrant que sur un
serveur interne SEVAM.

### Mettre à jour les données sources

Pour repartir de fichiers Excel plus récents (par exemple `Suivi_arrets_2025.xlsx` complété
avec de nouveaux mois) :

1. Remplacer les fichiers dans `data/raw/` (mêmes noms, mêmes structures de feuilles).
2. Relancer `python3 src/etl.py` — cela régénère `data/evenements_2024.csv`,
   `data/suivi_quotidien_2025.csv`, `data/rapport_qualite_donnees.csv` et
   `data/comparaison_sources_2024.csv`.
3. Redémarrer l'application (ou simplement rafraîchir la page si elle tourne déjà).

**Attention** : relancer l'ETL ne touche jamais aux déclarations saisies manuellement dans
l'application (`data/sevam.db`) — seul l'import initial 2024 est reconstruit à partir des
fichiers Excel.

### Déploiement

Deux options simples, sans changement de code :

- **Streamlit Community Cloud** (gratuit, rapide à mettre en place) : pousser ce dossier sur
  un dépôt Git (privé de préférence, les données étant internes à SEVAM) et connecter le
  dépôt sur [streamlit.io/cloud](https://streamlit.io/cloud). Le fichier `data/sevam.db`
  étant sur disque local au service, prévoir une sauvegarde régulière (voir section 4).
- **Serveur interne SEVAM** : installer Python + les dépendances sur un poste ou serveur
  accessible sur le réseau interne, puis lancer `streamlit run app.py --server.port 8501
  --server.address 0.0.0.0` pour le rendre accessible aux autres postes du réseau.

## 3. Structure du projet

```
real_app/
├── app.py                        # page d'accueil
├── common.py                     # bootstrap partagé (config page, cache, filtres)
├── requirements.txt
├── data/
│   ├── raw/                      # fichiers Excel originaux fournis par l'encadrant
│   ├── evenements_2024.csv       # journal détaillé nettoyé (généré par src/etl.py)
│   ├── suivi_quotidien_2025.csv  # suivi quotidien nettoyé (généré par src/etl.py)
│   ├── rapport_qualite_donnees.csv     # corrections appliquées (généré par src/etl.py)
│   ├── comparaison_sources_2024.csv    # écart entre les 2 sources (généré par src/etl.py)
│   └── sevam.db                  # base SQLite : import 2024 + déclarations manuelles
├── src/
│   ├── etl.py                    # nettoyage/unification des fichiers Excel bruts
│   ├── db.py                     # accès à la base SQLite (persistance réelle)
│   ├── kpi.py                    # calculs purs : MTBF/MTTR/dispo, Pareto, AMDEC, coûts
│   └── config.py                 # constantes partagées (lignes, fours, palette de couleurs)
├── pages/                        # les 8 pages de l'application (voir tableau ci-dessus)
└── tests/
    ├── test_kpi.py               # tests unitaires du moteur de calcul (5 tests)
    └── smoke_app.py              # test de bout en bout : chaque page se charge sans erreur
```

## 4. Fiabilité et vérifications effectuées

- **`python3 tests/test_kpi.py`** : 5 tests unitaires sur le moteur de calcul, dont un test
  de non-régression qui rejoue l'exemple du Four U2 déjà validé en soutenance PFA (92 jours,
  3 lignes, 14 pannes, 63,9 h d'arrêt → MTBF ≈ 468,6 h, MTTR ≈ 4,6 h, disponibilité ≈ 99,04 %).
- **`python3 tests/smoke_app.py`** : charge automatiquement les 8 pages de l'application
  (framework `streamlit.testing`) et vérifie qu'aucune ne lève d'exception ; un test
  end-to-end complémentaire a également validé le cycle complet déclaration → écriture en
  base → réapparition dans l'historique.
- Toute correction apportée aux données sources est journalisée et consultable dans la page
  **Qualité des données** — aucune valeur n'est modifiée sans laisser de trace.

**Sauvegarde recommandée** : `data/sevam.db` est le seul fichier qui grandit avec l'usage
(chaque nouvelle déclaration). Prévoir une copie régulière de ce fichier (ou un export CSV
depuis la page Historique) selon la politique de sauvegarde de SEVAM.

## 5. Points importants à partager avec l'encadrant

- **Écart entre les deux fichiers sources (2024)** : le journal détaillé des arrêts totalise,
  sur Janvier-Septembre 2024, environ **4 fois plus** de minutes d'arrêt que la colonne de
  référence "Total des arrêts 2024" intégrée dans le fichier de suivi 2025 (106 500 min contre
  26 000 min environ, avec un écart qui varie de x2,3 à x6,2 selon la ligne). L'hypothèse d'un
  simple filtre "arrêt de section vs arrêt de ligne entière" a été testée et ne suffit pas à
  l'expliquer complètement. L'explication la plus probable, détaillée dans la page **Qualité
  des données**, est que les deux fichiers proviennent de deux pratiques de suivi
  indépendantes (une équipe maintenance vs une équipe production, avec des critères de saisie
  différents) — **à confirmer directement auprès des équipes concernées**.
- Cette clarification rejoint directement l'**action 1** du rapport PFA (codes cause
  standardisés) : une fois les deux pratiques harmonisées, ce type d'écart disparaîtra de
  lui-même.
- L'application est prête à recevoir de nouvelles déclarations dès maintenant : aucune
  configuration supplémentaire n'est nécessaire.
