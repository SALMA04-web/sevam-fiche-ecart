"""Smoke-test end-to-end : charge chaque page de l'application via Streamlit AppTest
et vérifie qu'aucune exception n'est levée au chargement. Lancer avec :
    python3 tests/smoke_app.py
(depuis la racine du projet, pour que les chemins relatifs de common.py fonctionnent)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = [
    "app.py",
    "pages/1_Nouvelle_declaration.py",
    "pages/2_Historique.py",
    "pages/3_Suivi_quotidien_2025.py",
    "pages/4_Pareto.py",
    "pages/5_Fiabilite.py",
    "pages/6_AMDEC.py",
    "pages/7_Impact_economique.py",
    "pages/8_Qualite_des_donnees.py",
]

failed = []
for page in PAGES:
    path = str(ROOT / page)
    at = AppTest.from_file(path, default_timeout=60)
    at.run()
    if at.exception:
        failed.append(page)
        print(f"ECHEC  {page}")
        for exc in at.exception:
            print(f"   {exc.value!r}")
            print(f"   {exc.stack_trace}")
    else:
        n_widgets = len(at.button) + len(at.selectbox) + len(at.slider) + len(at.dataframe)
        print(f"OK     {page}  ({n_widgets} widgets/éléments rendus)")

print()
if failed:
    print(f"{len(failed)}/{len(PAGES)} page(s) en échec : {failed}")
    sys.exit(1)
else:
    print(f"{len(PAGES)}/{len(PAGES)} pages chargées sans exception.")
