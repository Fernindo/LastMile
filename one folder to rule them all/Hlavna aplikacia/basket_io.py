from __future__ import annotations

import os
import glob
import json
from datetime import datetime
from collections import OrderedDict
from typing import Optional

from tkinter import filedialog, messagebox


def save_basket(project_path: str, project_name: str, basket_items, user_name: str = "") -> bool:
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

    out = {"user_name": user_name, "items": []}
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
                "sync_qty": info_dict.get("sync_qty", False),
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
                "sync_qty": bool(p.get("sync_qty", False)),
            }
        basket_items[section] = prods
    return basket_items, data.get("user_name", "")
