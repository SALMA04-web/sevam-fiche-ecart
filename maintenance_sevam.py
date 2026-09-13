# -*- coding: utf-8 -*-
"""
Maintenance et fiabilité — Four U2 (Tit Mellil), SEVAM.

Données et calculs pour le module "Maintenance Four U2" du prototype applicatif :
historique des pannes, MTBF/MTTR/Disponibilité, analyse des causes (5M / 5S /
5 Pourquoi), criticité AMDEC des organes, fiche de calcul de besoin de production
et simulateur d'incident temps réel.

Reprend exactement les chiffres du classeur "Historique_Pannes_Four2_U2.xlsx" et
de "Fiche_Calcul_Besoin_Production_Steine100VA.xlsx" (chapitre 6.2.4 et 6.2.5 du
rapport PFA), afin que le rapport et le prototype présentent les mêmes chiffres.
"""
from datetime import date

# =========================================================
# HISTORIQUE DES PANNES — FOUR U2 (14 pannes, juin-août 2026)
# =========================================================
CAUSE_PANNE_LABELS = {
    "FOUR": "Panne four / thermique",
    "MECANIQUE": "Panne mécanique",
    "ELECTRIQUE": "Panne électrique",
    "APPRO": "Rupture / retard matière première",
    "SERIE": "Changement de série non anticipé",
    "QUALITE": "Rebuts / non-conformité qualité",
}
CAUSE_PANNE_COLOR = {
    "FOUR": "#8C2222", "MECANIQUE": "#2E75B6", "ELECTRIQUE": "#BF8F00",
    "APPRO": "#385723", "SERIE": "#5B2C6F", "QUALITE": "#C55A11",
}

PERIOD_START = date(2026, 6, 1)
PERIOD_END = date(2026, 8, 31)
PERIODE_JOURS = 92
NB_LIGNES_U2 = 3
LIGNES_U2 = ["L11", "L12", "L13"]

PANNES = [
    {"date": date(2026, 6, 3), "ligne": "L11", "article": "AIN SAISS 50 CL", "cause": "FOUR",
     "description": "Chute de température de recuisson (arche)", "duree_h": 2.4, "cadence": 124,
     "intervenant": "Four / Utilités", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 6, 9), "ligne": "L13", "article": "POT ATLAS 105", "cause": "MECANIQUE",
     "description": "Blocage moule ébaucheur — machine IS section 3", "duree_h": 2.9, "cadence": 250,
     "intervenant": "Maintenance mécanique", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 6, 14), "ligne": "L11", "article": "BORDELAISE ANNA VB 75CL PLATE", "cause": "ELECTRIQUE",
     "description": "Défaut variateur moteur convoyeur de sortie", "duree_h": 3.4, "cadence": 88,
     "intervenant": "Maintenance électrique", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 6, 18), "ligne": "L11", "article": "POT DAWN 200 GRS", "cause": "MECANIQUE",
     "description": "Grippage vis de centrage — machine IS", "duree_h": 5.9, "cadence": 100,
     "intervenant": "Maintenance mécanique", "statut": "Résolu (sous surveillance)", "estimee": False},
    {"date": date(2026, 6, 24), "ligne": "L13", "article": "BOUTEILLE JUS 33 CL CB", "cause": "APPRO",
     "description": "Rupture de calcin recyclé — attente approvisionnement", "duree_h": 3.1, "cadence": 103,
     "intervenant": "Logistique / Appro", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 7, 1), "ligne": "L11", "article": "POT DELICIA 72", "cause": "MECANIQUE",
     "description": "Casse convoyeur de sortie four", "duree_h": 1.9, "cadence": 142,
     "intervenant": "Maintenance mécanique", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 7, 8), "ligne": "L12", "article": "STEINE 100 VA", "cause": "FOUR",
     "description": "Dérive thermique zone d'alimentation (feeder)", "duree_h": 4.6, "cadence": 82,
     "intervenant": "Four / Utilités", "statut": "Résolu avec action corrective", "estimee": True},
    {"date": date(2026, 7, 15), "ligne": "L13", "article": "POT 37 CL GRAVE VMM", "cause": "QUALITE",
     "description": "Taux de rebuts anormal — bulles dans le verre", "duree_h": 3.2, "cadence": 188.5,
     "intervenant": "Qualité", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 7, 22), "ligne": "L11", "article": "POT 66 STD", "cause": "SERIE",
     "description": "Changement de série non planifié (urgence commerciale)", "duree_h": 2.2, "cadence": 146,
     "intervenant": "Production", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 7, 29), "ligne": "L11", "article": "BOUTEILLE UNIVERSELLE 1L", "cause": "FOUR",
     "description": "Arrêt four non planifié — défaut brûleur", "duree_h": 18.2, "cadence": 67,
     "intervenant": "Four / Utilités", "statut": "Résolu avec action corrective", "estimee": False},
    {"date": date(2026, 8, 5), "ligne": "L11", "article": "BORDELAISE ANNA VB 50CL CETIE", "cause": "MECANIQUE",
     "description": "Dérèglement machine IS (section 2)", "duree_h": 6.7, "cadence": 111,
     "intervenant": "Maintenance mécanique", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 8, 12), "ligne": "L11", "article": "BOUTEILLE CAPPY 20 CL", "cause": "ELECTRIQUE",
     "description": "Coupure électrique partielle — armoire ligne L11", "duree_h": 2.8, "cadence": 140,
     "intervenant": "Maintenance électrique", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 8, 19), "ligne": "L13", "article": "POT CAFE 50 CARRE", "cause": "APPRO",
     "description": "Retard de livraison matière première (soude)", "duree_h": 3.5, "cadence": 168,
     "intervenant": "Logistique / Appro", "statut": "Résolu", "estimee": False},
    {"date": date(2026, 8, 26), "ligne": "L13", "article": "POT DELICIA 21", "cause": "QUALITE",
     "description": "Arrêt contrôle qualité — dérive dimensionnelle du col", "duree_h": 3.1, "cadence": 248.2,
     "intervenant": "Qualité", "statut": "Résolu", "estimee": False},
]
for _p in PANNES:
    _p["qte_perdue"] = round(_p["duree_h"] * _p["cadence"])

TOTAL_HEURES_ARRET = sum(p["duree_h"] for p in PANNES)
TOTAL_QTE_PERDUE = sum(p["qte_perdue"] for p in PANNES)


# =========================================================
# CAS RÉEL A à Z — panne n°10 (29/07/2026, L11, défaut brûleur, la plus longue)
# =========================================================
CAS_REEL_PANNE = PANNES[9]

CAS_REEL_STEPS = [
    {"n": 1, "horaire": "02:10 – 02:22", "duree_min": 12, "etape": "Détection de l'anomalie",
     "action": "Baisse anormale de la température du four détectée par l'alarme automate ; "
               "confirmation visuelle par l'opérateur.",
     "acteur": "Opérateur ligne L11", "observation": "Alarme automate + ronde opérateur"},
    {"n": 2, "horaire": "02:22 – 03:02", "duree_min": 40, "etape": "Alerte et diagnostic initial",
     "action": "Appel du technicien four de garde ; premier diagnostic sur place : chute de "
               "pression au brûleur, zone 2.",
     "acteur": "Opérateur + Technicien Four", "observation": "—"},
    {"n": 3, "horaire": "03:02 – 03:22", "duree_min": 20, "etape": "Décision d'arrêt contrôlé",
     "action": "Arrêt contrôlé de la ligne L11 pour sécuriser le four et éviter d'endommager le "
               "verre en cours de formage.",
     "acteur": "Chef d'équipe + Technicien Four", "observation": "Évite un arrêt sauvage, plus coûteux"},
    {"n": 4, "horaire": "03:22 – 05:52", "duree_min": 150, "etape": "Diagnostic approfondi",
     "action": "Démontage partiel du brûleur ; contrôle de l'injecteur et de l'électrovanne.",
     "acteur": "Maintenance Four / Utilités", "observation": "Cause identifiée : injecteur encrassé"},
    {"n": 5, "horaire": "05:52 – 09:52", "duree_min": 240, "etape": "Intervention corrective",
     "action": "Remplacement de l'injecteur défectueux et nettoyage de l'électrovanne.",
     "acteur": "Maintenance Four / Utilités", "observation": "Pièce disponible en magasin"},
    {"n": 6, "horaire": "09:52 – 15:52", "duree_min": 360, "etape": "Redémarrage progressif du four",
     "action": "Remise en chauffe progressive du four dans le respect de la courbe de montée en "
               "température.",
     "acteur": "Technicien Four", "observation": "Étape la plus longue — évite de fissurer le réfractaire"},
    {"n": 7, "horaire": "15:52 – 18:52", "duree_min": 180, "etape": "Reprise de la production",
     "action": "Redémarrage de la ligne L11 avec contrôle qualité renforcé sur les premières pièces "
               "produites.",
     "acteur": "Opérateur + Contrôle Qualité", "observation": "—"},
    {"n": 8, "horaire": "18:52 – 19:52", "duree_min": 60, "etape": "Stabilisation et contrôle qualité",
     "action": "Vérification des paramètres (poids, épaisseur, absence de bulles) sur 3 lots "
               "consécutifs avant validation.",
     "acteur": "Contrôle Qualité", "observation": "Validation avant retour en cadence nominale"},
    {"n": 9, "horaire": "19:52 – 20:22", "duree_min": 30, "etape": "Clôture et retour d'expérience",
     "action": "Enregistrement de la panne dans l'historique ; analyse des causes (5M) ; proposition "
               "d'action corrective.",
     "acteur": "Chef Département Production", "observation": "Voir l'onglet Analyse des causes (5M/5S)"},
]

# =========================================================
# ANALYSE DES CAUSES — 5M, 5S et 5 Pourquoi (cas brûleur du 29/07)
# =========================================================
M5_ROWS = [
    {"categorie": "Main-d'œuvre", "cause": "Ronde de surveillance non systématique la nuit",
     "constat": "Délai de détection dépendant de la vigilance de l'opérateur",
     "action": "Renforcer la fréquence des rondes sur poste de nuit"},
    {"categorie": "Matériel", "cause": "Injecteur de brûleur en fin de vie, sans contrôle préventif planifié",
     "constat": "Encrassement progressif non détecté avant la panne",
     "action": "Établir un plan de maintenance préventive des brûleurs"},
    {"categorie": "Matière", "cause": "Variabilité de la pression d'alimentation en combustible",
     "constat": "Favorise l'encrassement / le dérèglement de l'injecteur",
     "action": "Suivre la pression d'alimentation en continu"},
    {"categorie": "Méthode", "cause": "Absence de procédure de contrôle préventif périodique",
     "constat": "Maintenance corrective uniquement, pas de check-list",
     "action": "Créer une fiche de contrôle préventif standard (mensuelle)"},
    {"categorie": "Milieu", "cause": "Four fonctionnant en continu 24 h/24 à haute température",
     "constat": "Environnement contraignant qui accélère l'usure des pièces",
     "action": "Prioriser les organes critiques dans le plan de maintenance (cf. AMDEC)"},
]

S5_ROWS = [
    {"etape": "Seiri (Trier)", "signification": "Éliminer l'inutile",
     "action": "Identifier et retirer les pièces de rechange obsolètes du magasin brûleurs"},
    {"etape": "Seiton (Ranger)", "signification": "Une place pour chaque chose",
     "action": "Prévoir un kit « brûleur Four U2 » pré-positionné et identifié à proximité immédiate du four"},
    {"etape": "Seiso (Nettoyer)", "signification": "Inspecter en nettoyant",
     "action": "Inspection visuelle et nettoyage régulier des injecteurs lors des arrêts programmés"},
    {"etape": "Seiketsu (Standardiser)", "signification": "Rendre visible l'anomalie",
     "action": "Créer une fiche de contrôle préventif standard (check-list mensuelle brûleurs)"},
    {"etape": "Shitsuke (Suivre / Rigueur)", "signification": "Maintenir la discipline",
     "action": "Suivi mensuel de l'application de la check-list par le chef d'équipe, indicateur affiché"},
]

POURQUOI_5 = [
    ("Pourquoi le four s'est-il arrêté ?", "Le brûleur de la zone 2 a perdu de la pression."),
    ("Pourquoi le brûleur a-t-il perdu de la pression ?", "L'injecteur était encrassé/défectueux."),
    ("Pourquoi l'injecteur était-il encrassé ?", "Aucun contrôle préventif n'est réalisé sur cette pièce."),
    ("Pourquoi n'y a-t-il pas de contrôle préventif ?",
     "Il n'existe pas de procédure standardisée pour les brûleurs (maintenance corrective uniquement)."),
    ("Pourquoi la maintenance reste-t-elle corrective ? (cause racine)",
     "Il n'y a pas encore d'indicateur de suivi ni de check-list formalisée sur le terrain."),
]

# =========================================================
# AMDEC — CRITICITÉ DES ORGANES DU FOUR U2
# =========================================================
AMDEC_ORGANES = [
    {"organe": "Compresseur d'air", "fonction": "Alimentation pneumatique (vannes, air de combustion, 3 lignes)",
     "mode": "Usure filtre/joint, chute de pression d'air comprimé",
     "F": 4, "G": 4, "D": 2, "mttr_h": 1.0, "mttr_label": "≈ 1 h", "cause_associee": "MECANIQUE",
     "commentaire": "Point unique de défaillance : alimente les 3 lignes du Four U2. Réparation rapide "
                    "mais impact immédiat et généralisé."},
    {"organe": "Brûleurs", "fonction": "Maintien de la température de fusion du verre",
     "mode": "Encrassement/défaillance de l'injecteur, perte de pression gaz",
     "F": 2, "G": 5, "D": 3, "mttr_h": 18.2, "mttr_label": "≈ 18,2 h", "cause_associee": "FOUR",
     "commentaire": "Panne la plus grave observée sur la période (cas réel du 29/07) ; redémarrage long "
                    "imposé par la courbe de montée en température."},
    {"organe": "Feeder", "fonction": "Dosage et alimentation du verre en fusion vers les machines IS",
     "mode": "Dérive thermique de la zone d'alimentation",
     "F": 2, "G": 4, "D": 3, "mttr_h": 4.6, "mttr_label": "≈ 4,6 h", "cause_associee": "FOUR",
     "commentaire": "Impact direct sur le poids et la qualité du verre formé (cf. cas Steine 100 VA, 08/07)."},
    {"organe": "Machines IS", "fonction": "Formage des articles (moulage, soufflage)",
     "mode": "Blocage/grippage mécanique (moule, vis de centrage)",
     "F": 4, "G": 2, "D": 2, "mttr_h": 3.0, "mttr_label": "≈ 3 h", "cause_associee": "MECANIQUE",
     "commentaire": "Cause la plus fréquente de l'historique, mais impact limité à une section, "
                    "contournable sans arrêt total."},
    {"organe": "Convoyeurs", "fonction": "Transport du verre formé (sortie four, arche de recuisson)",
     "mode": "Casse convoyeur, défaut variateur",
     "F": 3, "G": 2, "D": 2, "mttr_h": 2.0, "mttr_label": "≈ 2 h", "cause_associee": "MECANIQUE",
     "commentaire": "Pannes ponctuelles, correction rapide, faible impact sur la disponibilité globale."},
    {"organe": "Système de refroidissement", "fonction": "Régulation thermique des équipements",
     "mode": "Dérive ou coupure du circuit de refroidissement",
     "F": 2, "G": 3, "D": 2, "mttr_h": 3.0, "mttr_label": "≈ 3 h", "cause_associee": "FOUR",
     "commentaire": "Peu fréquent sur la période observée ; surveillance déjà en place."},
    {"organe": "Régénérateurs", "fonction": "Récupération de la chaleur des fumées",
     "mode": "Encrassement/dégradation progressive de la structure interne",
     "F": 1, "G": 5, "D": 2, "mttr_h": 72.0, "mttr_label": "≈ 72 h", "cause_associee": "FOUR",
     "commentaire": "Très rare, mais réparation lourde nécessitant un refroidissement complet du four."},
    {"organe": "Réfractaires", "fonction": "Structure du four (enceinte de fusion)",
     "mode": "Usure/fissuration progressive du garnissage réfractaire",
     "F": 1, "G": 5, "D": 2, "mttr_h": 504.0, "mttr_label": "plusieurs semaines", "cause_associee": "FOUR",
     "commentaire": "Défaillance exceptionnelle mais critique : implique un arrêt total et une "
                    "reconstruction partielle du four."},
    {"organe": "Armoire électrique / automate", "fonction": "Pilotage et alimentation électrique",
     "mode": "Coupure partielle, défaut composant électrique",
     "F": 2, "G": 3, "D": 1, "mttr_h": 2.5, "mttr_label": "≈ 2,5 h", "cause_associee": "ELECTRIQUE",
     "commentaire": "Détection immédiate par alarme automate ; intervention rapide de la maintenance "
                    "électrique."},
]
for _o in AMDEC_ORGANES:
    _o["C"] = _o["F"] * _o["G"] * _o["D"]
AMDEC_ORGANES.sort(key=lambda o: -o["C"])


def criticite_niveau(c):
    """Retourne (libellé, couleur) selon le seuil de criticité C = F x G x D."""
    if c >= 25:
        return "Critique", "#C0504D"
    if c >= 12:
        return "À surveiller", "#E97132"
    return "Maîtrisé", "#548235"


# =========================================================
# CALCUL DE FIABILITÉ (MTBF / MTTR / DISPONIBILITÉ) — recalculable en direct
# =========================================================
def compute_fiabilite(pannes, periode_jours=PERIODE_JOURS, nb_lignes=NB_LIGNES_U2, incidents_extra=None):
    """Recalcule MTBF, MTTR et disponibilité à partir d'une liste de pannes.

    Accepte des incidents supplémentaires (ex. issus du simulateur d'incident) pour
    permettre un recalcul en direct incluant un scénario simulé par l'utilisateur.
    """
    toutes = list(pannes) + list(incidents_extra or [])
    temps_ouverture_ligne = periode_jours * 24
    temps_ouverture_total = temps_ouverture_ligne * nb_lignes
    nb_pannes = len(toutes)
    heures_arret = sum(p["duree_h"] for p in toutes)
    temps_fonctionnement = temps_ouverture_total - heures_arret
    mtbf = temps_fonctionnement / nb_pannes if nb_pannes else temps_fonctionnement
    mttr = heures_arret / nb_pannes if nb_pannes else 0.0
    dispo = mtbf / (mtbf + mttr) if (mtbf + mttr) else 1.0
    return {
        "nb_pannes": nb_pannes,
        "heures_arret": heures_arret,
        "temps_ouverture_total": temps_ouverture_total,
        "temps_fonctionnement": temps_fonctionnement,
        "mtbf": mtbf,
        "mttr": mttr,
        "dispo": dispo,
    }


def mttr_par_cause(pannes):
    """MTTR moyen par catégorie de panne (occurrences, heures cumulées, MTTR moyen)."""
    agg = {}
    for p in pannes:
        occ, heures = agg.get(p["cause"], (0, 0.0))
        agg[p["cause"]] = (occ + 1, heures + p["duree_h"])
    ordered = sorted(agg.items(), key=lambda kv: -kv[1][1])
    return [
        {"cause": cause, "libelle": CAUSE_PANNE_LABELS[cause], "occurrences": occ,
         "heures": round(heures, 1), "mttr_moyen": round(heures / occ, 1)}
        for cause, (occ, heures) in ordered
    ]


# =========================================================
# FICHE DE CALCUL DE BESOIN DE PRODUCTION (chapitre 6.2.4 — Steine 100 VA / L12)
# =========================================================
BESOIN_DEFAUT = {
    "article": "Steine 100 VA", "ligne": "L12", "four": "U2",
    "besoin_client": 3_002_454, "stock_actuel": 376_011, "stock_rz": 21_404,
    "ventes_realisees": 2_533_986, "palettes_dispo": 44, "capacite_palette": 1014,
}


def calc_besoin(besoin_client, stock_actuel, stock_rz, ventes_realisees, palettes_dispo, capacite_palette):
    """Reproduit exactement la logique de la fiche de calcul de besoin (chapitre 6.2.4) :

    Besoin net à couvrir = Besoin client − Stock actuel − Stock R+Z − Ventes réalisées
    Reste à produire      = Besoin net − (Palettes déjà disponibles x Capacité palette)
    Palettes à produire   = partie entière de Reste à produire / Capacité palette
    """
    besoin_net = besoin_client - stock_actuel - stock_rz - ventes_realisees
    equiv_palettes_dispo = palettes_dispo * capacite_palette
    reste_a_produire = besoin_net - equiv_palettes_dispo
    palettes_a_produire = int(reste_a_produire // capacite_palette) if capacite_palette else 0
    return {
        "besoin_net": besoin_net,
        "equiv_palettes_dispo": equiv_palettes_dispo,
        "reste_a_produire": max(reste_a_produire, 0),
        "palettes_a_produire": max(palettes_a_produire, 0),
    }


# =========================================================
# SIMULATEUR D'INCIDENT — génère un scénario d'intervention pour un organe donné
# =========================================================
def organe_par_nom(nom):
    return next(o for o in AMDEC_ORGANES if o["organe"] == nom)


def cadence_moyenne_ligne(ligne, defaut=130):
    """Cadence moyenne observée (u/h) sur une ligne donnée, d'après l'historique
    des pannes ; utilisée pour estimer la quantité perdue d'un incident simulé."""
    cadences = [p["cadence"] for p in PANNES if p["ligne"] == ligne]
    if not cadences:
        return defaut
    return sum(cadences) / len(cadences)


def generer_scenario(organe):
    """Retourne la chronologie d'intervention pour un organe donné.

    Pour les Brûleurs, réutilise le cas réel détaillé (29/07/2026, 9 étapes).
    Pour les autres organes, génère une chronologie type à 6 étapes dont les
    durées sont mises à l'échelle du MTTR estimé de l'organe (grille AMDEC).
    """
    if organe["organe"] == "Brûleurs":
        return [dict(s) for s in CAS_REEL_STEPS]

    total_min = max(organe["mttr_h"] * 60, 6)
    props = [0.05, 0.20, 0.05, 0.40, 0.20, 0.10]
    labels = [
        "Détection de l'anomalie",
        "Diagnostic initial",
        "Décision d'arrêt contrôlé",
        "Intervention corrective",
        "Redémarrage / remise en production",
        "Clôture et retour d'expérience",
    ]
    actions = [
        f"Alerte automate / ronde opérateur signalant une anomalie sur : {organe['organe']} "
        f"({organe['fonction']}).",
        f"Diagnostic de terrain par l'équipe maintenance : {organe['mode']}.",
        "Arrêt contrôlé de la ligne concernée pour sécuriser l'intervention et éviter d'aggraver le défaut.",
        f"Intervention ciblée sur l'organe concerné pour traiter la cause identifiée ({organe['mode']}).",
        "Remise en route progressive et contrôle des paramètres avant retour en cadence nominale.",
        "Enregistrement de l'incident dans l'historique des pannes et mise à jour de la fiche AMDEC.",
    ]
    acteurs = ["Opérateur", "Technicien Maintenance", "Chef d'équipe",
               "Équipe Maintenance", "Technicien / Opérateur", "Chef Département Production"]
    steps = []
    for i, (p, lab, act, who) in enumerate(zip(props, labels, actions, acteurs), start=1):
        steps.append({
            "n": i, "etape": lab, "duree_min": max(1, round(total_min * p)),
            "action": act, "acteur": who, "horaire": "", "observation": "",
        })
    return steps
