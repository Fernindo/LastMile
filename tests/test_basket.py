import sys
from pathlib import Path

# Add application directory to path
ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / 'one folder to rule them all' / 'Hlavna aplikacia'
sys.path.append(str(APP_DIR))

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
