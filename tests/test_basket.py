import sys
import subprocess
from pathlib import Path

# Build and add application directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "setup.py", "build"], cwd=ROOT_DIR, check=True)
build_lib = next((ROOT_DIR / "build").glob("lib.*"))
sys.path.insert(0, str(build_lib.resolve()))

APP_DIR = ROOT_DIR / "one folder to rule them all" / "Hlavna aplikacia"
sys.path.append(str(APP_DIR))

import fastbasket
from basket import Basket


def make_item():
    return (
        "Produkt",
        "ks",
        "Supplier",
        "link",
        1.2,
        2.0,
        3.0,
        1.5,
        "SectionA",
    )


def test_add_and_recompute():
    b = Basket()
    assert b.add_item(make_item())
    mat, work, total = b.recompute_totals()
    assert mat == 2.0 * 1.2
    assert work == 3.0 * 1.5
    assert total == mat + work


def test_apply_and_revert_coefficients():
    b = Basket()
    b.add_item(make_item())
    b.apply_global_coefficient(2.0)
    info = b.items["SectionA"]["Produkt"]
    assert info.koeficient_material == 2.0
    assert info.koeficient_prace == 2.0
    b.revert_coefficient()
    info = b.items["SectionA"]["Produkt"]
    assert info.koeficient_material == 1.2
    assert info.koeficient_prace == 1.5


def test_undo_engine():
    eng = fastbasket.UndoEngine()
    ch = fastbasket.Change("sec", "prod", "field", "1", "2")
    eng.apply(ch)
    u = eng.undo()
    assert u.old_value == "1"
    r = eng.redo()
    assert r.new_value == "2"
