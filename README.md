# SEVAM — Outil de pilotage (arrêts · production · commercial)

Application unique regroupant, sur des **données réelles** transmises par l'encadrant,
tout ce qui était auparavant réparti entre plusieurs prototypes : le suivi des arrêts de
ligne (2024-2025, présenté en soutenance PFA), le rendement de production réel
(2012-2024), le catalogue produits, le suivi commercial (commandes clients et
prospection 2025-2026) et le stock/planification Gobeleterie 2026 — avec une connexion
par rôle (Opérateur, Chef de service, Chef de département, Direction Générale) qui donne
accès aux modules pertinents. C'est un outil polyvalent (« ERP junior ») pensé pour être
directement utile dans la vie professionnelle de SEVAM, pas seulement une démonstration.

**Aucune donnée n'est inventée.** Quand une information n'existe dans aucun des fichiers
sources (coût de revient, organigramme nominatif...), elle est laissée absente plutôt que
remplacée par une valeur plausible — voir la page **Qualité des données**, qui documente
en toute transparence la provenance et les limites de chaque source.

## 1. Modules disponibles

13 pages, accessibles depuis le menu de gauche (visibilité selon le rôle connecté) :

| Page | Contenu | Rôles |
|---|---|---|
| **Accueil** | Tableau de bord multi-modules : arrêts, rendement, commercial, stock. | Tous |
| **Connexion** | Choix du nom/rôle, indicateur des utilisateurs connectés en temps réel. | Tous |
| **Nouvelle déclaration** | Déclarer un arrêt (ligne, équipement, durée). Enregistrement permanent. | Tous |
| **Historique** | Recherche/filtrage de tous les événements d'arrêt, export CSV. | Tous |
| **Suivi quotidien 2025** | Suivi journalier réel (Jan-Sept 2025) vs seuil de référence SEVAM. | Tous |
| **Analyse Pareto** | Causes qui concentrent le plus de temps d'arrêt (règle des 80/20). | Chef de service +|
| **Fiabilité** | MTBF, MTTR, disponibilité — méthode validée en soutenance. | Chef de service +|
| **AMDEC** | Grille de criticité (Fréquence x Gravité) + simulateur d'incident. | Chef de service +|
| **Rendement & écarts** | Écarts RDT vs PTM réels, 2 308 ordres de fabrication (2012-2024). | Chef de service +|
| **Catalogue produits** | Référentiel articles réel (poids, usine, ligne), 340 articles. | Chef de service +|
| **Suivi commercial** | Commandes clients 2026, prospection — noms réels des commerciaux. | Chef de département +|
| **Stock & planification** | Stock Gobeleterie, budget commercial 2026, ventes mensuelles. | Chef de département +|
| **Impact économique** | Estimation du coût des arrêts (coût/minute réglable). | Chef de département +|
| **Qualité des données** | Transparence totale : provenance, corrections, limites de chaque source. | Chef de service +|

"Chef de service +" signifie : Chef de service, Chef de département ou Direction
Générale. "Chef de département +" signifie : Chef de département ou Direction Générale.

## 2. Connexion par rôle — ce que c'est et ce que ce n'est pas

SEVAM n'a fourni aucun annuaire d'utilisateurs (pas de LDAP/Active Directory, pas
d'organigramme nominatif). Les 4 rôles sont donc des **libellés génériques de fonction**,
choisis librement à la connexion — **ce n'est pas une authentification sécurisée** (aucun
mot de passe n'est vérifié côté serveur). Deux choses sont en revanche bien réelles :

- le **contrôle d'accès par page selon le rôle** (`src/config.PAGE_ROLES`) ;
- l'**indicateur de présence** ("connectés actuellement"), qui lit une vraie table de
  sessions dans `data/sevam.db`, partagée par tous les postes connectés au même
  déploiement — ce n'est pas un chiffre simulé.

Si SEVAM industrialise l'outil, la suite logique est de brancher cette page sur un vrai
système d'authentification d'entreprise (voir page Qualité des données, section 5).

## 3. Installation et lancement

Prérequis : Python 3.10 ou plus récent.

```bash
# 1) installer les dépendances (une seule fois)
pip install -r requirements.txt

# 2) (re)générer les données nettoyées à partir des fichiers Excel bruts (une seule fois,
#    ou après avoir remplacé un fichier dans data/raw/ par une version plus récente)
python3 src/etl.py       # arrêts de ligne (2024-2025)
python3 src/etl_erp.py   # rendement, catalogue, commercial, stock (2012-2026)

# 3) lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement dans le navigateur (par défaut sur
`http://localhost:8501`). Elle fonctionne aussi bien sur le poste de l'encadrant que sur
un serveur interne SEVAM.

### Mettre à jour les données sources

1. Remplacer le(s) fichier(s) dans `data/raw/` (mêmes noms, mêmes structures de feuilles).
2. Relancer le script ETL correspondant :
   - `Arret_2024.xlsx` ou `Suivi_arrets_2025.xlsx` → `python3 src/etl.py`
   - `FPAS_POT_DELICIA_37_corrige.xlsm`, `Suivi_BC.xlsx` ou `Planner_Gobeleterie_2026.xlsm`
     → `python3 src/etl_erp.py`
3. Redémarrer l'application (ou rafraîchir la page si elle tourne déjà).

**Attention** : relancer un ETL ne touche jamais aux déclarations saisies manuellement
dans l'application (`data/sevam.db`) — seuls les imports depuis les fichiers Excel sont
reconstruits.

### Déploiement

Deux options simples, sans changement de code :

- **Streamlit Community Cloud** (gratuit, rapide à mettre en place) : pousser ce dossier
  sur un dépôt Git (privé de préférence, les données étant internes à SEVAM) et connecter
  le dépôt sur [streamlit.io/cloud](https://streamlit.io/cloud). Le fichier `data/sevam.db`
  étant sur disque local au service, prévoir une sauvegarde régulière (voir section 5).
- **Serveur interne SEVAM** : installer Python + les dépendances sur un poste ou serveur
  accessible sur le réseau interne, puis lancer `streamlit run app.py --server.port 8501
  --server.address 0.0.0.0` pour le rendre accessible aux autres postes du réseau.

## 4. Structure du projet

```
real_app/
├── app.py                        # tableau de bord d'accueil (tous modules)
├── common.py                     # bootstrap partagé (config page, cache, connexion, style)
├── requirements.txt
├── data/
│   ├── raw/                      # fichiers Excel originaux fournis par l'encadrant
│   ├── evenements_2024.csv       # journal détaillé des arrêts, nettoyé (src/etl.py)
│   ├── suivi_quotidien_2025.csv  # suivi quotidien des arrêts, nettoyé (src/etl.py)
│   ├── rapport_qualite_donnees.csv     # corrections appliquées (src/etl.py)
│   ├── comparaison_sources_2024.csv    # écart entre les 2 sources arrêts (src/etl.py)
│   ├── rendement_of.csv          # 2 308 ordres de fabrication réels (src/etl_erp.py)
│   ├── catalogue_articles.csv    # catalogue produits réel, fusion 3 sources (src/etl_erp.py)
│   ├── commandes_clients_2026.csv, suivi_commandes_clients_2026.csv,
│   │   prospection_commerciale.csv     # suivi commercial réel (src/etl_erp.py)
│   ├── stock_gobeleterie.csv, budget_commercial_2026.csv,
│   │   ventes_mensuelles_2026.csv      # stock/planification réel (src/etl_erp.py)
│   └── sevam.db                  # base SQLite : imports + déclarations manuelles + sessions
├── src/
│   ├── etl.py                    # nettoyage/unification des arrêts de ligne
│   ├── etl_erp.py                # nettoyage/unification des modules ERP supplémentaires
│   ├── db.py                     # accès SQLite (arrêts, déclarations, sessions connectées)
│   ├── auth.py                   # connexion par rôle, contrôle d'accès par page
│   ├── kpi.py                    # calculs purs : MTBF/MTTR/dispo, Pareto, AMDEC, coûts
│   └── config.py                 # constantes partagées (lignes, fours, rôles, couleurs)
├── pages/                        # les 13 pages de l'application (voir tableau ci-dessus)
└── tests/
    ├── test_kpi.py               # tests unitaires du moteur de calcul (5 tests)
    └── smoke_app.py              # charge les 13 pages + vérifie le contrôle d'accès
```

## 5. Fiabilité et vérifications effectuées

- **`python3 tests/test_kpi.py`** : 5 tests unitaires sur le moteur de calcul, dont un
  test de non-régression qui rejoue l'exemple du Four U2 déjà validé en soutenance PFA.
- **`python3 tests/smoke_app.py`** : charge automatiquement les 13 pages de l'application
  (framework `streamlit.testing`) en tant que Direction Générale, vérifie qu'aucune ne
  lève d'exception, **et vérifie que le contrôle d'accès par rôle bloque bien** un rôle
  non autorisé sur une page réservée.
- Toute correction apportée aux données sources est journalisée et consultable dans la
  page **Qualité des données** — aucune valeur n'est modifiée sans laisser de trace.

**Sauvegarde recommandée** : `data/sevam.db` est le seul fichier qui grandit avec l'usage
(déclarations manuelles + sessions connectées). Prévoir une copie régulière de ce fichier
selon la politique de sauvegarde de SEVAM.

## 6. Points importants à partager avec l'encadrant

- **Écart entre les deux fichiers sources d'arrêts (2024)** : voir la page **Qualité des
  données**, section 2 — hypothèse la plus probable : deux pratiques de suivi
  indépendantes (maintenance vs production), à confirmer auprès des équipes concernées.
- **Le module Rendement & écarts a une granularité différente** du module Arrêts de
  ligne (1 ligne = 1 ordre de fabrication, pas 1 jour) : les heures d'arrêt des deux
  modules ne doivent pas être additionnées — voir Qualité des données, section 4.
- **La connexion par rôle n'est pas une authentification sécurisée** (voir section 2
  ci-dessus et Qualité des données, section 5) — à faire évoluer si l'outil est
  industrialisé.
- L'application est prête à recevoir de nouvelles déclarations et de nouveaux fichiers
  sources dès maintenant : aucune configuration supplémentaire n'est nécessaire.
