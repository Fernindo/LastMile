from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import OrderedDict
from typing import Dict, Tuple, Optional
import copy

import fastbasket

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
    sync: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)

class Basket:
    """Encapsulates all basket related logic."""

    def __init__(self) -> None:
        self.items: OrderedDict[str, OrderedDict[str, BasketItem]] = OrderedDict()
        self.original: OrderedDict[str, OrderedDict[str, BasketItem]] = OrderedDict()
        self.base_coeffs_material: Dict[Tuple[str, str], float] = {}
        self.base_coeffs_work: Dict[Tuple[str, str], float] = {}
        self._undo = fastbasket.UndoEngine()

    # ------------------------------------------------------------------
    # Basic modifications
    def add_item(self, item: Tuple, section: Optional[str] = None) -> bool:
        produkt, jednotky, dodavatel, odkaz, koef_mat, nakup_mat, cena_prace, koef_pr = item[:8]
        if section is None:
            section = item[8] if len(item) > 8 and item[8] is not None else "Uncategorized"
        # Do not record if nothing changes (duplicate add)
        if section in self.items and produkt in self.items[section]:
            return False
        if section not in self.items:
            self.items[section] = OrderedDict()
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

    # ------------------------------------------------------------------
    # Undo/Redo using fastbasket engine
    def apply_change(self, section: str, produkt: str, field: str, new_value: str) -> None:
        info = self.items.get(section, {}).get(produkt)
        if not info:
            return
        old_val = getattr(info, field)
        self._undo.apply(fastbasket.Change(section, produkt, field, str(old_val), str(new_value)))
        if field in {"pocet_materialu", "pocet_prace"}:
            setattr(info, field, int(new_value))
        elif field in {"koeficient_material", "nakup_materialu", "koeficient_prace", "cena_prace"}:
            setattr(info, field, float(new_value))
        elif field == "sync":
            setattr(info, field, bool(new_value))
        else:
            setattr(info, field, new_value)

    def undo(self) -> bool:
        ch = self._undo.undo()
        if ch is None:
            return False
        info = self.items.get(ch.section, {}).get(ch.product)
        if info:
            field = ch.field
            val = ch.old_value
            if field in {"pocet_materialu", "pocet_prace"}:
                setattr(info, field, int(val))
            elif field in {"koeficient_material", "nakup_materialu", "koeficient_prace", "cena_prace"}:
                setattr(info, field, float(val))
            elif field == "sync":
                setattr(info, field, val.lower() in {"true", "1"})
            else:
                setattr(info, field, val)
        return True

    def redo(self) -> bool:
        ch = self._undo.redo()
        if ch is None:
            return False
        info = self.items.get(ch.section, {}).get(ch.product)
        if info:
            field = ch.field
            val = ch.new_value
            if field in {"pocet_materialu", "pocet_prace"}:
                setattr(info, field, int(val))
            elif field in {"koeficient_material", "nakup_materialu", "koeficient_prace", "cena_prace"}:
                setattr(info, field, float(val))
            elif field == "sync":
                setattr(info, field, val.lower() in {"true", "1"})
            else:
                setattr(info, field, val)
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
            tree.item(sec_id, open=True)
            rows: list[fastbasket.InputRow] = []
            for produkt, d in products.items():
                rows.append(
                    fastbasket.InputRow(
                        produkt,
                        d.jednotky,
                        int(d.pocet_materialu),
                        float(d.koeficient_material),
                        float(d.nakup_materialu),
                        int(d.pocet_prace),
                        float(d.koeficient_prace),
                        float(d.cena_prace),
                        bool(d.sync),
                    )
                )
            formatted, _, _ = fastbasket.compute_rows_and_totals(rows)
            for row in formatted:
                tree.insert(sec_id, "end", text="", values=row)


    def recompute_totals(self) -> Tuple[float, float, float]:
        """Return (material_total, work_total, overall_total)."""
        rows: list[fastbasket.InputRow] = []
        for section, products in self.items.items():
            for produkt, info in products.items():
                rows.append(
                    fastbasket.InputRow(
                        produkt,
                        info.jednotky,
                        int(info.pocet_materialu),
                        float(info.koeficient_material),
                        float(info.nakup_materialu),
                        int(info.pocet_prace),
                        float(info.koeficient_prace),
                        float(info.cena_prace),
                        bool(info.sync),
                    )
                )
        _, total_material, total_work = fastbasket.compute_rows_and_totals(rows)
        return total_material, total_work, total_material + total_work

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
                    sync=(vals[19] == "✓"),
                )
            new_items[sec_name] = prods
        self.items.clear()
        self.items.update(new_items)

    # ------------------------------------------------------------------
    def apply_global_coefficient(self, factor: float) -> None:
        """Apply the same coefficient to material and work for all items."""
        if not self.items:
            return
        for section, products in self.items.items():
            for pname, info in products.items():
                key = (section, pname)
                if key not in self.base_coeffs_material:
                    self.base_coeffs_material[key] = float(info.koeficient_material)
                if key not in self.base_coeffs_work:
                    self.base_coeffs_work[key] = float(info.koeficient_prace)
                info.koeficient_material = factor
                info.koeficient_prace = factor

    def apply_material_coefficient(self, factor: float) -> None:
        """Apply coefficient only to material prices for all items."""
        if not self.items:
            return
        for section, products in self.items.items():
            for pname, info in products.items():
                key = (section, pname)
                if key not in self.base_coeffs_material:
                    self.base_coeffs_material[key] = float(info.koeficient_material)
                info.koeficient_material = factor

    def apply_work_coefficient(self, factor: float) -> None:
        """Apply coefficient only to work prices for all items."""
        if not self.items:
            return
        for section, products in self.items.items():
            for pname, info in products.items():
                key = (section, pname)
                if key not in self.base_coeffs_work:
                    self.base_coeffs_work[key] = float(info.koeficient_prace)
                info.koeficient_prace = factor

    def revert_coefficient(self) -> None:
        """Revert both material and work coefficients to stored originals."""
        for (section, pname), orig in self.base_coeffs_material.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_material = orig
        for (section, pname), orig in self.base_coeffs_work.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_prace = orig
        self.base_coeffs_material.clear()
        self.base_coeffs_work.clear()

    def revert_material_coefficient(self) -> None:
        """Revert only material coefficients to stored originals."""
        for (section, pname), orig in self.base_coeffs_material.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_material = orig
        self.base_coeffs_material.clear()

    def revert_work_coefficient(self) -> None:
        """Revert only work coefficients to stored originals."""
        for (section, pname), orig in self.base_coeffs_work.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_prace = orig
        self.base_coeffs_work.clear()

    def reset_item(self, section: str, produkt: str) -> None:
        orig = self.original.get(section, {}).get(produkt)
        if not orig:
            return
        self.items[section][produkt] = copy.deepcopy(orig)


# ----------------------------------------------------------------------
# Persistence helpers (not currently used)

