from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import OrderedDict
from typing import Dict, Tuple, Optional
import copy

@dataclass
class BasketItem:
    jednotky: str
    dodavatel: str
    odkaz: str
    koeficient_material: float
    nakup_materialu: float
    cena_prace: float
    koeficient_prace: float
    pocet_materialu: int = 1
    pocet_prace: int = 1
    sync_qty: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

class Basket:
    """Encapsulates all basket related logic."""

    def __init__(self) -> None:
        self.items: OrderedDict[str, OrderedDict[str, BasketItem]] = OrderedDict()
        self.original: OrderedDict[str, OrderedDict[str, BasketItem]] = OrderedDict()
        self.base_coeffs: Dict[Tuple[str, str], Tuple[float, float]] = {}

    # ------------------------------------------------------------------
    # Basic modifications
    def add_item(self, item: Tuple, section: Optional[str] = None) -> bool:
        produkt, jednotky, dodavatel, odkaz, koef_mat, nakup_mat, cena_prace, koef_pr = item[:8]
        if section is None:
            section = item[8] if len(item) > 8 and item[8] is not None else "Uncategorized"
        if section not in self.items:
            self.items[section] = OrderedDict()
        if produkt in self.items[section]:
            return False
        info = BasketItem(
            jednotky=jednotky,
            dodavatel=dodavatel,
            odkaz=odkaz,
            koeficient_material=float(koef_mat),
            nakup_materialu=float(nakup_mat),
            cena_prace=float(cena_prace),
            koeficient_prace=float(koef_pr),
        )
        self.items[section][produkt] = info
        self.original.setdefault(section, OrderedDict())[produkt] = copy.deepcopy(info)
        return True

    def remove(self, section: str, produkt: str) -> None:
        if section in self.items and produkt in self.items[section]:
            del self.items[section][produkt]
            if not self.items[section]:
                del self.items[section]

    def remove_selection(self, tree) -> None:
        for iid in tree.selection():
            parent = tree.parent(iid)
            if parent == "":
                sec_name = tree.item(iid, "text")
                self.items.pop(sec_name, None)
            else:
                prod_name = tree.item(iid, "values")[0]
                sec_name = tree.item(parent, "text")
                self.remove(sec_name, prod_name)

    def update_tree(self, tree) -> None:
        """Refresh all rows of the provided tree widget."""
        tree.delete(*tree.get_children())

        for section, products in self.items.items():
            sec_id = tree.insert("", "end", text=section)
            # Expand sections by default so all products are visible
            tree.item(sec_id, open=True)
            for produkt, d in products.items():
                poc_mat = int(d.pocet_materialu)
                poc_pr = int(d.pocet_prace)
                koef_mat = float(d.koeficient_material)
                nakup_mat = float(d.nakup_materialu)
                predaj_mat_jedn = nakup_mat * koef_mat
                predaj_mat_spolu = predaj_mat_jedn * poc_mat
                koef_pr = float(d.koeficient_prace)
                cena_pr = float(d.cena_prace)
                predaj_praca_jedn = cena_pr * koef_pr
                predaj_praca_spolu = predaj_praca_jedn * poc_pr
                predaj_spolu = predaj_mat_spolu + predaj_praca_spolu
                nakup_mat_spolu = nakup_mat * poc_mat
                zisk_mat = predaj_mat_spolu - nakup_mat_spolu
                marza_mat = (zisk_mat / predaj_mat_spolu * 100) if predaj_mat_spolu else 0
                nakup_praca_spolu = cena_pr * poc_pr
                zisk_pr = predaj_praca_spolu - nakup_praca_spolu
                marza_pr = (zisk_pr / predaj_praca_spolu * 100) if predaj_praca_spolu else 0
                sync = "\u2713" if d.sync_qty else ""
                tree.insert(
                    sec_id,
                    "end",
                    text="",
                    values=(
                        produkt,
                        d.jednotky,
                        poc_mat,
                        koef_mat,
                        nakup_mat,
                        predaj_mat_jedn,
                        nakup_mat_spolu,
                        predaj_mat_spolu,
                        zisk_mat,
                        marza_mat,
                        poc_pr,
                        koef_pr,
                        cena_pr,
                        nakup_praca_spolu,
                        predaj_praca_jedn,
                        predaj_praca_spolu,
                        zisk_pr,
                        marza_pr,
                        predaj_spolu,
                        sync,
                    ),
                )


    def recompute_total(self) -> float:
        total = 0.0
        for section, products in self.items.items():
            for _, info in products.items():
                koef_mat = float(info.koeficient_material)
                nakup_mat = float(info.nakup_materialu)
                poc_mat = int(info.pocet_materialu)
                predaj_mat = nakup_mat * koef_mat * poc_mat
                koef_pr = float(info.koeficient_prace)
                cena_pr = float(info.cena_prace)
                poc_pr = int(info.pocet_prace)
                predaj_pr = cena_pr * koef_pr * poc_pr
                total += predaj_mat + predaj_pr
        return total

    def reorder_from_tree(self, tree) -> None:
        new_items: OrderedDict[str, OrderedDict[str, BasketItem]] = OrderedDict()
        for sec in tree.get_children(""):
            sec_name = tree.item(sec, "text")
            prods: OrderedDict[str, BasketItem] = OrderedDict()
            for child in tree.get_children(sec):
                vals = tree.item(child, "values")
                prods[vals[0]] = BasketItem(
                    jednotky=vals[1],
                    koeficient_material=float(vals[3]),
                    nakup_materialu=float(vals[4]),
                    koeficient_prace=float(vals[11]),
                    cena_prace=float(vals[12]),
                    pocet_materialu=int(float(vals[2])),
                    pocet_prace=int(float(vals[10])),
                    dodavatel="",
                    odkaz="",
                    sync_qty=(vals[19] == "✓"),
                )
            new_items[sec_name] = prods
        self.items.clear()
        self.items.update(new_items)

    # ------------------------------------------------------------------
    def apply_global_coefficient(self, factor: float) -> None:
        if not self.items:
            return
        for section, products in self.items.items():
            for pname, info in products.items():
                key = (section, pname)
                if key not in self.base_coeffs:
                    self.base_coeffs[key] = (
                        float(info.koeficient_material),
                        float(info.koeficient_prace),
                    )
                info.koeficient_material = factor
                info.koeficient_prace = factor

    def revert_coefficient(self) -> None:
        for (section, pname), (orig_mat, orig_pr) in self.base_coeffs.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_material = orig_mat
                self.items[section][pname].koeficient_prace = orig_pr
        self.base_coeffs.clear()

    def reset_item(self, section: str, produkt: str) -> None:
        orig = self.original.get(section, {}).get(produkt)
        if not orig:
            return
        self.items[section][produkt] = copy.deepcopy(orig)


# ----------------------------------------------------------------------
# Persistence helpers
from basket_io import save_basket, load_basket

