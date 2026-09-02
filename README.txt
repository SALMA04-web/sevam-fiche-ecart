PROTOTYPE — Fiche de déclaration d'écart numérique (SEVAM)
=============================================================

Ce dossier contient un prototype Python (Streamlit) qui démontre une version
numérique de la fiche de déclaration d'écart proposée au chapitre 5 du
rapport PFA, avec pilotage Pareto des causes en temps réel.

Contenu :
- app.py                                  → l'application
- Dataset_Ecarts_Production_SEVAM.csv     → données de démonstration (163 OF)
- requirements.txt                        → dépendances Python

INSTALLATION ET LANCEMENT (sur ton ordinateur)
-----------------------------------------------
1. Installer Python 3.9 ou plus récent (python.org).
2. Ouvrir un terminal dans ce dossier et exécuter :

   pip install -r requirements.txt
   streamlit run app.py

3. Une page va s'ouvrir automatiquement dans le navigateur
   (sinon, ouvrir l'adresse indiquée dans le terminal, en général
   http://localhost:8501).

UTILISATION EN SOUTENANCE
--------------------------
- Panneau de gauche : seuil d'alerte (%) et coût unitaire (MAD) sont
  paramétrables et recalculent tout en direct.
- Onglet "Saisie d'une déclaration" : remplir une fiche comme le ferait
  un opérateur/planificateur, l'écart et son statut se calculent
  automatiquement à l'enregistrement.
- Onglet "Pilotage QCD & Pareto" : indicateurs structurés selon les
  3 critères Qualité / Coût / Délai, Pareto des causes avec repère
  des 80%, répartition par ligne/four. Tout se met à jour instantanément,
  y compris avec les nouvelles déclarations saisies pendant la démo.
- Onglet "Impact économique" : traduction financière des écarts et
  simulation de gain interactive (curseur d'objectif de réduction).
- Onglet "Méthodologie & note technique" : explique à un lecteur qui
  découvre l'application (le jury) le contexte, l'architecture
  technique, la cohérence avec le rapport, les limites assumées et
  les pistes d'évolution — à lire ou montrer directement en soutenance.
- Chaque écran comporte des petits blocs "ℹ️" dépliables qui expliquent
  comment lire les graphiques et les indicateurs.

Ce prototype a été testé et s'exécute sans erreur (démarrage serveur,
soumission du formulaire, calcul et affichage des graphiques et des
4 onglets vérifiés par capture d'écran).

Argument pour le jury : ce prototype démontre concrètement la faisabilité
technique de la piste d'amélioration proposée au chapitre 5 — remplacer
la fiche papier par une saisie numérique alimentant automatiquement un
pilotage par cause, en cohérence avec l'ERP JD Edwards et Qlik Sense déjà
utilisés par SEVAM.
