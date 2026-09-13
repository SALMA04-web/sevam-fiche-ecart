PLATEFORME NUMÉRIQUE SEVAM — Suivi des écarts & Maintenance — v7
===================================================================

Ce dossier contient un prototype Python (Streamlit) qui démontre une version
numérique de la fiche de déclaration d'écart proposée au chapitre 5 du
rapport PFA (pilotage Pareto des causes en temps réel, catalogue produit
réel, connexion nom + poste adossée à un vrai annuaire SEVAM, base d'OF
confirmés à sélectionner), ENRICHIE d'un module complet de suivi de la
fiabilité et de la maintenance du Four U2 (chapitre 6.2.4/6.2.5).

Contenu :
- app.py                                  -> l'application
- catalogue_sevam.py                      -> fours/lignes/départements/rôles + catalogue produit (246 réf.)
- maintenance_sevam.py                    -> historique des pannes, MTBF/MTTR/AMDEC, calcul de besoin (Four U2)
- build_dataset_v3.py                     -> script qui régénère le CSV de démonstration à partir du catalogue
- Dataset_Ecarts_Production_SEVAM.csv     -> données de démonstration (218 OF, catalogue réel)
- logo_sevam.png                          -> logo officiel SEVAM
- requirements.txt                        -> dépendances Python

NOUVEAUTÉS v6 — suite au retour du professeur encadrant
----------------------------------------------------------
Le professeur a indiqué qu'en ouvrant la plateforme, on ne comprenait pas
immédiatement de quoi il s'agissait, et a demandé une interface plus claire,
plus détaillée, et un fonctionnement plus réaliste ("temps réel") — par
exemple : un problème survient sur un four, comment procède-t-on ?
Trois changements y répondent :
1. Écran d'accueil (avant ET après connexion) qui explique en clair le
   périmètre de la plateforme (les deux livrables numérisés, comment s'en
   servir), plutôt qu'un simple formulaire de connexion sans contexte.
2. Un nouvel onglet "Maintenance Four U2", proposé aux postes dont le
   périmètre couvre ce four (chefs de service/département concernés,
   Direction), qui déploie tout ce qui a été construit pour le rapport :
   historique des 14 pannes réelles, fiabilité (MTBF/MTTR/disponibilité)
   RECALCULÉE EN DIRECT, analyse des causes (5M/5S/5 Pourquoi), grille de
   criticité AMDEC des 9 organes du four, et un calculateur de besoin de
   production (article Steine 100 VA).
3. Un SIMULATEUR D'INCIDENT temps réel : on choisit un organe du four et une
   ligne, puis on rejoue, étape par étape (bouton "Étape suivante"), la
   procédure de traitement de l'incident — de la détection à la clôture —
   avec un chronomètre et une barre de progression. Une fois le scénario
   terminé, on peut enregistrer l'incident dans l'historique : le MTBF, le
   MTTR et la disponibilité affichés dans l'onglet Fiabilité se recalculent
   alors instantanément pour en tenir compte — ce qui rend concrètement
   visible, en soutenance, l'intérêt d'un outil qui "travaille en temps réel"
   plutôt qu'un historique reconstitué a posteriori.

NOUVEAUTÉS v7 — compte d'accès pour l'encadrant pédagogique (école)
------------------------------------------------------------------
Un 11e compte a été ajouté dans l'annuaire de connexion : "Pr. Bellahkim —
Encadrant pédagogique — École", avec un accès complet (tous sites, tous
départements, comme la Direction Générale) pour qu'il puisse se connecter et
explorer librement toute la plateforme de son côté. Ce compte est clairement
identifié dans l'onglet Méthodologie comme ajouté pour la soutenance et ne
faisant pas partie de l'annuaire réel SEVAM (contrairement aux 10 autres
postes, qui restent tous issus de la fiche de validation avant lancement
transmise par l'entreprise) — la transparence sur l'origine des données reste
intacte.

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

NOUVEAUTÉS v5 — connexion nom + poste, vrai annuaire Tit Mellil
------------------------------------------------------------------
L'écran d'accueil demande maintenant un NOM et affiche automatiquement le
POSTE associé (au lieu d'un simple sélecteur de rôle) : le périmètre de
données est déduit du poste, comme le ferait un annuaire d'entreprise réel.
Les 10 postes proposés sont réels, identifiés sur la fiche de validation
avant lancement transmise par SEVAM (réf. FN-PR-121-05-V.00, client
SACOFRINA SA, site de Tit Mellil) : Adnane RAFIK (Chef Service Supply
Chain), Youssef HAFFOU (Chef Département Supply Chain), Fatima Zahra AOUAB
(Chef Département SMI), Abderrahim BELKHDIM (Chef Département Production —
Four 2), Abderrahim ZNIDI (Chef Département Qualité Process), Asmaa KDAH
(Chef Département Contrôle de Gestion), Abderrahim EL ABBADI (Directeur
Exploitation), Hassan TAHRI (Directeur Commercial & Marketing), Bouchra
SNAIBI (Directeur Administratif et Financier), Karim AMMAR (Directeur
Général Délégué). Un compte "Autre" reste disponible pour les opérateurs de
ligne et les postes de chef de service Four 1/3/4 (aucun nom réel confirmé
pour ces deux derniers dans les documents transmis — affiché tel quel, sans
nom inventé). Le périmètre visible gère aussi un niveau "site" (ex. tout Tit
Mellil = U2+U3+U4) pour les postes qui supervisent un site entier.

NOUVEAUTÉS v5 — Tit Mellil mis en avant
-------------------------------------------
La stagiaire étant affectée au site de Tit Mellil (fours U2/U3/U4,
département Verre creux), les listes de lignes/fours de l'application sont
triées avec Tit Mellil en premier (Roches Noires reste visible, jamais
masqué), et la base d'OF confirmés (ci-dessous) est majoritairement
construite sur Tit Mellil.

NOUVEAUTÉS v5 — base d'OF confirmés (fin de la ressaisie manuelle)
------------------------------------------------------------------
L'onglet Saisie propose désormais deux modes : "OF confirmé" (par défaut),
qui permet de choisir un OF déjà planifié dans une base existante — article,
ligne/four et quantité planifiée se remplissent automatiquement, il ne reste
qu'à saisir la quantité réalisée et la cause d'écart — et "Saisie manuelle"
pour les OF hors liste (formulaire d'origine, conservé tel quel). La base
contient 54 OF, dont 9 construits à partir de correspondances réelles
vérifiables entre la fiche de validation avant lancement et le fichier réel
"Copie de Suivi BC.xlsx" (suivi des commandes clients 2026) transmis par
SEVAM, recoupé avec les libellés exacts du catalogue produit (clients réels
SOTHERMA, JAD DISTRIBUTION, FLEUR ATLAS BELAAMRI, LES EAUX MINERALES
D'OULMES, ROSLANE WINE & SPIRITS, SACOFRINA SA...). Chaque OF affiche sa
provenance (donnée réelle / démonstration) directement dans le formulaire.

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
Remplace TOUS les fichiers de ce dossier (y compris les nouveaux
maintenance_sevam.py et catalogue_sevam.py) dans ton dépôt GitHub
"sevam-fiche-ecart" en utilisant "Add file -> Upload files", comme la
dernière fois. Le redéploiement est automatique après le remplacement.

UTILISATION EN SOUTENANCE
--------------------------
- Se connecter avec un nom réel de l'annuaire (ex. Abderrahim BELKHDIM, Chef
  Département Production Four 2) pour montrer au jury que le poste — donc le
  périmètre visible — se déduit automatiquement du nom, puis se déconnecter
  et se reconnecter en Karim AMMAR (Directeur Général Délégué) pour montrer
  la vue complète : cela illustre concrètement la maîtrise du besoin métier
  (qui doit voir quoi) ET l'ancrage dans l'organisation réelle de SEVAM.
- Onglet "Saisie d'une déclaration" : mode "OF confirmé" par défaut — choisir
  un OF dans la liste et montrer que l'article/ligne/quantité planifiée se
  remplissent seuls (plus de ressaisie manuelle) ; basculer sur "Saisie
  manuelle" pour montrer que l'ancien formulaire reste disponible.
- Onglet "Pilotage QCD & Pareto" : Pareto des causes, répartition par ligne,
  top articles en écart, part des OF passés par l'atelier Décor.
- Onglet "Impact économique" : traduction financière + simulation de gain
  (+ vue comparative inter-départements pour la Direction uniquement).
- Onglet "Méthodologie & note technique" : explique au jury la provenance
  des données réelles (catalogue, annuaire, base d'OF confirmés), les
  limites assumées et les points à vérifier avec SEVAM (codification U1/U4,
  noms des chefs Four 1/3/4).
- Onglet "Maintenance Four U2" (connecté en Karim AMMAR, ou Abderrahim
  BELKHDIM pour rester dans le rôle du Four 2) : montrer l'historique des 14
  pannes et le Pareto, puis la fiabilité (MTBF/MTTR/disponibilité), puis
  enchaîner directement sur le sous-onglet "Simulateur d'incident" — choisir
  "Brûleurs" (scénario réel du 29/07/2026) et cliquer "Étape suivante"
  plusieurs fois pour montrer la procédure de A à Z ; une fois le scénario
  terminé, cliquer "Enregistrer cet incident" puis revenir sur l'onglet
  Fiabilité pour montrer que le MTBF/MTTR/disponibilité se sont recalculés
  instantanément. C'est le moment le plus fort pour répondre à la demande du
  professeur d'un outil "qui travaille en temps réel".
- Pour ton encadrant pédagogique (école) : il peut se connecter directement
  avec le nom "Pr. Bellahkim" dans la liste — il a un accès complet comme la
  Direction Générale et peut naviguer seul dans tous les onglets, y compris
  le simulateur d'incident.

Argument pour le jury : ce prototype ne se contente pas d'illustrer un
concept — son catalogue produit, sa structure four/ligne, son annuaire des
accès et sa base d'OF confirmés s'appuient sur de vrais documents fournis
par l'entreprise (extraits ERP, fiche de validation avant lancement, suivi
des commandes clients), et son architecture d'accès par nom + poste répond
directement à un besoin d'organisation exprimé par SEVAM.
