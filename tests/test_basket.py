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


def test_duplicate_add_does_not_affect_undo():
    b = Basket()
    item = make_item()
    assert b.add_item(item)
    assert not b.add_item(item)
    b.undo()
    assert not b.items


class FakeTree:
    def __init__(self):
        self.nodes = {"": []}
        self.data = {}
        self._counter = 0

    def insert(self, parent, index, text="", values=()):
        iid = f"I{self._counter}"
        self._counter += 1
        self.nodes.setdefault(parent, []).append(iid)
        self.nodes[iid] = []
        self.data[iid] = {"text": text, "values": values, "parent": parent, "open": False}
        return iid

    def get_children(self, item=""):
        return list(self.nodes.get(item, []))

    def item(self, iid, option=None, **kw):
        if kw:
            self.data[iid].update(kw)
        if option:
            return self.data[iid].get(option, "")
        return self.data[iid]

    def parent(self, iid):
        return self.data[iid]["parent"]

    def delete(self, *iids):
        for iid in iids:
            parent = self.data[iid]["parent"]
            self.nodes[parent].remove(iid)
            self._delete_recursive(iid)

    def _delete_recursive(self, iid):
        for child in list(self.nodes[iid]):
            self._delete_recursive(child)
        del self.nodes[iid]
        del self.data[iid]


def test_reorder_preserves_vendor_and_link():
    b = Basket()
    item1 = ("Prod1", "ks", "Vendor1", "link1", 1.0, 2.0, 3.0, 1.0, "Sec")
    item2 = ("Prod2", "ks", "Vendor2", "link2", 1.0, 2.0, 3.0, 1.0, "Sec")
    b.add_item(item1)
    b.add_item(item2)

    tree = FakeTree()
    b.update_tree(tree)
    sec_id = tree.get_children("")[0]
    children = tree.get_children(sec_id)
    tree.nodes[sec_id] = list(reversed(children))

    b.reorder_from_tree(tree)
    assert list(b.items["Sec"].keys()) == ["Prod2", "Prod1"]
    assert b.items["Sec"]["Prod1"].dodavatel == "Vendor1"
    assert b.items["Sec"]["Prod1"].odkaz == "link1"
    assert b.items["Sec"]["Prod2"].dodavatel == "Vendor2"
    assert b.items["Sec"]["Prod2"].odkaz == "link2"
