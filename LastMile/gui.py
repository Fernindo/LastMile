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
import json
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
    existing_tags = list(tree.item(item_id, "tags"))
    if tag_name not in existing_tags:
        existing_tags.append(tag_name)
        tree.item(item_id, tags=existing_tags)

def remove_treeview_tag(tree, item_id, tag_name):
    existing_tags = list(tree.item(item_id, "tags"))
    if tag_name in existing_tags:
        existing_tags.remove(tag_name)
        tree.item(item_id, tags=existing_tags)

# ---------- Update Basket Treeview (with new columns) ----------
def update_basket_table(basket_tree, basket_items):
    """
    Rebuilds the basket_tree from basket_items.
    Each top-level key is treated as a section (in #0),
    each product is a child row with columns:
        0: produkt
        1: jednotky
        2: dodavatel
        3: odkaz
        4: koeficient
        5: nakup_materialu
        6: cena_prace
        7: pocet_materialu
        8: pocet_prace
    """
    basket_tree.delete(*basket_tree.get_children())
    for section, products in basket_items.items():
        section_id = basket_tree.insert("", "end", text=section, open=True)
        for produkt, item_data in products.items():
            basket_tree.insert(
                section_id, "end", text="",
                values=(
                    produkt,
                    item_data.get("jednotky", ""),
                    item_data.get("dodavatel", ""),
                    item_data.get("odkaz", ""),
                    float(item_data.get("koeficient", 0)),        # default 0 if missing
                    float(item_data.get("nakup_materialu", 0)),   # default 0 if missing
                    float(item_data.get("cena_prace", 0)),        # default 0 if missing
                    int(item_data.get("pocet_materialu", 1)),     # default 1 if missing
                    int(item_data.get("pocet_prace", 1))          # default 1 if missing
                )
            )

def reorder_basket_data():
    """
    Rebuilds basket_items from the new columns in the basket_tree.
    """
    new_basket = OrderedDict()
    for section_id in basket_tree.get_children(""):
        section_name = basket_tree.item(section_id, "text")
        product_dict = OrderedDict()
        for child_id in basket_tree.get_children(section_id):
            vals = basket_tree.item(child_id, "values")
            produkt = vals[0]
            product_dict[produkt] = {
                "jednotky":        vals[1],
                "dodavatel":       vals[2],
                "odkaz":           vals[3],
                "koeficient":      float(vals[4]),
                "nakup_materialu": float(vals[5]),
                "cena_prace":      float(vals[6]),
                "pocet_materialu": int(vals[7]),
                "pocet_prace":     int(vals[8])
            }
        new_basket[section_name] = product_dict
    basket_items.clear()
    basket_items.update(new_basket)

def reorder_basket_sections():
    reorder_basket_data()

# ---------- Drag-and-Drop with Visual Indicator ----------
dragging_item = {"item": None}
current_drop_target = None  # holds the current drop target

def get_top_level_ancestor(tree, item_id):
    """Return the top-level ancestor if item_id is child, or itself if top-level."""
    parent = tree.parent(item_id)
    while parent:
        item_id = parent
        parent = tree.parent(item_id)
    return item_id

def on_drag_start(event):
    iid = basket_tree.identify_row(event.y)
    if not iid:
        return
    dragging_item["item"] = iid

def on_drag_motion(event):
    global current_drop_target
    if not dragging_item["item"]:
        return

    target_iid = basket_tree.identify_row(event.y)
    if not target_iid or target_iid == dragging_item["item"]:
        if current_drop_target:
            remove_treeview_tag(basket_tree, current_drop_target, "drop_target")
            current_drop_target = None
        return

    dragging_is_section = (basket_tree.parent(dragging_item["item"]) == "")
    if dragging_is_section:
        target_iid = get_top_level_ancestor(basket_tree, target_iid)

    if current_drop_target and current_drop_target != target_iid:
        remove_treeview_tag(basket_tree, current_drop_target, "drop_target")
    current_drop_target = target_iid

    basket_tree.tag_configure("drop_target", background="lightblue",
                              foreground="red", font=('Arial', 10, 'bold'))
    add_treeview_tag(basket_tree, current_drop_target, "drop_target")

    if dragging_is_section:
        basket_tree.move(dragging_item["item"], "", basket_tree.index(target_iid))
    else:
        parent_drag = basket_tree.parent(dragging_item["item"])
        parent_target = basket_tree.parent(target_iid)
        if parent_drag and parent_drag == parent_target:
            basket_tree.move(dragging_item["item"], parent_drag, basket_tree.index(target_iid))

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

# ---------- Dynamic Column Resizing Using Percentages ----------
# DB Items Treeview
db_column_proportions = {
    "produkt": 0.20,
    "jednotky": 0.10,
    "dodavatel": 0.20,
    "odkaz": 0.25,
    "koeficient": 0.10,
    "nakup_materialu": 0.075,
    "cena_prace": 0.075
}
def adjust_db_columns(event):
    total_width = event.width
    for col, perc in db_column_proportions.items():
        tree.column(col, width=int(total_width * perc))

# Basket Treeview
basket_column_proportions = {
    "produkt": 0.10,
    "jednotky": 0.08,
    "dodavatel": 0.10,
    "odkaz": 0.15,
    "koeficient": 0.10,
    "nakup_materialu": 0.10,
    "cena_prace": 0.08,
    "pocet_materialu": 0.07,
    "pocet_prace": 0.07
}
def adjust_basket_columns(event):
    total_width = event.width
    basket_tree.column("#0", width=int(total_width * 0.25))
    for col in basket_columns:
        perc = basket_column_proportions.get(col, 0.10)
        basket_tree.column(col, width=int(total_width * perc))

# ---------- Let the user edit Koeficient..Pocet_prace by double-click ----------
def edit_basket_cell(event):
    """
    By double-clicking a cell in columns 4..8, user can edit them:
    4: Koeficient (float)
    5: Nakup_materialu (float)
    6: Cena_prace (float)
    7: Pocet_materialu (int)
    8: Pocet_prace (int)
    """
    region = basket_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    selected_item = basket_tree.focus()
    if not selected_item:
        return
    # If this is a parent (section), skip
    if basket_tree.get_children(selected_item):
        return

    item_vals = basket_tree.item(selected_item)["values"]
    if not item_vals:
        return

    col_str = basket_tree.identify_column(event.x)  # e.g. '#4'
    col_index = int(col_str.replace('#','')) - 1     # 0-based

    # We allow editing columns 4..8
    if col_index < 4 or col_index > 8:
        return

    # Convert the bounding box to place an Entry
    x, y, width, height = basket_tree.bbox(selected_item, col_str)
    entry_popup = tk.Entry(basket_tree)
    entry_popup.place(x=x, y=y, width=width, height=height)
    old_value = item_vals[col_index]
    entry_popup.insert(0, old_value)
    entry_popup.focus()

    def save_edit(e):
        new_val_str = entry_popup.get()
        try:
            if col_index in [4,5,6]:
                # parse as float
                new_value = float(new_val_str)
            else:
                # parse as int for columns 7..8
                new_value = int(new_val_str)
        except ValueError:
            # If invalid, revert
            entry_popup.destroy()
            return
        # Update the basket_items dict
        produkt = item_vals[0]
        parent = basket_tree.parent(selected_item)
        key_map = {
            4: "koeficient",
            5: "nakup_materialu",
            6: "cena_prace",
            7: "pocet_materialu",
            8: "pocet_prace"
        }
        if parent in basket_items and produkt in basket_items[parent]:
            basket_items[parent][produkt][key_map[col_index]] = new_value
        # Rebuild the tree
        update_basket_table(basket_tree, basket_items)
        mark_modified()
        entry_popup.destroy()

    entry_popup.bind("<Return>", save_edit)
    entry_popup.bind("<FocusOut>", save_edit)

# ---------- Example add_to_basket that sets new fields to 1 ----------
def add_to_basket(item, basket_items, update_basket_table, basket_tree):
    """
    Adds a product (provided as a tuple from DB) to the basket.
    We assume item has at least 7 fields:
       0: produkt
       1: jednotky
       2: dodavatel
       3: odkaz
       4: koeficient
       5: nakup_materialu
       6: cena_prace
       (7: optional section)
    """
    print("📦 item =", item)
    produkt = item[0]
    try:
        section = item[7] 
    except IndexError:
        section = "Uncategorized"

    item_data = {
        "jednotky":        item[1],
        "dodavatel":       item[2],
        "odkaz":           item[3],
        "koeficient":      float(item[4]),
        "nakup_materialu": float(item[5]),
        "cena_prace":      float(item[6]),
        "pocet_materialu": 1,
        "pocet_prace":     1
    }
    if section not in basket_items:
        basket_items[section] = OrderedDict()
    if produkt in basket_items[section]:
        basket_items[section][produkt]["pocet_materialu"] += 1
        basket_items[section][produkt]["pocet_prace"] += 1
    else:
        basket_items[section][produkt] = item_data
    update_basket_table(basket_tree, basket_items)
    mark_modified()

# ---------- Start of the GUI code ----------
if len(sys.argv) < 2:
    print("❌ No project name provided.")
    sys.exit(1)

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

category_structure = {}
cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
for class_id, main_cat, tab_name in cursor.fetchall():
    category_structure.setdefault(main_cat, []).append((class_id, tab_name))

filter_frame, setup_category_tree, category_vars, table_vars = create_filter_panel(
    root,
    lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
)
filter_frame.config(width=280)
filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5,0), pady=5)
setup_category_tree(category_structure)

main_frame = tk.Frame(root)
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

top_frame = tk.Frame(main_frame)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

home_button = tk.Button(top_frame, text="🏠 Home", command=return_home)
home_button.pack(side=tk.LEFT, padx=(0,10))

tk.Label(top_frame, text="Tvoje meno:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0,5))
user_name_entry = tk.Entry(top_frame, width=20)
user_name_entry.pack(side=tk.LEFT, padx=(0,15))

def on_name_change(*args):
    if user_name_entry.get().strip():
        export_button.config(state=tk.NORMAL)
    else:
        export_button.config(state=tk.DISABLED)
user_name_entry.bind("<KeyRelease>", lambda event: on_name_change())

tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
name_entry = tk.Entry(top_frame, width=30)
name_entry.pack(side=tk.LEFT, padx=5)
name_entry.bind("<KeyRelease>", lambda event: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree))

# DB Items TreeView
tree_frame = tk.Frame(main_frame)
tree_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

db_columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup materialu", "cena prace")
tree = ttk.Treeview(tree_frame, columns=db_columns, show="headings")
for col in db_columns:
    tree.heading(col, text=col.capitalize())
    tree.column(col, anchor="center")
tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<Configure>", adjust_db_columns)

def on_tree_double_click(event):
    selected = tree.focus()
    values = tree.item(selected)["values"]
    if not values or "--" in str(values[1]):
        return
    # We call our local add_to_basket that includes the new keys
    add_to_basket(values, basket_items, update_basket_table, basket_tree)
    print("🗁 Double-clicked:", values)

tree.bind("<Double-1>", on_tree_double_click)

# Basket TreeView with new columns
basket_items = OrderedDict()

basket_frame = tk.Frame(main_frame)
basket_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10)).pack()

basket_columns = (
    "produkt", 
    "jednotky", 
    "dodavatel", 
    "odkaz", 
    "koeficient", 
    "nakup materialu", 
    "cena prace", 
    "pocet materialu", 
    "pocet prace"
)
basket_tree = ttk.Treeview(basket_frame, columns=basket_columns, show="tree headings")
basket_tree.heading("#0", text="Section")
basket_tree.column("#0", width=150, anchor="w", stretch=False)
for col in basket_columns:
    basket_tree.heading(col, text=col.capitalize())
    basket_tree.column(col, anchor="center", stretch=False)
basket_tree.pack(fill=tk.BOTH, expand=True)
basket_tree.bind("<Configure>", adjust_basket_columns)

create_notes_panel(basket_frame, project_name)

# Bind double-click to let user edit columns 4..8
basket_tree.bind("<Double-1>", edit_basket_cell)

def remove_wrapper():
    from gui_functions import remove_from_basket
    remove_from_basket(basket_tree, basket_items, update_basket_table)
    mark_modified()

tk.Button(basket_frame, text="Odstrániť", command=remove_wrapper).pack(pady=3)

def try_export():
    if not user_name_entry.get().strip():
        messagebox.showwarning("Meno chýba", "⚠ Prosím zadaj svoje meno pred exportom.")
        return
    update_excel_from_basket(basket_items, project_name)

export_button = tk.Button(basket_frame, text="Exportovať", command=try_export, state=tk.DISABLED)
export_button.pack(pady=3)

def backup_project():
    save_basket(project_path, project_name, basket_items, user_name_entry.get().strip())
    mark_modified()
    messagebox.showinfo("Záloha", "Záloha bola vytvorená (nový basket_*.json).")

backup_button = tk.Button(basket_frame, text="Zálohovať", command=backup_project)
backup_button.pack(pady=3)

on_name_change()

# Drag-and-drop binds
basket_tree.bind("<ButtonPress-1>", on_drag_start)
basket_tree.bind("<B1-Motion>", on_drag_motion)
basket_tree.bind("<ButtonRelease-1>", on_drag_release)

# Load basket, migrating old data so the new keys default to 1
basket_items_loaded, saved_user_name = load_basket(project_path, project_name, file_path=commit_file)

for section_key in basket_items_loaded:
    for product_key, item_data in basket_items_loaded[section_key].items():
        item_data.setdefault("pocet_materialu", 1)
        item_data.setdefault("pocet_prace", 1)

basket_items.update(basket_items_loaded)
user_name_entry.insert(0, saved_user_name)
update_basket_table(basket_tree, basket_items)
apply_filters(conn.cursor(), db_type, table_vars, category_vars, name_entry, tree)

def on_closing():
    if basket_modified:
        save_basket(project_path, project_name, basket_items, user_name_entry.get().strip())
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
