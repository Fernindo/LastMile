from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import OrderedDict
from typing import Dict, Tuple, Optional
import copy
import os
import glob
import json
from datetime import datetime

from tkinter import filedialog, messagebox

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
        self._undo_stack: list[
            tuple[
                OrderedDict[str, OrderedDict[str, BasketItem]],
                Dict[Tuple[str, str], float],
                Dict[Tuple[str, str], float],
            ]
        ] = []
        self._redo_stack: list[
            tuple[
                OrderedDict[str, OrderedDict[str, BasketItem]],
                Dict[Tuple[str, str], float],
                Dict[Tuple[str, str], float],
            ]
        ] = []

    # ------------------------------------------------------------------
    # Undo/Redo helpers
    def snapshot(self) -> None:
        self._undo_stack.append(
            (
                copy.deepcopy(self.items),
                copy.deepcopy(self.base_coeffs_material),
                copy.deepcopy(self.base_coeffs_work),
            )
        )
        self._redo_stack.clear()

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(
            (
                copy.deepcopy(self.items),
                copy.deepcopy(self.base_coeffs_material),
                copy.deepcopy(self.base_coeffs_work),
            )
        )
        self.items, self.base_coeffs_material, self.base_coeffs_work = self._undo_stack.pop()
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(
            (
                copy.deepcopy(self.items),
                copy.deepcopy(self.base_coeffs_material),
                copy.deepcopy(self.base_coeffs_work),
            )
        )
        self.items, self.base_coeffs_material, self.base_coeffs_work = self._redo_stack.pop()
        return True

    # ------------------------------------------------------------------
    # Basic modifications
    def add_item(self, item: Tuple, section: Optional[str] = None) -> bool:
        produkt, jednotky, dodavatel, odkaz, koef_mat, nakup_mat, cena_prace, koef_pr = item[:8]
        if section is None:
            section = item[8] if len(item) > 8 and item[8] is not None else "Uncategorized"
        # Do not snapshot if nothing changes (duplicate add)
        if section in self.items and produkt in self.items[section]:
            return False
        # We are about to mutate state; snapshot first
        self.snapshot()
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

    def remove(self, section: str, produkt: str) -> None:
        if section in self.items and produkt in self.items[section]:
            self.snapshot()
            del self.items[section][produkt]
            if not self.items[section]:
                del self.items[section]

    def remove_selection(self, tree) -> None:
        self.snapshot()
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
                sync = "\u2713" if d.sync else ""
                tree.insert(
                    sec_id,
                    "end",
                    text="",
                    values=(
                        produkt,
                        d.jednotky,
                        poc_mat,
                        f"{koef_mat:.2f}",
                        f"{nakup_mat:.2f}",
                        f"{predaj_mat_jedn:.2f}",
                        f"{nakup_mat_spolu:.2f}",
                        f"{predaj_mat_spolu:.2f}",
                        f"{zisk_mat:.2f}",
                        f"{marza_mat:.2f}",
                        poc_pr,
                        f"{koef_pr:.2f}",
                        f"{cena_pr:.2f}",
                        f"{nakup_praca_spolu:.2f}",
                        f"{predaj_praca_jedn:.2f}",
                        f"{predaj_praca_spolu:.2f}",
                        f"{zisk_pr:.2f}",
                        f"{marza_pr:.2f}",
                        f"{predaj_spolu:.2f}",
                        sync,
                    ),
                )


    def recompute_totals(self) -> Tuple[float, float, float]:
        """Return (material_total, work_total, overall_total)."""
        total_material = 0.0
        total_work = 0.0
        for section, products in self.items.items():
            for _, info in products.items():
                koef_mat = float(info.koeficient_material)
                nakup_mat = float(info.nakup_materialu)
                poc_mat = int(info.pocet_materialu)
                total_material += nakup_mat * koef_mat * poc_mat

                koef_pr = float(info.koeficient_prace)
                cena_pr = float(info.cena_prace)
                poc_pr = int(info.pocet_prace)
                total_work += cena_pr * koef_pr * poc_pr

        return total_material, total_work, total_material + total_work

    def reorder_from_tree(self, tree) -> None:
        self.snapshot()
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
        self.snapshot()
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
        self.snapshot()
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
        self.snapshot()
        for section, products in self.items.items():
            for pname, info in products.items():
                key = (section, pname)
                if key not in self.base_coeffs_work:
                    self.base_coeffs_work[key] = float(info.koeficient_prace)
                info.koeficient_prace = factor

    def revert_coefficient(self) -> None:
        """Revert both material and work coefficients to stored originals."""
        self.snapshot()
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
        self.snapshot()
        for (section, pname), orig in self.base_coeffs_material.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_material = orig
        self.base_coeffs_material.clear()

    def revert_work_coefficient(self) -> None:
        """Revert only work coefficients to stored originals."""
        self.snapshot()
        for (section, pname), orig in self.base_coeffs_work.items():
            if section in self.items and pname in self.items[section]:
                self.items[section][pname].koeficient_prace = orig
        self.base_coeffs_work.clear()

    def reset_item(self, section: str, produkt: str) -> None:
        orig = self.original.get(section, {}).get(produkt)
        if not orig:
            return
        self.snapshot()
        self.items[section][produkt] = copy.deepcopy(orig)


# ----------------------------------------------------------------------
# Persistence helpers (migrated from basket_io.py)

def save_basket(
    project_path: str,
    project_name: str,
    basket_items,
    user_name: str = "",
    notes: list | None = None,
) -> bool:
    os.makedirs(project_path, exist_ok=True)
    default_name = f"basket_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"
    file_path = filedialog.asksaveasfilename(
        title="Uložiť košík ako…",
        initialdir=project_path,
        initialfile=default_name,
        defaultextension=".json",
        filetypes=[("JSON súbory", "*.json")],
    )
    if not file_path:
        return False

    notes_list = notes if notes is not None else []

    out = {"user_name": user_name, "items": [], "notes": notes_list}
    for section, prods in basket_items.items():
        sec_obj = {"section": section, "products": []}
        for pname, info in prods.items():
            if hasattr(info, "to_dict"):
                info_dict = info.to_dict()
            else:
                info_dict = info
            sec_obj["products"].append({
                "produkt": pname,
                "jednotky": info_dict.get("jednotky", ""),
                "dodavatel": info_dict.get("dodavatel", ""),
                "odkaz": info_dict.get("odkaz", ""),
                "koeficient_material": info_dict.get("koeficient_material", 0),
                "koeficient_prace": info_dict.get("koeficient_prace", 1),
                "nakup_materialu": info_dict.get("nakup_materialu", 0),
                "cena_prace": info_dict.get("cena_prace", 0),
                "pocet_prace": info_dict.get("pocet_prace", 1),
                "pocet_materialu": info_dict.get("pocet_materialu", 1),
                "sync": info_dict.get("sync", False),
            })
        out["items"].append(sec_obj)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Chyba pri ukladaní", f"Nepodarilo sa uložiť súbor:\n{e}")
        return False


def load_basket(project_path: str, project_name: str, file_path: Optional[str] = None):
    if file_path and os.path.isfile(file_path):
        path = file_path
    else:
        candidates = glob.glob(os.path.join(project_path, "basket_*.json"))
        if not candidates:
            return OrderedDict(), ""
        path = max(candidates, key=os.path.getmtime)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return OrderedDict(), ""

    notes_list = data.get("notes", [])

    basket_items = OrderedDict()
    for sec in data.get("items", []):
        section = sec.get("section", "")
        prods = OrderedDict()
        for p in sec.get("products", []):
            pname = p.get("produkt")
            if not pname:
                continue
            prods[pname] = {
                "jednotky": p.get("jednotky", ""),
                "dodavatel": p.get("dodavatel", ""),
                "odkaz": p.get("odkaz", ""),
                "koeficient_material": float(p.get("koeficient_material", 0)),
                "koeficient_prace": float(p.get("koeficient_prace", 1)),
                "nakup_materialu": float(p.get("nakup_materialu", 0)),
                "cena_prace": float(p.get("cena_prace", 0)),
                "pocet_prace": int(p.get("pocet_prace", 1)),
                "pocet_materialu": int(p.get("pocet_materialu", 1)),
                "sync": bool(p.get("sync", p.get("sync_qty", False))),
            }
        basket_items[section] = prods
    return basket_items, data.get("user_name", ""), notes_list

