"""Constantes partagées : lignes/fours réels, palette de couleurs (reprise de
l'identité visuelle utilisée en soutenance), paramètres par défaut."""

LIGNES = ["L11", "L12", "L13", "L21", "L22", "L23"]
FOURS = ["Four 1", "Four 2"]
LIGNE_TO_FOUR = {"L11": "Four 1", "L12": "Four 1", "L13": "Four 1",
                 "L21": "Four 2", "L22": "Four 2", "L23": "Four 2"}
FOUR_TO_LIGNES = {"Four 1": ["L11", "L12", "L13"], "Four 2": ["L21", "L22", "L23"]}

# Palette — identité visuelle reprise du rapport PFA (une seule couleur dominante,
# un accent net, rouge/vert réservés au statut). Assignation fixe, jamais recalculée
# à la volée pour ne pas changer de sens d'une page à l'autre.
COLOR = {
    "anthracite": "#2B333C",
    "anthracite_deep": "#171D23",
    "steel": "#5A6B78",
    "steel_light": "#DCE1E6",
    "steel_pale": "#EEF1F3",
    "amber": "#E3963E",
    "amber_deep": "#C4801F",
    "amber_pale": "#FBEBD3",
    "ink": "#262626",
    "ink_mute": "#6B6B6B",
    "white": "#FFFFFF",
    "green": "#1E6B31",
    "green_pale": "#EAF3EC",
    "red": "#8C2222",
    "red_pale": "#F5E6E6",
}

# Assignation catégorielle fixe (four 1 / four 2), jamais recyclée pour autre chose.
FOUR_COLOR = {"Four 1": COLOR["anthracite"], "Four 2": COLOR["amber_deep"]}
LIGNE_COLOR = {
    "L11": "#2B333C", "L12": "#4A5A68", "L13": "#7C8B97",
    "L21": "#C4801F", "L22": "#E3963E", "L23": "#EFC38B",
}

# Rampe séquentielle (une teinte, clair -> foncé) pour les magnitudes (Pareto, AMDEC).
AMBER_SEQUENTIAL = ["#FBEBD3", "#F3CE9B", "#E3963E", "#C4801F", "#8F5D13"]

SEUIL_ARRET_2024_MIN_PAR_JOUR = 18  # seuil de référence déjà utilisé par SEVAM (fichier Suivi 2025)
