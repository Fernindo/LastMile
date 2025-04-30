import sys
import os
import subprocess
import json
from collections import OrderedDict

import ttkbootstrap as tb
from ttkbootstrap import Style
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import tkinter.ttk as ttk

from excel_processing import update_excel
from filter_panel import create_filter_panel
from notes_panel import create_notes_panel
from gui_functions import (
    is_online,
    get_database_connection,
    sync_postgres_to_sqlite,
    save_basket,
    load_basket,
    show_error,
    apply_filters,
    update_excel_from_basket
)

# ─── Determine project_path & commit_file ─────────────────────────────────
if len(sys.argv) >= 2:
    # Launched by launcher.exe or CLI
    project_path = sys.argv[1]
    commit_file  = sys.argv[2] if len(sys.argv) >= 3 else None
else:
    # Fallback if someone double-clicks gui.py
    tmp = tk.Tk(); tmp.withdraw()
    project_path = filedialog.askdirectory(title="Select project folder")
    tmp.destroy()
    if not project_path:
        sys.exit(1)
    commit_file = None

# ─── Prepare project & JSON directory ──────────────────────────────────────
project_name = os.path.basename(project_path)
json_dir     = os.path.join(project_path, "projects")
os.makedirs(json_dir, exist_ok=True)

# ─── Database setup ─────────────────────────────────────────────────────────
conn, db_type = get_database_connection()
cursor = conn.cursor()
if db_type == "postgres":
    sync_postgres_to_sqlite(conn)

# ─── Themed Window ──────────────────────────────────────────────────────────
style = Style(theme="litera")
root  = style.master
root.title(f"Project: {project_name}")
root.state("zoomed")
root.option_add("*Font", ("Segoe UI", 10))

# ---------------- Global Modification Flag ---------------
basket_modified = False
def mark_modified():
    global basket_modified
    basket_modified = True

# ---------- Update Basket Treeview ----------
def update_basket_table(basket_tree, basket_items):
    basket_tree.delete(*basket_tree.get_children())
    for section, products in basket_items.items():
        sec_id = basket_tree.insert("", "end", text=section, open=True)
        for produkt, d in products.items():
            basket_tree.insert(
                sec_id, "end", text="",
                values=(
                    produkt,
                    d.get("jednotky",""),
                    d.get("dodavatel",""),
                    d.get("odkaz",""),
                    float(d.get("koeficient",0)),
                    float(d.get("nakup_materialu",0)),
                    int(d.get("pocet_materialu",1)),
                    float(d.get("cena_prace",0)),
                    int(d.get("pocet_prace",1))
                )
            )

# ---------- Reorder Basket Data (sections) ----------
def reorder_basket_data():
    new_basket = OrderedDict()
    for sec in basket_tree.get_children(""):
        sec_name = basket_tree.item(sec, "text")
        prods = OrderedDict()
        for child in basket_tree.get_children(sec):
            vals = basket_tree.item(child, "values")
            prods[vals[0]] = {
                "jednotky": vals[1],
                "dodavatel": vals[2],
                "odkaz": vals[3],
                "koeficient": float(vals[4]),
                "nakup_materialu": float(vals[5]),
                "pocet_materialu": int(vals[6]),
                "cena_prace": float(vals[7]),
                "pocet_prace": int(vals[8])
            }
        new_basket[sec_name] = prods
    basket_items.clear()
    basket_items.update(new_basket)

# ---------- Column Resizing ----------
db_column_proportions = {
    "produkt":0.20, "jednotky":0.15, "dodavatel":0.15,
    "odkaz":0.21, "koeficient":0.10, "nakup_materialu":0.089,
    "cena_prace":0.075
}
def adjust_db_columns(event):
    w = event.width
    for col, pct in db_column_proportions.items():
        tree.column(col, width=int(w * pct))

basket_columns = (
    "produkt","jednotky","dodavatel","odkaz","koeficient",
    "nakup materialu","pocet materialu","cena prace","pocet prace"
)
basket_column_widths = {
    "produkt":175,"jednotky":150,"dodavatel":155,"odkaz":320,
    "koeficient":120,"nakup materialu":140,"pocet materialu":140,
    "cena prace":100,"pocet prace":100
}
def adjust_basket_columns(event):
    basket_tree.column("#0", width=170, anchor="w", stretch=False)
    for col in basket_columns:
        basket_tree.column(col, width=basket_column_widths[col], stretch=False)

# ---------- Cell Editing via Dialog ----------
def edit_basket_cell(event):
    row_id = basket_tree.identify_row(event.y)
    col_id = basket_tree.identify_column(event.x)
    if not row_id or basket_tree.parent(row_id)=="":
        return
    col_index = int(col_id.replace("#","")) - 1
    if col_index<4 or col_index>8:
        return

    old = basket_tree.set(row_id, col_id)
    names = [
        "Produkt","Jednotky","Dodávateľ","Odkaz","Koeficient",
        "Nákup materiálu","Počet materiálu","Cena práce","Počet práce"
    ]
    prompt = f"Nová hodnota pre '{names[col_index]}'"
    if col_index in (6,8):
        new = simpledialog.askinteger("Upraviť bunku", prompt,
                                      initialvalue=int(old), parent=root)
    else:
        new = simpledialog.askfloat("Upraviť bunku", prompt,
                                    initialvalue=float(old), parent=root)
    if new is None:
        return

    basket_tree.set(row_id, col_id, new)
    section = basket_tree.parent(row_id)
    prod    = basket_tree.item(row_id)["values"][0]
    key_map = {
        4:"koeficient",5:"nakup_materialu",6:"pocet_materialu",
        7:"cena_prace",8:"pocet_prace"
    }
    basket_items[section][prod][key_map[col_index]] = new
    mark_modified()

# ---------- Add to Basket ----------
def add_to_basket(item):
    produkt = item[0]
    section = item[7] if len(item)>7 else "Uncategorized"
    data = {
        "jednotky": item[1], "dodavatel": item[2], "odkaz": item[3],
        "koeficient": float(item[4]), "nakup_materialu": float(item[5]),
        "cena_prace": float(item[6]), "pocet_materialu":1, "pocet_prace":1
    }
    if section not in basket_items:
        basket_items[section] = OrderedDict()
    if produkt in basket_items[section]:
        basket_items[section][produkt]["pocet_materialu"] += 1
        basket_items[section][produkt]["pocet_prace"]    += 1
    else:
        basket_items[section][produkt] = data
    update_basket_table(basket_tree, basket_items)
    mark_modified()

# ---------- Return Home ----------
def return_home():
    if basket_modified:
        save_basket(json_dir, project_name, basket_items, user_name_entry.get().strip())
    conn.close()
    root.destroy()
    subprocess.Popen([
        sys.executable,
        os.path.join(os.path.dirname(__file__),"project_selector.py")
    ])

# ─── Filter panel setup ────────────────────────────────────────────────────
category_structure = {}
cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
for cid, main_cat, tablename in cursor.fetchall():
    category_structure.setdefault(main_cat, []).append((cid, tablename))

filter_frame, setup_cat_tree, category_vars, table_vars = create_filter_panel(
    root,
    lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
)
filter_frame.config(width=280)
filter_frame.pack(side="left", fill="y", padx=10, pady=10)
setup_cat_tree(category_structure)

# ─── Main content layout ───────────────────────────────────────────────────
main_frame = tb.Frame(root, padding=10)
main_frame.pack(side="left", fill="both", expand=True)

# Top bar
top = tb.Frame(main_frame, padding=5)
top.pack(side="top", fill="x")
tb.Button(top, text="🏠 Home", bootstyle="light", command=return_home).pack(side="left")
tb.Label(top, text="Tvoje meno:").pack(side="left", padx=(10,5))
user_name_entry = tb.Entry(top, width=20)
user_name_entry.pack(side="left")
def on_name_change(*_):
    export_btn.config(state=tb.DISABLED if not user_name_entry.get().strip() else tb.NORMAL)
user_name_entry.bind("<KeyRelease>", on_name_change)

tb.Label(top, text="Vyhľadávanie:").pack(side="left", padx=(20,5))
name_entry = tb.Entry(top, width=30)
name_entry.pack(side="left")
name_entry.bind("<KeyRelease>",
    lambda e: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
)

# Database Treeview
tree_frame = tb.Frame(main_frame)
tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
db_columns = ("produkt","jednotky","dodavatel","odkaz","koeficient","nakup_materialu","cena_prace")
tree = ttk.Treeview(tree_frame, columns=db_columns, show="headings")
for c in db_columns:
    tree.heading(c, text=c.capitalize())
    tree.column(c, anchor="center")
tree.pack(fill="both", expand=True)
tree.bind("<Configure>", adjust_db_columns)
tree.bind("<Double-1>", lambda e: add_to_basket(tree.item(tree.focus())["values"]))

# Basket Treeview
basket_items = OrderedDict()
basket_frame = tb.Frame(main_frame, padding=5)
basket_frame.pack(fill="both", expand=True, padx=10, pady=10)
tb.Label(basket_frame, text="Košík - vybraté položky:").pack(anchor="w")

basket_tree = ttk.Treeview(
    basket_frame,
    columns=basket_columns,
    show="tree headings"
)
basket_tree.heading("#0", text="")
basket_tree.column("#0", width=200, stretch=False)
for c in basket_columns:
    basket_tree.heading(c, text=c.capitalize())
    basket_tree.column(c, anchor="center", stretch=False)
basket_tree.pack(fill="both", expand=True)
basket_tree.bind("<Configure>", adjust_basket_columns)
basket_tree.bind("<Double-1>", edit_basket_cell)

# Drag-drop reordering
_drag = {"item": None}
def _start(evt):
    _drag["item"] = basket_tree.identify_row(evt.y)
def _motion(evt):
    iid = _drag["item"]
    if iid:
        tgt = basket_tree.identify_row(evt.y)
        if tgt and tgt != iid and basket_tree.parent(tgt) == basket_tree.parent(iid):
            basket_tree.move(iid, basket_tree.parent(iid), basket_tree.index(tgt))
def _release(evt):
    _drag["item"] = None

basket_tree.bind("<ButtonPress-1>", _start)
basket_tree.bind("<B1-Motion>", _motion)
basket_tree.bind("<ButtonRelease-1>", _release)

# Notes panel
create_notes_panel(basket_frame, project_name)

# Remove & Export
tb.Button(
    basket_frame, text="Odstrániť", bootstyle="danger-outline",
    command=lambda: (
        __import__("gui_functions").remove_from_basket(
            basket_tree, basket_items, update_basket_table
        ),
        mark_modified()
    )
).pack(pady=3)

export_btn = tb.Button(
    basket_frame, text="Exportovať", bootstyle="success",
    command=lambda: (
        messagebox.showwarning("Meno chýba","Prosím zadaj meno.")
        if not user_name_entry.get().strip()
        else update_excel_from_basket(basket_items, project_name)
    )
)
export_btn.pack(pady=3)
on_name_change()

# Load basket
basket_items_loaded, saved = load_basket(json_dir, project_name, file_path=commit_file)
basket_items.update(basket_items_loaded)
user_name_entry.insert(0, saved)
update_basket_table(basket_tree, basket_items)

# Initial filter
apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

# Handle close
def on_closing():
    if basket_modified:
        save_basket(json_dir, project_name, basket_items, user_name_entry.get().strip())
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
