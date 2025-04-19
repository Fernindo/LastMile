import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
from collections import OrderedDict
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
import subprocess
from datetime import datetime

# ---------------- Global Modification Flag ---------------
basket_modified = False
def mark_modified():
    global basket_modified
    basket_modified = True

def block_expand_collapse(event):
    return "break"

# ---------- Utility: manually add/remove Treeview tags ----------
def add_treeview_tag(tree, item_id, tag_name):
    existing = list(tree.item(item_id, "tags"))
    if tag_name not in existing:
        existing.append(tag_name)
        tree.item(item_id, tags=existing)

def remove_treeview_tag(tree, item_id, tag_name):
    existing = list(tree.item(item_id, "tags"))
    if tag_name in existing:
        existing.remove(tag_name)
        tree.item(item_id, tags=existing)

# ---------- Update Basket Treeview (with new column order) ----------
def update_basket_table(basket_tree, basket_items):
    basket_tree.delete(*basket_tree.get_children())
    for section, products in basket_items.items():
        sec_id = basket_tree.insert("", "end", text=section, open=True)
        for produkt, d in products.items():
            basket_tree.insert(
                sec_id, "end", text="",
                values=(
                    produkt,
                    d.get("jednotky", ""),
                    d.get("dodavatel", ""),
                    d.get("odkaz", ""),
                    float(d.get("koeficient", 0)),
                    float(d.get("nakup_materialu", 0)),
                    int(d.get("pocet_materialu", 1)),
                    float(d.get("cena_prace", 0)),
                    int(d.get("pocet_prace", 1))
                )
            )

def reorder_basket_data():
    new_basket = OrderedDict()
    for sec in basket_tree.get_children(""):
        sec_name = basket_tree.item(sec, "text")
        prods = OrderedDict()
        for child in basket_tree.get_children(sec):
            vals = basket_tree.item(child, "values")
            prods[vals[0]] = {
                "jednotky":        vals[1],
                "dodavatel":       vals[2],
                "odkaz":           vals[3],
                "koeficient":      float(vals[4]),
                "nakup_materialu": float(vals[5]),
                "pocet_materialu": int(vals[6]),
                "cena_prace":      float(vals[7]),
                "pocet_prace":     int(vals[8])
            }
        new_basket[sec_name] = prods
    basket_items.clear()
    basket_items.update(new_basket)

def reorder_basket_sections():
    reorder_basket_data()

# ---------- Drag-and-Drop with Visual Indicator ----------
dragging_item = {"item": None}
current_drop_target = None

def get_top_level_ancestor(tree, item_id):
    parent = tree.parent(item_id)
    while parent:
        item_id = parent
        parent = tree.parent(item_id)
    return item_id

def on_drag_start(event):
    iid = basket_tree.identify_row(event.y)
    if iid:
        dragging_item["item"] = iid

def on_drag_motion(event):
    global current_drop_target
    if not dragging_item["item"]:
        return
    target = basket_tree.identify_row(event.y)
    if not target or target == dragging_item["item"]:
        if current_drop_target:
            remove_treeview_tag(basket_tree, current_drop_target, "drop_target")
            current_drop_target = None
        return
    dragging_is_section = (basket_tree.parent(dragging_item["item"]) == "")
    if dragging_is_section:
        target = get_top_level_ancestor(basket_tree, target)
    if current_drop_target and current_drop_target != target:
        remove_treeview_tag(basket_tree, current_drop_target, "drop_target")
    current_drop_target = target
    basket_tree.tag_configure("drop_target", background="lightblue",
                              foreground="red", font=('Arial', 10, 'bold'))
    add_treeview_tag(basket_tree, target, "drop_target")
    if dragging_is_section:
        basket_tree.move(dragging_item["item"], "", basket_tree.index(target))
    else:
        parent_drag = basket_tree.parent(dragging_item["item"])
        parent_target = basket_tree.parent(target)
        if parent_drag and parent_drag == parent_target:
            basket_tree.move(dragging_item["item"], parent_drag, basket_tree.index(target))

def on_drag_release(event):
    global current_drop_target
    if dragging_item["item"]:
        if basket_tree.parent(dragging_item["item"]) == "":
            reorder_basket_sections()
        else:
            reorder_basket_data()
        mark_modified()
    if current_drop_target:
        remove_treeview_tag(basket_tree, current_drop_target, "drop_target")
        current_drop_target = None
    dragging_item["item"] = None

# ---------- Dynamic Column Resizing Using Fixed Widths ----------
db_column_proportions = {
    "produkt": 0.20,
    "jednotky": 0.15,
    "dodavatel": 0.15,
    "odkaz": 0.25,
    "koeficient": 0.10,
    "nakup materialu": 0.075,
    "cena prace": 0.075
}
def adjust_db_columns(event):
    total = event.width
    for col, pct in db_column_proportions.items():
        tree.column(col, width=int(total * pct))

basket_column_widths = {
    "produkt": 200,
    "jednotky": 150,
    "dodavatel": 155,
    "odkaz": 350,
    "koeficient": 120,
    "nakup materialu": 140,
    "pocet materialu": 100,
    "cena prace": 100,
    "pocet prace": 100
}
def adjust_basket_columns(event):
    basket_tree.column("#0", width=200, anchor="w", stretch=False)
    for col in basket_columns:
        basket_tree.column(col, width=basket_column_widths[col], stretch=False)

# ---------- Let the user edit columns by double-click ----------
def edit_basket_cell(event):
    region = basket_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    iid = basket_tree.focus()
    if not iid or basket_tree.get_children(iid):
        return
    vals = basket_tree.item(iid)["values"]
    if not vals:
        return
    col = int(basket_tree.identify_column(event.x).replace('#','')) - 1
    if col < 4 or col > 8:
        return
    x, y, w, h = basket_tree.bbox(iid, f"#{col+1}")
    entry = tk.Entry(basket_tree)
    entry.place(x=x, y=y, width=w, height=h)
    entry.insert(0, vals[col])
    entry.focus()
    def save_edit(e):
        try:
            new = float(entry.get()) if col in (4,5,7) else int(entry.get())
        except ValueError:
            entry.destroy()
            return
        key_map = {
            4: "koeficient",
            5: "nakup_materialu",
            6: "pocet_materialu",
            7: "cena_prace",
            8: "pocet_prace"
        }
        section = basket_tree.parent(iid)
        prod = vals[0]
        basket_items[section][prod][key_map[col]] = new
        update_basket_table(basket_tree, basket_items)
        mark_modified()
        entry.destroy()
    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", save_edit)

# ---------- Adding items to basket ----------
def add_to_basket(item, basket_items, update_basket_table, basket_tree):
    produkt = item[0]
    section = item[7] if len(item) > 7 else "Uncategorized"
    data = {
        "jednotky": item[1],
        "dodavatel": item[2],
        "odkaz": item[3],
        "koeficient": float(item[4]),
        "nakup_materialu": float(item[5]),
        "cena_prace": float(item[6]),
        "pocet_materialu": 1,
        "pocet_prace": 1
    }
    if section not in basket_items:
        basket_items[section] = OrderedDict()
    if produkt in basket_items[section]:
        basket_items[section][produkt]["pocet_materialu"] += 1
        basket_items[section][produkt]["pocet_prace"] += 1
    else:
        basket_items[section][produkt] = data
    update_basket_table(basket_tree, basket_items)
    mark_modified()

# ---------- Start of the GUI ----------
if len(sys.argv) < 2:
    tmp = tk.Tk(); tmp.withdraw()
    project_path = filedialog.askdirectory(title="Select a Project Folder")
    tmp.destroy()
    if not project_path:
        print("❌ No project folder provided.")
        sys.exit(1)
else:
    project_path = sys.argv[1]

project_name = os.path.basename(project_path)
commit_file = sys.argv[2] if len(sys.argv) > 2 else None

conn, db_type = get_database_connection()
cursor = conn.cursor()
if db_type == 'postgres':
    sync_postgres_to_sqlite(conn)

root = tk.Tk()
root.state('zoomed')
root.title(f"Project: {project_name}")

def return_home():
    if basket_modified:
        save_basket(project_path, project_name, basket_items, user_name_entry.get().strip())
    conn.close()
    root.destroy()
    subprocess.Popen(["python", "project_selector.py"])

# Filter panel
category_structure = {}
cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
for cid, main_cat, tab in cursor.fetchall():
    category_structure.setdefault(main_cat, []).append((cid, tab))

filter_frame, setup_category_tree, category_vars, table_vars = create_filter_panel(
    root,
    lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
)
filter_frame.config(width=280)
filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5,0), pady=5)
setup_category_tree(category_structure)

# Main layout
main_frame = tk.Frame(root)
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Top bar
top_frame = tk.Frame(main_frame)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

tk.Button(top_frame, text="🏠 Home", command=return_home).pack(side=tk.LEFT)
tk.Label(top_frame, text="Tvoje meno:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(10,5))
user_name_entry = tk.Entry(top_frame, width=20)
user_name_entry.pack(side=tk.LEFT)

def on_name_change(*args):
    export_button.config(state=tk.NORMAL if user_name_entry.get().strip() else tk.DISABLED)
user_name_entry.bind("<KeyRelease>", on_name_change)

tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(20,5))
name_entry = tk.Entry(top_frame, width=30)
name_entry.pack(side=tk.LEFT)
name_entry.bind("<KeyRelease>",
    lambda e: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
)

# Database Treeview
tree_frame = tk.Frame(main_frame)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

db_columns = ("produkt", "jednotky", "dodavatel", "odkaz",
              "koeficient", "nakup materialu", "cena prace")
tree = ttk.Treeview(tree_frame, columns=db_columns, show="headings")
for c in db_columns:
    tree.heading(c, text=c.capitalize())
    tree.column(c, anchor="center")
tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<Configure>", adjust_db_columns)
tree.bind("<Double-1>",
    lambda e: add_to_basket(tree.item(tree.focus())["values"],
                            basket_items, update_basket_table, basket_tree)
)

# Basket Treeview
basket_items = OrderedDict()
basket_frame = tk.Frame(main_frame)
basket_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10)).pack(anchor="w")

basket_columns = (
    "produkt", "jednotky", "dodavatel", "odkaz", "koeficient",
    "nakup materialu", "pocet materialu", "cena prace", "pocet prace"
)
basket_tree = ttk.Treeview(basket_frame, columns=basket_columns, show="tree headings")
basket_tree.heading("#0", text="")
basket_tree.column("#0", width=200, stretch=False)
for c in basket_columns:
    basket_tree.heading(c, text=c.capitalize())
    basket_tree.column(c, anchor="center", stretch=False)
basket_tree.pack(fill=tk.BOTH, expand=True)
basket_tree.bind("<Configure>", adjust_basket_columns)
basket_tree.bind("<Double-1>", edit_basket_cell)

create_notes_panel(basket_frame, project_name)

tk.Button(basket_frame, text="Odstrániť",
          command=lambda: ( __import__('gui_functions').remove_from_basket(basket_tree, basket_items, update_basket_table),
                            mark_modified() )
         ).pack(pady=3)

export_button = tk.Button(basket_frame, text="Exportovať",
    command=lambda: (
        messagebox.showwarning("Meno chýba", "⚠ Prosím zadaj svoje meno pred exportom.")
        if not user_name_entry.get().strip()
        else update_excel_from_basket(basket_items, project_name)
    )
)
export_button.pack(pady=3)
on_name_change()

tk.Button(basket_frame, text="Zálohovať",
          command=lambda: ( save_basket(project_path, project_name, basket_items, user_name_entry.get().strip()),
                            mark_modified(),
                            messagebox.showinfo("Záloha", "Záloha bola vytvorená (nový basket_*.json).") )
         ).pack(pady=3)

# Drag & drop bindings
basket_tree.bind("<ButtonPress-1>", on_drag_start)
basket_tree.bind("<B1-Motion>", on_drag_motion)
basket_tree.bind("<ButtonRelease-1>", on_drag_release)

# ----- Load previous basket & refill missing cena_prace -----
basket_items_loaded, saved_user_name = load_basket(project_path, project_name, file_path=commit_file)
for section, prods in basket_items_loaded.items():
    for prod, data in prods.items():
        data.setdefault("pocet_materialu", 1)
        data.setdefault("pocet_prace", 1)
        if float(data.get("cena_prace", 0)) == 0:
            if db_type == 'postgres':
                cursor.execute(
                    "SELECT cena_prace FROM produkty WHERE produkt = %s",
                    (prod,)
                )
            else:
                cursor.execute(
                    "SELECT cena_prace FROM produkty WHERE produkt = ?",
                    (prod,)
                )
            r = cursor.fetchone()
            if r:
                data["cena_prace"] = float(r[0])

basket_items.update(basket_items_loaded)
user_name_entry.insert(0, saved_user_name)

update_basket_table(basket_tree, basket_items)
apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

def on_closing():
    if basket_modified:
        save_basket(project_path, project_name, basket_items, user_name_entry.get().strip())
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
