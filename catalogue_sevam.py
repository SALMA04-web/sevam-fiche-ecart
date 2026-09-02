# -*- coding: utf-8 -*-
"""
Catalogue des articles SEVAM (fours, lignes, produits) et rôles applicatifs.

Construit à partir de 3 fichiers réels transmis par l'entreprise :
  - F.P.A.S POT DELICIA 37 (+ version corrigée) -> catalogue "verre creux"
    (134 articles réels, poids de plan réels) et journal de production réel
    "BD des changements" (2308 lignes, 2013-2024) qui a permis de retrouver
    la vraie codification four/ligne pour U2 et U3.
  - Planner Gobeleterie 2026 -> catalogue "gobeleterie nue" (34 articles réels)
    et "articles de décor" (39 articles réels, atelier de personnalisation).

39 articles supplémentaires ont été ajoutés (source='genere') pour élargir le choix
disponible dans le formulaire, en conservant le style de nommage réel de SEVAM ;
ils sont clairement identifiables via le champ 'source'.
"""

# =========================================================
# FOURS, LIGNES ET DÉPARTEMENTS
# =========================================================
# Codification réelle confirmée par le journal de production ERP (BD des changements) :
#   Four U2 -> lignes L11, L12, L13
#   Four U3 -> lignes L21, L22, L23
# Le fichier ne couvre pas U1 (Roches Noires) ni U4 (le plus récent) : leur codification
# ci-dessous prolonge la même logique observée (rang du four -> dizaine, n° de ligne -> unité)
# et reste À VÉRIFIER auprès de SEVAM avant tout usage hors PFA.
FOURS = {
    "U1": {"index": 0, "site": "Roches Noires", "departement": "Gobeleterie",
           "statut": "Le plus ancien four du site — spécialisé verres à thé / jus", "ligne_source": "extrapolee"},
    "U2": {"index": 1, "site": "Tit Mellil", "departement": "Verre creux",
           "statut": "Four ancien — bouteilles / pots", "ligne_source": "reelle (BD des changements)"},
    "U3": {"index": 2, "site": "Tit Mellil", "departement": "Verre creux",
           "statut": "Four ancien — bouteilles / pots", "ligne_source": "reelle (BD des changements)"},
    "U4": {"index": 3, "site": "Tit Mellil", "departement": "Verre creux",
           "statut": "Four récent (en service depuis ~4 ans) — bouteilles / pots", "ligne_source": "extrapolee"},
}

LIGNES = []
for _four_code, _info in FOURS.items():
    for _n_ligne in (1, 2, 3):
        _ligne_code = f"L{_info['index']}{_n_ligne}"
        LIGNES.append((_ligne_code, _four_code))

LIGNE_LABELS = {code: f"{code} — Four {four} ({FOURS[four]['site']})" for code, four in LIGNES}

# Atelier transverse : ne dépend d'aucun four particulier (personnalisation en sortie de four)
ATELIER_DECOR = "Atelier Décor"

DEPARTEMENTS = {
    "Gobeleterie": {"fours": ["U1"], "description": "Verres à thé, café et jus (four U1, Roches Noires)"},
    "Verre creux": {"fours": ["U2", "U3", "U4"], "description": "Bouteilles, pots et bocaux (fours U2/U3/U4, Tit Mellil)"},
    "Décor": {"fours": [], "description": "Personnalisation / décoration après sortie de four, tous fours confondus"},
}

CAUSES = {
    "FOUR": "Arrêt four non planifié",
    "APPRO": "Retard livraison matière première",
    "SERIE": "Changement de série non anticipé",
    "QUALITE": "Rebuts / non-conformités",
    "DECOR": "Incident à l'atelier décor (casse, défaut d'impression)",
    "AUTRE": "Cause diverse",
}

# =========================================================
# RÔLES ET NIVEAUX D'ACCÈS (démonstration — pas d'authentification réelle)
# =========================================================
ROLES = ["Opérateur", "Chef de service", "Chef de département", "Directeur Général (DG)"]

# Site principal de la stagiaire (utilisé pour mettre en avant Tit Mellil par défaut
# dans l'interface, sans masquer Roches Noires).
SITE_PRINCIPAL = "Tit Mellil"
SITES = {
    "Tit Mellil": ["U2", "U3", "U4"],
    "Roches Noires": ["U1"],
}

# =========================================================
# ANNUAIRE RÉEL — vrais types d'accès (issus de la fiche de validation avant
# lancement, réf. FN-PR-121-05-V.00, client SACOFRINA SA, article APO 33 CL VA
# SACO, ligne L-23, site de Tit Mellil — voir Figure 3.4 du rapport PFA) et de
# l'organigramme du rapport. Chaque entrée associe une vraie personne / un vrai
# poste à un niveau d'accès (tier) et un périmètre de données (scope) réutilisant
# la structure four/ligne/département déjà validée.
#
# scope_type :
#   "ligne"  -> une seule ligne de production (Opérateur)
#   "four"   -> un four et toutes ses lignes (Chef de service)
#   "site"   -> tous les fours d'un site, ex. Tit Mellil = U2+U3+U4 (Chef de
#               département "site", ex. Supply Chain, SMI, Qualité process)
#   "dept"   -> un département au sens gobeleterie/verre creux/décor
#   "all"    -> tous les sites, tous les départements (Direction)
# =========================================================
ANNUAIRE_REEL = [
    {"nom": "Adnane RAFIK", "poste": "Chef Service Supply Chain",
     "tier": "Chef de service", "scope_type": "site", "scope_value": "Tit Mellil",
     "source": "reel", "note": "Encadrant de stage — service Logistique, Tit Mellil."},
    {"nom": "Youssef HAFFOU", "poste": "Chef Département Supply Chain",
     "tier": "Chef de département", "scope_type": "site", "scope_value": "Tit Mellil",
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Fatima Zahra AOUAB", "poste": "Chef Département SMI (Système de Management Intégré)",
     "tier": "Chef de département", "scope_type": "site", "scope_value": "Tit Mellil",
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Abderrahim BELKHDIM", "poste": "Chef Département Production — Four 2 (U2)",
     "tier": "Chef de service", "scope_type": "four", "scope_value": "U2",
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Abderrahim ZNIDI", "poste": "Chef Département Qualité Process",
     "tier": "Chef de département", "scope_type": "site", "scope_value": "Tit Mellil",
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Asmaa KDAH", "poste": "Chef Département Contrôle de Gestion",
     "tier": "Chef de département", "scope_type": "all", "scope_value": None,
     "source": "reel", "note": "Fiche de validation avant lancement — signataire (vue coûts inter-sites)."},
    {"nom": "Abderrahim EL ABBADI", "poste": "Directeur Exploitation",
     "tier": "Directeur Général (DG)", "scope_type": "all", "scope_value": None,
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Hassan TAHRI", "poste": "Directeur Commercial & Marketing",
     "tier": "Directeur Général (DG)", "scope_type": "all", "scope_value": None,
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Bouchra SNAIBI", "poste": "Directeur Administratif et Financier",
     "tier": "Directeur Général (DG)", "scope_type": "all", "scope_value": None,
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
    {"nom": "Karim AMMAR", "poste": "Directeur Général Délégué",
     "tier": "Directeur Général (DG)", "scope_type": "all", "scope_value": None,
     "source": "reel", "note": "Fiche de validation avant lancement — signataire."},
]

# Postes de chefs de service Four 1 / Four 3 / Four 4 : aucun nom réel confirmé
# n'apparaît dans les documents transmis (seul le Four 2 a un signataire réel sur
# la fiche de validation disponible) — ces postes restent donc "à pourvoir" côté
# annuaire plutôt que de fabriquer un nom, et apparaissent uniquement dans le
# formulaire de connexion "Autre" avec une mention explicite.
POSTES_FOUR_NON_CONFIRMES = {
    "U1": "Chef Département Production — Four 1 (nom à confirmer)",
    "U3": "Chef Département Production — Four 3 (nom à confirmer)",
    "U4": "Chef Département Production — Four 4 (nom à confirmer)",
}

# =========================================================
# CATALOGUE DES ARTICLES (246 références : 207 réelles + 39 ajoutées pour élargir le choix)
# =========================================================
ARTICLES = [
    {"article": "PIETRA 25 CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": 195, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 500 VB ALMA", "famille": "Verre creux (bouteilles / pots)", "poids": 520, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE BG 30 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 380, "decore": False, "marque": None, "source": "reel"},
    {"article": "ALE 50 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 385, "decore": False, "marque": None, "source": "reel"},
    {"article": "BG TERRA PESANTE 75CL VH", "famille": "Verre creux (bouteilles / pots)", "poids": 808, "decore": False, "marque": None, "source": "reel"},
    {"article": "SIROP DUVAL 75 CL V.B.", "famille": "Verre creux (bouteilles / pots)", "poids": 400, "decore": False, "marque": None, "source": "reel"},
    {"article": "AIN SAISS 75 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 500, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DELICIA 37", "famille": "Verre creux (bouteilles / pots)", "poids": 200, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT  TRAMIER 37 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 190, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 37 GRAVE AICHA", "famille": "Verre creux (bouteilles / pots)", "poids": 200, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT PATE A TARTINER 37CL", "famille": "Verre creux (bouteilles / pots)", "poids": 200, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT  21 GRAVE AICHA", "famille": "Verre creux (bouteilles / pots)", "poids": 125, "decore": False, "marque": None, "source": "reel"},
    {"article": "SIDI ALI 75 CL VXB", "famille": "Verre creux (bouteilles / pots)", "poids": 500, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE UNIVERSELLE 1L", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORD. FLORENCE VB 75CL  CETIE", "famille": "Verre creux (bouteilles / pots)", "poids": 600, "decore": False, "marque": None, "source": "reel"},
    {"article": "BG 100 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 800, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT  72 CL GRAVE VMM", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT PATE A TARTINER 72CL", "famille": "Verre creux (bouteilles / pots)", "poids": 340, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE SEDUCTION 75 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 575, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DELICIA 72", "famille": "Verre creux (bouteilles / pots)", "poids": 330, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE  50 CL ALE VB", "famille": "Verre creux (bouteilles / pots)", "poids": 350, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE VIPO 75 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT  37 CL GRAVE VMM", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DELICIA 21", "famille": "Verre creux (bouteilles / pots)", "poids": 125, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 72 STD", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT ATLAS 210", "famille": "Verre creux (bouteilles / pots)", "poids": 125, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 21", "famille": "Verre creux (bouteilles / pots)", "poids": 125, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT ATLAS 105", "famille": "Verre creux (bouteilles / pots)", "poids": 90, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOCAL 37 CLS ETK", "famille": "Verre creux (bouteilles / pots)", "poids": 170, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 66 STD", "famille": "Verre creux (bouteilles / pots)", "poids": 275, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT GRAVE 72 AICHA", "famille": "Verre creux (bouteilles / pots)", "poids": 330, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 37  STD", "famille": "Verre creux (bouteilles / pots)", "poids": 170, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT FRUITA  660 ML", "famille": "Verre creux (bouteilles / pots)", "poids": 280, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DELICIA 90", "famille": "Verre creux (bouteilles / pots)", "poids": 100, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT  21 CL GRAVE VMM", "famille": "Verre creux (bouteilles / pots)", "poids": 125, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE SIDI ALI 50 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 360, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT CAFE JODA JAR 50GR", "famille": "Verre creux (bouteilles / pots)", "poids": 165, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DAWN 50 GRS", "famille": "Verre creux (bouteilles / pots)", "poids": 150, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DAWN 100 GRS", "famille": "Verre creux (bouteilles / pots)", "poids": 245, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 106 ML", "famille": "Verre creux (bouteilles / pots)", "poids": 105, "decore": False, "marque": None, "source": "reel"},
    {"article": "AIN SAISS 50 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 350, "decore": False, "marque": None, "source": "reel"},
    {"article": "PIETRA 25 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 195, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 37,5 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 320, "decore": False, "marque": None, "source": "reel"},
    {"article": "AIN SAISS 33 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 240, "decore": False, "marque": None, "source": "reel"},
    {"article": "BREMER 65 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 480, "decore": False, "marque": None, "source": "reel"},
    {"article": "BREMER 33 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "reel"},
    {"article": "APO 33 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 320, "decore": False, "marque": None, "source": "reel"},
    {"article": "BIERE  CASABLANCA 33 CL VA LN", "famille": "Verre creux (bouteilles / pots)", "poids": 280, "decore": False, "marque": None, "source": "reel"},
    {"article": "BD CONICA PESANTE 75CL VH", "famille": "Verre creux (bouteilles / pots)", "poids": 730, "decore": False, "marque": None, "source": "reel"},
    {"article": "ALE 50 CL VA SACO VM", "famille": "Verre creux (bouteilles / pots)", "poids": 385, "decore": False, "marque": None, "source": "reel"},
    {"article": "GBM 24 VV", "famille": "Verre creux (bouteilles / pots)", "poids": 180, "decore": False, "marque": None, "source": "reel"},
    {"article": "CASTEL BEER 33 VA", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "reel"},
    {"article": "BD CONICA 300 SP 75CL VH", "famille": "Verre creux (bouteilles / pots)", "poids": 550, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE  75 CL 500 VH ALMA", "famille": "Verre creux (bouteilles / pots)", "poids": 520, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE DORON 1L VH", "famille": "Verre creux (bouteilles / pots)", "poids": 470, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE 1 L AVIS BVS VV CDM", "famille": "Verre creux (bouteilles / pots)", "poids": 460, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOURGUIGNONNE 500 VB", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORD. FLORENCE VH75CL  CETIE", "famille": "Verre creux (bouteilles / pots)", "poids": 600, "decore": False, "marque": None, "source": "reel"},
    {"article": "BREMER 24CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": 290, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 75 CL AVIS BVS VV", "famille": "Verre creux (bouteilles / pots)", "poids": 520, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE ANNA VH 75 CL CETIE", "famille": "Verre creux (bouteilles / pots)", "poids": 575, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOURGUIGNONNE 75 CL 500 VH", "famille": "Verre creux (bouteilles / pots)", "poids": 530, "decore": False, "marque": None, "source": "reel"},
    {"article": "BLLE EAU DE ROSE 1L  AVIS VV", "famille": "Verre creux (bouteilles / pots)", "poids": 500, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 37,5 VV VP", "famille": "Verre creux (bouteilles / pots)", "poids": 320, "decore": False, "marque": None, "source": "reel"},
    {"article": "PIETRA 25 VA", "famille": "Verre creux (bouteilles / pots)", "poids": 195, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 37,5  VH", "famille": "Verre creux (bouteilles / pots)", "poids": 320, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOURGUIGNONNE 37 VH", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BD CONICA PESANTE 75CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 730, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE OULMES 75CL PREMIUM", "famille": "Verre creux (bouteilles / pots)", "poids": 560, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 580 ML", "famille": "Verre creux (bouteilles / pots)", "poids": 280, "decore": False, "marque": None, "source": "reel"},
    {"article": "AIN SOLTANE 75 CL VXB", "famille": "Verre creux (bouteilles / pots)", "poids": 530, "decore": False, "marque": None, "source": "reel"},
    {"article": "TROPICANA 1 L VB", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT SUPER 314 ML", "famille": "Verre creux (bouteilles / pots)", "poids": 165, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE OULMES FRUITE 25 VIS", "famille": "Verre creux (bouteilles / pots)", "poids": 185, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT FRUITA  300 ML", "famille": "Verre creux (bouteilles / pots)", "poids": 175, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT CAFE 50 CARRE", "famille": "Verre creux (bouteilles / pots)", "poids": 140, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE  25 CL VB CLASSIQUE", "famille": "Verre creux (bouteilles / pots)", "poids": 185, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 140 GRAVE CHERGUI", "famille": "Verre creux (bouteilles / pots)", "poids": 80, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 18,7 VH STD", "famille": "Verre creux (bouteilles / pots)", "poids": 185, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 85 STD", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT CAFE 100 CARRE", "famille": "Verre creux (bouteilles / pots)", "poids": 245, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE CIGOGNE 25 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 230, "decore": False, "marque": None, "source": "reel"},
    {"article": "BLLE ALE STORK 47,5 CL VC VV", "famille": "Verre creux (bouteilles / pots)", "poids": 360, "decore": False, "marque": None, "source": "reel"},
    {"article": "OULMES 33 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 240, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE BG 50 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 420, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT DAWN 200 GRS", "famille": "Verre creux (bouteilles / pots)", "poids": 430, "decore": False, "marque": None, "source": "reel"},
    {"article": "TROPICANA POINT BLANC", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE BG 30 VB VM", "famille": "Verre creux (bouteilles / pots)", "poids": 380, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT 300 ML", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT  AICHA 106 ML NM", "famille": "Verre creux (bouteilles / pots)", "poids": 90, "decore": False, "marque": None, "source": "reel"},
    {"article": "COCA COLA  20 A NON DECOREE", "famille": "Verre creux (bouteilles / pots)", "poids": 210, "decore": False, "marque": None, "source": "reel"},
    {"article": "COCA COLA 30 CL NON DECOREE", "famille": "Verre creux (bouteilles / pots)", "poids": 380, "decore": False, "marque": None, "source": "reel"},
    {"article": "MIRINDA 35 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "PEPSI 35 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 360, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE SKITTLE 30 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT ANFORA 160 TO", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "APO 33 CL VA SACO VMF", "famille": "Verre creux (bouteilles / pots)", "poids": 320, "decore": False, "marque": None, "source": "reel"},
    {"article": "BREMER 33 CL VV VM", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "reel"},
    {"article": "SEVEN UP 35 CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE  50 CL ALE VV", "famille": "Verre creux (bouteilles / pots)", "poids": 385, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE SEDUCTION 75 CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": 575, "decore": False, "marque": None, "source": "reel"},
    {"article": "SPRITE DIMPLE 200ML NON DECORE", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BEER CASTEL 33 VA VMF", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "reel"},
    {"article": "BREMER 65 CL VA SACO VM", "famille": "Verre creux (bouteilles / pots)", "poids": 480, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOURGUIGNONNE 75 VV VP", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE 1L 6 ETOILES VH LOC", "famille": "Verre creux (bouteilles / pots)", "poids": 500, "decore": False, "marque": None, "source": "reel"},
    {"article": "SPRITE DIMPLE 300ML  DECORE", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 18.7 VV STD", "famille": "Verre creux (bouteilles / pots)", "poids": 185, "decore": False, "marque": None, "source": "reel"},
    {"article": "BIERE  CASABLANCA 25 CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": 185, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT CAFE 200 CARRE", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BELLE KRITER 20 CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": 230, "decore": False, "marque": None, "source": "reel"},
    {"article": "BG ECOVA EVOL 77 PLU", "famille": "Verre creux (bouteilles / pots)", "poids": 440, "decore": False, "marque": None, "source": "reel"},
    {"article": "BG ECOVA EVOL BVS HAVANE77 PLU", "famille": "Verre creux (bouteilles / pots)", "poids": 440, "decore": False, "marque": None, "source": "reel"},
    {"article": "CARLSBERG 25 CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE UNIVERSELLE 20 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 210, "decore": False, "marque": None, "source": "reel"},
    {"article": "BDX TRAD ALL ECO VERT SR 75", "famille": "Verre creux (bouteilles / pots)", "poids": 440, "decore": False, "marque": None, "source": "reel"},
    {"article": "MX DOUBLE RE CUVE 78.1 CMC VV", "famille": "Verre creux (bouteilles / pots)", "poids": 560, "decore": False, "marque": None, "source": "reel"},
    {"article": "ALE 50 CL VV VM", "famille": "Verre creux (bouteilles / pots)", "poids": 385, "decore": False, "marque": None, "source": "reel"},
    {"article": "BOUTEILLE 33CL VV  BREMER MAD", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "Apo gravée Youki 33 VB VM", "famille": "Verre creux (bouteilles / pots)", "poids": 320, "decore": False, "marque": None, "source": "reel"},
    {"article": "BUD APO 65 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 530, "decore": False, "marque": None, "source": "reel"},
    {"article": "BUD APO 65 CL VA SACO VM", "famille": "Verre creux (bouteilles / pots)", "poids": 530, "decore": False, "marque": None, "source": "reel"},
    {"article": "BEER CASTEL 50 VA VMF", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "Bremer 30 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 290, "decore": False, "marque": None, "source": "reel"},
    {"article": "Bambie 30 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 345, "decore": False, "marque": None, "source": "reel"},
    {"article": "BREMER 33 CL VA SACO VM", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE VIPO 75CL VV", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "Guinness Genius 33 VA VM", "famille": "Verre creux (bouteilles / pots)", "poids": 285, "decore": False, "marque": None, "source": "reel"},
    {"article": "Malta Guinness 30 VA", "famille": "Verre creux (bouteilles / pots)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "Guinness Genius 33 VA", "famille": "Verre creux (bouteilles / pots)", "poids": 285, "decore": False, "marque": None, "source": "reel"},
    {"article": "Steine 100 VA", "famille": "Verre creux (bouteilles / pots)", "poids": 729, "decore": False, "marque": None, "source": "reel"},
    {"article": "POT GRAVE AICHA 21 EPAL", "famille": "Verre creux (bouteilles / pots)", "poids": 129, "decore": False, "marque": None, "source": "reel"},
    {"article": "BORDELAISE 500 VB ALMA RWS", "famille": "Verre creux (bouteilles / pots)", "poids": 520, "decore": False, "marque": None, "source": "reel"},
    {"article": "OULMES FRUITE 25 VIS BAGUE EMO", "famille": "Verre creux (bouteilles / pots)", "poids": 185, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ CAFE ARABICA FL", "famille": "Gobeleterie (verres)", "poids": 95.84915378955118, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/ISLANDE FRANCE D", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/ISLANDE FRANCE D GM", "famille": "Gobeleterie (verres)", "poids": 184, "decore": False, "marque": None, "source": "reel"},
    {"article": "MOUMTAZ 30", "famille": "Gobeleterie (verres)", "poids": 275, "decore": False, "marque": None, "source": "reel"},
    {"article": "F L G M (12)", "famille": "Gobeleterie (verres)", "poids": 126.72257374823054, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/MOUMTAZ FB", "famille": "Gobeleterie (verres)", "poids": 263, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE TOKYO", "famille": "Gobeleterie (verres)", "poids": 107, "decore": False, "marque": None, "source": "reel"},
    {"article": "RIAD", "famille": "Gobeleterie (verres)", "poids": 107, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE GRAVES PRESTIGE", "famille": "Gobeleterie (verres)", "poids": 158, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/O S L O", "famille": "Gobeleterie (verres)", "poids": 195, "decore": False, "marque": None, "source": "reel"},
    {"article": "E X P R E S S", "famille": "Gobeleterie (verres)", "poids": 125, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/THE 14 COTES", "famille": "Gobeleterie (verres)", "poids": 84, "decore": False, "marque": None, "source": "reel"},
    {"article": "DIFFUSEUR GF 20X20", "famille": "Gobeleterie (verres)", "poids": 689.9784833377082, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE GRAVES ELEGANCE", "famille": "Gobeleterie (verres)", "poids": 158, "decore": False, "marque": None, "source": "reel"},
    {"article": "CONIQUE 16 PRESSE X12", "famille": "Gobeleterie (verres)", "poids": 157.43481786848673, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE YACOUTA", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE ISLANDE FL DV", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ ICEGLASS CERAMICA GD", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ CASABAHIA PE (R)", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/ISLANDE SELECTION  PM", "famille": "Gobeleterie (verres)", "poids": 150, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/CONIQUE 18", "famille": "Gobeleterie (verres)", "poids": 119.61403508771933, "decore": False, "marque": None, "source": "reel"},
    {"article": "CONIQUE 28", "famille": "Gobeleterie (verres)", "poids": 214, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/THE ISLANDE PM", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ CAFÉ PDT ECONOMIQUE VERA", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "24/VERRINE NUE", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ ICEGLASS CERAMICA", "famille": "Gobeleterie (verres)", "poids": 258, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ CAFE ARABICA FL NV", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE ISLANDE FRANCE D GM NV", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "CENDRIER CUBA", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/THE BOOK", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/THE LANCIA SELECTION", "famille": "Gobeleterie (verres)", "poids": 132, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V / THE CONIQUE 5 PRESSE NV", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ EAU MOUMTAZ 30 NV", "famille": "Gobeleterie (verres)", "poids": None, "decore": False, "marque": None, "source": "reel"},
    {"article": "6V/ ISLANDE AQUA", "famille": "Gobeleterie (verres)", "poids": 298, "decore": False, "marque": None, "source": "reel"},
    {"article": "12V/ THE TOKYO FIBULE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/TOKYO AHLAN WESAHLAN BLEU", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 ARCHE BLEU", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/ARABICA CAFÉ  CARRION BLANC", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/ARABICA CARTE NOIRE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Carte Noire", "source": "reel"},
    {"article": "12V/C5 CAFÉ CARRION BLANC", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/EXPRESS CAFÉS CARRION BLAN", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/EXPRESS MECAFE SIMILI OR", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "EXPRESS CARTE NOIRE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Carte Noire", "source": "reel"},
    {"article": "6V/C5 NESCAFE CLASSIQUE (N.R)", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Nescafé", "source": "reel"},
    {"article": "12V/EXPRESS TOTAL ENERGIES BLA", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "TotalEnergies", "source": "reel"},
    {"article": "12V/ THE C16 FIBULE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/TOKYO ANBA", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 NOUARA SO", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE ISLANDE GM EMPIRE BLEU", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/THE ISLANDE GM SAMARA NV", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/THE C16 CRAQUELE TOP HOME", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/C28 POINT BLANC", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/EAU ICEGLASS TENDANCE SO", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/ THE TOKYO NOUVEAU DECOR", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 ARCHE VERT", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 MARHABA NOUVEAU", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 NOUVEAU DECOR", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/ARABICA DÉCOR AB SO", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/C5 LOGO SOMATHES DEPOLI BLA", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/EAU ICEGLASS ARC BL", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/CONIQUE 5 BUTAGAZ", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Butagaz", "source": "reel"},
    {"article": "4V/CONIQUE 28 D", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/C16 ASTA SIMILI OR", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "6V/C5 SHELL ADVANCE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Shell", "source": "reel"},
    {"article": "6V CAFE ROMA", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "TROPICANA  POINT BL  ET  BCH", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 AMBASSADEUR S.O", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE TOKYO WARDA VERT", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE LUX TRADITION ANBA NV", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 TAJ BLANC", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 TAJ NOIR", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE TOKYO ZELIJE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE C16 LOTUS", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": None, "source": "reel"},
    {"article": "12V/THE CONIQUE 5 PRESSE", "famille": "Gobeleterie (verres)", "poids": 155, "decore": False, "marque": None, "source": "genere"},
    {"article": "6V/THE MARRAKECH SELECTION", "famille": "Gobeleterie (verres)", "poids": 118, "decore": False, "marque": None, "source": "genere"},
    {"article": "12V/ISLANDE FRANCE D PM", "famille": "Gobeleterie (verres)", "poids": 150, "decore": False, "marque": None, "source": "genere"},
    {"article": "6V/CAFE ARABICA GM", "famille": "Gobeleterie (verres)", "poids": 132, "decore": False, "marque": None, "source": "genere"},
    {"article": "12V/THE FES PRESTIGE", "famille": "Gobeleterie (verres)", "poids": 160, "decore": False, "marque": None, "source": "genere"},
    {"article": "6V/ICEGLASS TENDANCE NU", "famille": "Gobeleterie (verres)", "poids": 122, "decore": False, "marque": None, "source": "genere"},
    {"article": "CONIQUE 5 PRESSE X12 NU", "famille": "Gobeleterie (verres)", "poids": 90, "decore": False, "marque": None, "source": "genere"},
    {"article": "6V/MOUMTAZ GM", "famille": "Gobeleterie (verres)", "poids": 140, "decore": False, "marque": None, "source": "genere"},
    {"article": "12V/THE AGADIR SELECTION", "famille": "Gobeleterie (verres)", "poids": 158, "decore": False, "marque": None, "source": "genere"},
    {"article": "VERRINE 12/NUE", "famille": "Gobeleterie (verres)", "poids": 60, "decore": False, "marque": None, "source": "genere"},
    {"article": "12V/THE C16 AFRIQUIA GAZ", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Afriquia Gaz", "source": "genere"},
    {"article": "6V/C5 INWI LOGO BLEU", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Inwi", "source": "genere"},
    {"article": "12V/THE TOKYO MAROC TELECOM", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Maroc Telecom", "source": "genere"},
    {"article": "6V/CAFE ARABICA ATTIJARIWAFA BANK", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Attijariwafa Bank", "source": "genere"},
    {"article": "12V/THE C16 OCP LOGO", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "OCP Group", "source": "genere"},
    {"article": "6V/C5 SHELL HELIX", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Shell", "source": "genere"},
    {"article": "12V/EXPRESS TOTAL ENERGIES VERT", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "TotalEnergies", "source": "genere"},
    {"article": "6V/ARABICA CARTE NOIRE PRESTIGE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Carte Noire", "source": "genere"},
    {"article": "12V/THE C16 NESCAFE GOLD", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Nescafé", "source": "genere"},
    {"article": "6V/CONIQUE 5 BUTAGAZ NOUVEAU", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Butagaz", "source": "genere"},
    {"article": "12V/THE TOKYO MAROC TOURISME", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Office National Marocain du Tourisme", "source": "genere"},
    {"article": "6V/C5 LESIEUR CRISTAL", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Lesieur Cristal", "source": "genere"},
    {"article": "12V/THE C16 CENTRALE DANONE", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Centrale Danone", "source": "genere"},
    {"article": "6V/EAU ICEGLASS SIDI ALI EVENT", "famille": "Gobeleterie (verres)", "poids": None, "decore": True, "marque": "Sidi Ali", "source": "genere"},
    {"article": "POT DELICIA 55", "famille": "Verre creux (bouteilles / pots)", "poids": 220, "decore": False, "marque": None, "source": "genere"},
    {"article": "POT TRAMIER 72 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 300, "decore": False, "marque": None, "source": "genere"},
    {"article": "POT GRAVE AICHA 55", "famille": "Verre creux (bouteilles / pots)", "poids": 190, "decore": False, "marque": None, "source": "genere"},
    {"article": "BOUTEILLE SIDI ALI 33 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 260, "decore": False, "marque": None, "source": "genere"},
    {"article": "AIN SAISS 1L VB", "famille": "Verre creux (bouteilles / pots)", "poids": 560, "decore": False, "marque": None, "source": "genere"},
    {"article": "BORDELAISE OULMES 75 CL VB", "famille": "Verre creux (bouteilles / pots)", "poids": 520, "decore": False, "marque": None, "source": "genere"},
    {"article": "POT CAFE 72 CARRE", "famille": "Verre creux (bouteilles / pots)", "poids": 260, "decore": False, "marque": None, "source": "genere"},
    {"article": "BOUTEILLE BAMBI 50 VB", "famille": "Verre creux (bouteilles / pots)", "poids": 400, "decore": False, "marque": None, "source": "genere"},
    {"article": "POT DAWN 300 GRS", "famille": "Verre creux (bouteilles / pots)", "poids": 470, "decore": False, "marque": None, "source": "genere"},
    {"article": "BREMER 50 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 400, "decore": False, "marque": None, "source": "genere"},
    {"article": "APO 50 CL VA SACO", "famille": "Verre creux (bouteilles / pots)", "poids": 400, "decore": False, "marque": None, "source": "genere"},
    {"article": "POT FRUITA 450 ML", "famille": "Verre creux (bouteilles / pots)", "poids": 230, "decore": False, "marque": None, "source": "genere"},
    {"article": "BOUTEILLE OULMES CLASSIC 1L", "famille": "Verre creux (bouteilles / pots)", "poids": 480, "decore": False, "marque": None, "source": "genere"},
    {"article": "POT ATLAS 55", "famille": "Verre creux (bouteilles / pots)", "poids": 155, "decore": False, "marque": None, "source": "genere"},
    {"article": "BORDELAISE ANNA VB 75 CL", "famille": "Verre creux (bouteilles / pots)", "poids": 560, "decore": False, "marque": None, "source": "genere"},
]

ARTICLES_BY_FAMILLE = {
    "Gobeleterie (verres)": [a for a in ARTICLES if a["famille"] == "Gobeleterie (verres)"],
    "Verre creux (bouteilles / pots)": [a for a in ARTICLES if a["famille"] == "Verre creux (bouteilles / pots)"],
}

MARQUES_DECOR = sorted({a["marque"] for a in ARTICLES if a["marque"]})

# =========================================================
# BASE DES OF CONFIRMÉS (« OF du jour ») — réponse au besoin exprimé par
# l'entreprise : ne pas ressaisir manuellement un OF déjà confirmé côté
# planification, mais le sélectionner dans une base existante (comme le ferait
# une intégration réelle avec l'ERP JD Edwards).
#
# 9 OF sont construits à partir de correspondances réelles et vérifiables entre
# deux sources transmises par l'entreprise (source="reel") :
#   - la fiche de validation avant lancement (Figure 3.4 du rapport, réf.
#     FN-PR-121-05-V.00) : client SACOFRINA SA, article "APO 33 CL VA SACO",
#     ligne L-23 ;
#   - le fichier réel "Copie de Suivi BC.xlsx" (suivi des commandes clients
#     2026, feuilles "Suivi commandes 2026" et "Etats BC reçus 2026 i") qui
#     donne de vrais couples client / référence article, recoupés avec les
#     libellés exacts du catalogue ci-dessus (ex. "AIN SAISS 75 CL" / SOTHERMA,
#     "TROPICANA 1 L VB" / JAD DISTRIBUTION, "BLLE EAU DE ROSE 1L AVIS VV" /
#     FLEUR ATLAS BELAAMRI, "OULMES FRUITE 25 VIS BAGUE EMO" / LES EAUX
#     MINERALES D'OULMES, "BORDELAISE 500 VB ALMA RWS" / ROSLANE WINE & SPIRITS
#     — le suffixe RWS de l'article correspond au vrai client).
# Les autres OF (source="genere") élargissent la base à d'autres lignes/articles
# du catalogue, avec des clients réels de "Copie de Suivi BC.xlsx" réutilisés
# à titre illustratif (le couple client/article n'est alors pas garanti réel).
# =========================================================
import datetime as _dt

_OF_REELS_BASE = [
    # (client, libellé article exact du catalogue, ligne, source_detail)
    ("SACOFRINA SA", "APO 33 CL VA SACO", "L23",
     "Fiche de validation avant lancement (Figure 3.4 du rapport, FN-PR-121-05-V.00)"),
    ("LES EAUX MINERALES D'OULMES", "OULMES FRUITE 25 VIS BAGUE EMO", "L11",
     "Copie de Suivi BC.xlsx — Etats BC reçus 2026"),
    ("ROSLANE WINE & SPIRITS", "BORDELAISE 500 VB ALMA RWS", "L22",
     "Copie de Suivi BC.xlsx — Suivi commandes 2026 (client RWS)"),
    ("FLEUR ATLAS BELAAMRI", "BLLE EAU DE ROSE 1L  AVIS VV", "L12",
     "Copie de Suivi BC.xlsx — Etats BC reçus 2026"),
    ("SOTHERMA", "AIN SAISS 75 CL", "L13",
     "Copie de Suivi BC.xlsx — Etats BC reçus 2026"),
    ("SOTHERMA", "AIN SAISS 50 CL", "L21",
     "Copie de Suivi BC.xlsx — Etats BC reçus 2026"),
    ("SOTHERMA", "AIN SAISS 33 CL", "L31",
     "Copie de Suivi BC.xlsx — Etats BC reçus 2026"),
    ("JAD DISTRIBUTION", "TROPICANA 1 L VB", "L23",
     "Copie de Suivi BC.xlsx — Etats BC reçus 2026"),
    ("SOCIETE DES  CAFES SAHARA", "6V/ CAFE ARABICA FL", "L01",
     "Copie de Suivi BC.xlsx — Suivi commandes 2026"),
]

_CLIENTS_GENERIQUES = [
    "THALVIN", "SOCIETE DES BOISSONS DU MAROC", "EPICES GIRONA SARL", "FYLAR SARL",
    "LES AROMES DU MAROC", "STE UNIDIS SARL", "OKSA",
]

_ARTICLES_INDEX = {a["article"]: a for a in ARTICLES}


def _four_de_ligne(ligne_code):
    return dict(LIGNES)[ligne_code]


def _build_of_confirmes():
    of_list = []
    n = 1000
    aujourdhui = _dt.date(2026, 9, 2)

    def _next_n_of():
        nonlocal n
        n += 1
        return f"OF-2026-{n}"

    # --- 9 OF réels (client + article vérifiés dans les fichiers transmis) ---
    for i, (client, art_label, ligne, detail) in enumerate(_OF_REELS_BASE):
        art = _ARTICLES_INDEX.get(art_label)
        if art is None:
            continue
        four = _four_de_ligne(ligne)
        of_list.append({
            "n_of": _next_n_of(),
            "client": client,
            "article": art["article"],
            "famille": art["famille"],
            "decore": art["decore"],
            "marque": art["marque"],
            "ligne": ligne,
            "four": four,
            "site": FOURS[four]["site"],
            "qte_planifiee": 8000 + (i * 733) % 6000,
            "date": aujourdhui - _dt.timedelta(days=i % 5),
            "source": "reel",
            "source_detail": detail,
        })

    # --- OF supplémentaires (élargissement, source="genere"), en privilégiant
    # Tit Mellil (U2/U3/U4) : ~2/3 des OF générés y sont affectés. ---
    lignes_tit_mellil = [c for c, f in LIGNES if FOURS[f]["site"] == "Tit Mellil"]
    lignes_roches_noires = [c for c, f in LIGNES if FOURS[f]["site"] == "Roches Noires"]
    cycle_lignes = (lignes_tit_mellil * 2 + lignes_roches_noires)

    deja_utilises = {(x["client"], x["article"]) for x in of_list}
    articles_dispo = [a for a in ARTICLES if a["article"] not in {x["article"] for x in of_list}]

    for i, art in enumerate(articles_dispo[:45]):
        ligne = cycle_lignes[i % len(cycle_lignes)]
        four = _four_de_ligne(ligne)
        client = _CLIENTS_GENERIQUES[i % len(_CLIENTS_GENERIQUES)]
        of_list.append({
            "n_of": _next_n_of(),
            "client": client,
            "article": art["article"],
            "famille": art["famille"],
            "decore": art["decore"],
            "marque": art["marque"],
            "ligne": ligne,
            "four": four,
            "site": FOURS[four]["site"],
            "qte_planifiee": 5000 + (i * 517) % 9000,
            "date": aujourdhui - _dt.timedelta(days=i % 5),
            "source": "genere",
            "source_detail": "Élargissement de la base pour la démonstration (article réel, couple client/OF illustratif).",
        })

    return of_list


OF_CONFIRMES = _build_of_confirmes()
