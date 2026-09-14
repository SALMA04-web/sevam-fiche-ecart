PLATEFORME NUMÉRIQUE SEVAM — Suivi des écarts & Maintenance — v13
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

NOUVEAUTÉS v13 — correctif d'un plantage au déploiement (AttributeError)
------------------------------------------------------------------------------
En déployant la v12 sur Streamlit Cloud, l'onglet "Pilotage QCD & Pareto"
plantait avec une erreur "AttributeError: declarations_len_initial". Cause :
sur Streamlit Cloud, un redéploiement peut réutiliser une session déjà
ouverte AVANT la mise à jour du code — dans ce cas, "declarations" existait
déjà dans la session, donc le bloc qui initialisait "declarations_len_initial"
(utilisé par le bouton "Annuler ma dernière déclaration") ne s'exécutait
jamais pour cette session. Corrigé en donnant à "declarations_len_initial" sa
propre initialisation indépendante, plutôt que de la faire dépendre de
l'initialisation de "declarations". Vérifié en reproduisant exactement ce
scénario (session avec des déclarations déjà présentes mais sans cette clé)
avant et après le correctif.
Conseil pratique pour la suite : en cas d'erreur similaire après un futur
déploiement sur Streamlit Cloud, un simple redémarrage de l'application
("Reboot app" dans le menu de gestion) réinitialise toutes les sessions et
suffit en général à repartir sur une base saine.

NOUVEAUTÉS v12 — suite à une analyse complète de l'application (retours "jury")
------------------------------------------------------------------------------
Trois ajouts issus d'une relecture complète de la plateforme dans l'optique de
la soutenance :
1. Un panneau « 🎬 Scénario de démonstration suggéré (environ 5 minutes) » en
   haut de l'onglet Accueil (replié par défaut) : un enchaînement rédigé en
   phrases complètes, étape par étape (connexion, déclaration d'un OF, second
   onglet pour montrer le temps réel, Pareto, impact économique, Maintenance
   Four U2), pour dérouler la démonstration sans avoir à improviser l'ordre
   devant le jury.
2. Un champ de recherche « 🔍 Rechercher un N° OF » au-dessus du tableau des
   dernières déclarations (onglet Saisie) : permet de retrouver instantanément
   une déclaration précise plutôt que de parcourir la liste à l'œil.
3. Un bouton « ↩️ Annuler ma dernière déclaration » : permet de corriger en un
   clic une saisie faite par erreur pendant une démonstration. Il ne retire
   jamais les données de démonstration de départ — uniquement la dernière
   déclaration ajoutée par l'utilisateur pendant la session en cours — et reste
   grisé tant qu'aucune déclaration n'a encore été ajoutée.

NOUVEAUTÉS v11 — détail du calcul de besoin, chiffre par chiffre
------------------------------------------------------------------------------
En re-testant le calculateur avec un second cas réel (article différent de
Steine 100 VA), un écart est apparu entre le résultat de l'application et le
calcul fait à la main sur papier (4 palettes attendues, contre 0 affiché).
Vérification faite : la formule de l'application est la bonne — elle
reproduit exactement, avec les chiffres réels de la fiche Steine 100 VA
(chapitre 6.2.4), le résultat obtenu manuellement (26 palettes). L'écart sur
le second cas venait du champ « Ventes réalisées » : le résultat intermédiaire
« Besoin client − Stock actuel − Stock R+Z », déjà noté à la main sur le
papier, avait été ressaisi une seconde fois dans ce champ — ce qui revenait
à le soustraire deux fois (d'où 0 au lieu de 4 palettes). En remettant
« Ventes réalisées » à 0 (puisque, pour ce cas, les ventes déjà réalisées
étaient déjà comprises dans les autres champs et n'avaient pas à être
déduites une seconde fois), l'application retrouve exactement les 4 palettes
du calcul papier.
Pour que ce genre de confusion ne se reproduise plus et pour que le calcul
reste totalement transparent (utile aussi en soutenance), un nouveau bloc
dépliable « 🔍 Détail du calcul, chiffre par chiffre » a été ajouté juste
sous les champs de saisie : il affiche, avec les valeurs réellement saisies,
chacune des trois étapes du calcul (besoin net, équivalent des palettes déjà
disponibles, reste à produire, puis palettes à produire), accompagné d'un
rappel : ne pas ressaisir dans « Ventes réalisées » un montant déjà pris en
compte ailleurs, sous peine de le déduire deux fois.

NOUVEAUTÉS v10 — clarification du calculateur de besoin (onglet Maintenance)
------------------------------------------------------------------------------
Le calculateur "🧮 Calcul de besoin" recalculait déjà instantanément à chaque
changement de champ (aucun bouton "valider" n'est nécessaire) — mais avec
certaines combinaisons de chiffres de test, "Besoin net à couvrir" et "Reste
à produire" tombent exactement à 0, ce qui pouvait donner l'impression, à
tort, que l'outil était resté bloqué sur l'exemple Steine 100 VA de départ.
En réalité, un résultat à 0 est un cas normal de la formule : cela veut dire
que le stock actuel + le stock R+Z + les ventes déjà réalisées couvrent, à
eux seuls, le besoin client saisi — donc, logiquement, aucune palette
supplémentaire à produire. Un message explicatif "✅ Stock déjà suffisant"
apparaît désormais automatiquement dans ce cas précis, pour que ce résultat
se lise comme une conclusion du calcul et non comme un blocage de l'outil.

NOUVEAUTÉS v9 — passage en temps réel PARTAGÉ entre tous les postes connectés
------------------------------------------------------------------------------
Constat corrigé : jusqu'à la v8, le "Centre d'alertes" et le journal
d'activité étaient recalculés en temps réel, mais uniquement pour la
session/l'onglet de navigateur en cours — si un autre poste déclarait un OF
au même moment, rien ne le signalait ailleurs tant que cette personne n'avait
pas rouvert elle-même l'onglet Accueil. Ce n'était donc pas encore un vrai
temps réel PARTAGÉ entre utilisateurs.
Trois changements y répondent, sans base de données externe ni serveur
supplémentaire :
1. La page se rafraîchit désormais automatiquement TOUTE SEULE toutes les
   5 secondes (paquet "streamlit-autorefresh", ajouté à requirements.txt) :
   un poste resté ouvert, sans qu'on touche à rien, voit apparaître ce que
   les autres postes viennent de faire.
2. Le flux d'activité (déclarations d'OF, incidents simulés) n'est plus
   propre à chaque session : il est désormais PARTAGÉ entre tous les postes
   connectés au même moment à l'application. Concrètement, dès qu'une
   personne déclare un OF ou enregistre un incident simulé, TOUT LE MONDE de
   connecté voit apparaître, dans les secondes qui suivent :
     - une notification "toast" (petite bulle en bas de l'écran, qui se
       ferme toute seule) précisant qui a fait l'action et quel est
       l'écart/le problème — par exemple : "Youssef HAFFOU a déclaré l'OF
       OF-2026-1001 sur L23 — Four U3 — écart de -8.0% (A traiter)...". Une
       personne n'est jamais notifiée de ses propres actions.
     - la mise à jour du flux d'activité affiché dans l'onglet Accueil, avec
       la mention "(vous)" sur les événements que l'utilisateur connecté a
       lui-même déclenchés.
3. (Bonus) Un bandeau "🟢 X personne(s) connectée(s) en ce moment" affiche, en
   direct, qui d'autre utilise la plateforme au même moment (nom + poste),
   avec "— vous" sur sa propre ligne — utile en soutenance pour montrer que
   plusieurs postes peuvent travailler simultanément sur le même outil,
   exactement comme le ferait un vrai système de production partagé.
Remarque technique : ce partage utilise le mécanisme officiel de Streamlit
pour l'état partagé entre sessions (`st.cache_resource`, protégé par un
verrou pour rester sûr même si plusieurs personnes agissent au même moment).
L'information est donc bien partagée entre tous les navigateurs connectés
tant que le serveur applicatif tourne — c'est un vrai progrès par rapport à
la v8, purement locale à chaque session. Cela reste néanmoins un état gardé
en mémoire du processus (pas une base de données) : il est partagé "en
direct" pendant toute la durée où l'application tourne, mais repart à zéro
si le serveur est redémarré/redéployé — cohérent avec le positionnement d'un
prototype de démonstration légère annoncé dans le rapport, à mentionner si le
jury pose une question sur les limites assumées de l'outil.

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

NOUVEAUTÉS v8 — Centre d'alertes et journal d'activité (page d'accueil)
------------------------------------------------------------------------
Demande : que la plateforme "prévienne" d'elle-même l'utilisateur — dès qu'un
OF est déclaré, qu'un écart significatif apparaît ou qu'une quantité perdue
est calculée — plutôt que de le laisser découvrir l'information en rouvrant
chaque onglet un par un.
Un bandeau "🔔 Centre d'alertes" a été ajouté tout en haut de l'onglet
Accueil, donc visible immédiatement à la connexion et à chaque retour sur cet
onglet :
1. Des alertes calculées EN DIRECT à partir du périmètre de l'utilisateur
   connecté : nombre d'OF au-delà du seuil de vigilance (avec le cas le plus
   marqué et l'impact économique cumulé en MAD), disponibilité du Four U2 si
   elle descend sous le seuil de vigilance (97%), nombre d'organes classés
   "Critique" dans la grille AMDEC, et nombre d'incidents simulés enregistrés
   dans la session — chacune avec une explication en une phrase de ce qui se
   passe et, si besoin, de l'onglet où creuser le sujet.
2. Un "Journal d'activité récente" (dépliable) qui historise, dans l'ordre
   chronologique inverse et avec un horodatage relatif ("à l'instant", "il y
   a 12 min"...), chaque déclaration d'OF traitée et chaque incident simulé
   enregistré au cours de la session — jusqu'à 20 événements conservés.
Par ailleurs, le message de confirmation affiché juste après l'enregistrement
d'une déclaration explique désormais clairement pourquoi le dossier est classé
"À traiter" (écart au-delà du seuil affiché dans le panneau de gauche) ou au
contraire pourquoi il ne nécessite aucune action (écart dans la tolérance).
Remarque technique pour la suite du développement : comme l'onglet Accueil est
codé avant les autres et s'exécute donc en premier à chaque rafraîchissement
Streamlit, toute action qui doit se refléter immédiatement dans le Centre
d'alertes (déclaration, incident simulé) déclenche un rerun explicite juste
après avoir mis à jour les données de session — sans quoi l'alerte resterait
affichée avec l'état précédent jusqu'à la prochaine interaction.

Enfin, un bouton "📥 Exporter la synthèse (Excel)" a été ajouté en bas de
l'onglet Impact économique : il génère, à la demande et sans rien écrire sur
le serveur (fichier construit en mémoire), un classeur Excel à trois onglets
(Synthèse des indicateurs clés, Coût estimé par cause, Détail des OF) sur le
périmètre de l'utilisateur connecté — un support prêt à distribuer au jury ou
au contrôle de gestion. Nécessite le paquet "openpyxl" (ajouté à
requirements.txt).

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
