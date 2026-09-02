PROTOTYPE — Fiche de déclaration d'écart numérique (SEVAM) — v4
=================================================================

Ce dossier contient un prototype Python (Streamlit) qui démontre une version
numérique de la fiche de déclaration d'écart proposée au chapitre 5 du
rapport PFA, avec pilotage Pareto des causes en temps réel, catalogue produit
réel et accès différencié par rôle.

Contenu :
- app.py                                  -> l'application
- catalogue_sevam.py                      -> fours/lignes/départements/rôles + catalogue produit (246 réf.)
- build_dataset_v3.py                     -> script qui régénère le CSV de démonstration à partir du catalogue
- Dataset_Ecarts_Production_SEVAM.csv     -> données de démonstration (218 OF, catalogue réel)
- logo_sevam.png                          -> logo officiel SEVAM
- requirements.txt                        -> dépendances Python

NOUVEAUTÉS v4 — données réelles de l'entreprise
------------------------------------------------
Le catalogue produit et la codification four/ligne ont été reconstruits à
partir de 3 fichiers réels transmis par SEVAM (F.P.A.S POT DELICIA 37 + sa
version corrigée, Planner Gobeleterie 2026) :
- 246 références produit, dont 207 réelles (bouteilles, pots, bocaux, verres
  à thé/café, articles décorés/personnalisés pour des marques identifiées
  dans les fichiers : Shell, TotalEnergies, Carte Noire, Nescafé, Butagaz...).
  39 références ont été ajoutées pour élargir le choix (identifiées
  source="genere" dans catalogue_sevam.py).
- Codification des lignes corrigée grâce au vrai journal de production ERP
  (2308 lignes réelles, 2013-2024) : U2 -> L11/L12/L13, U3 -> L21/L22/L23.
  U1 et U4 (absents de ce fichier) prolongent la même logique, à vérifier
  auprès de SEVAM.
- L'atelier Décor est modélisé comme un atelier transverse (pas de four
  dédié), conformément à la confirmation de l'entreprise.
- Départements : Gobeleterie (four U1), Verre creux (fours U2/U3/U4), Décor.

NOUVEAUTÉS v4 — accès différencié par rôle (backend)
------------------------------------------------------
Un sélecteur de rôle en haut de la barre latérale simule 4 niveaux d'accès :
- Opérateur           -> saisie restreinte à sa ligne + résumé personnel simplifié
- Chef de service      -> pilotage de son four (toutes les lignes du four)
- Chef de département  -> pilotage de son département, y compris impact économique
- Directeur Général    -> accès complet à tous les départements + vue comparative
Il s'agit d'une démonstration de principe (pas d'authentification réelle) —
voir l'onglet Méthodologie de l'application pour le détail et les limites.

INSTALLATION ET LANCEMENT (sur ton ordinateur)
-----------------------------------------------
1. Installer Python 3.9 ou plus récent (python.org).
2. Ouvrir un terminal dans ce dossier et exécuter :

   pip install -r requirements.txt
   streamlit run app.py

3. Une page va s'ouvrir automatiquement dans le navigateur
   (sinon, ouvrir l'adresse indiquée dans le terminal, en général
   http://localhost:8501).

POUR RE-DÉPLOYER SUR STREAMLIT CLOUD (sevam-pfa.streamlit.app)
-----------------------------------------------------------------
Remplace TOUS les fichiers de ce dossier (y compris le nouveau
catalogue_sevam.py et build_dataset_v3.py) dans ton dépôt GitHub
"sevam-fiche-ecart" en utilisant "Add file -> Upload files", comme la
dernière fois. Le redéploiement est automatique après le remplacement.

UTILISATION EN SOUTENANCE
--------------------------
- Choisir un rôle dans la barre latérale pour montrer au jury la vue
  Opérateur (simple) puis la vue DG (complète) : cela illustre concrètement
  la maîtrise du besoin métier (qui doit voir quoi).
- Onglet "Saisie d'une déclaration" : le champ Référence article est un vrai
  catalogue SEVAM (article + décor + marque si personnalisé).
- Onglet "Pilotage QCD & Pareto" : Pareto des causes, répartition par ligne,
  top articles en écart, part des OF passés par l'atelier Décor.
- Onglet "Impact économique" : traduction financière + simulation de gain
  (+ vue comparative inter-départements pour la DG uniquement).
- Onglet "Méthodologie & note technique" : explique au jury la provenance
  des données réelles, les limites assumées et les points à vérifier avec
  SEVAM (codification U1/U4).

Argument pour le jury : ce prototype ne se contente pas d'illustrer un
concept — son catalogue produit et sa structure four/ligne s'appuient sur
de vrais extraits ERP fournis par l'entreprise, et son architecture d'accès
par rôle répond directement à un besoin d'organisation exprimé par SEVAM.
