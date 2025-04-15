import tkinter as tk
from tkinter import ttk, messagebox
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
    update_basket_table,
    add_to_basket,
    edit_pocet_cell,
    remove_from_basket,
    update_excel_from_basket
)
import subprocess
import filter_panel
import json
from datetime import datetime

# Global flag to track modifications in the basket
basket_modified = False

def mark_modified():
    global basket_modified
    basket_modified = True

def block_expand_collapse(event):
    return "break"

# Require at least one argument: the project folder path.
if len(sys.argv) < 2:
    print("❌ No project name provided.")
    sys.exit(1)

project_path = sys.argv[1]
project_name = os.path.basename(project_path)

# Optional: if a specific JSON file is provided in sys.argv[2], load that version.
commit_file = sys.argv[2] if len(sys.argv) > 2 else None

conn, db_type = get_database_connection()
cursor = conn.cursor()
if db_type == 'postgres':
    sync_postgres_to_sqlite(conn)

root = tk.Tk()
root.state('zoomed')
root.title(f"Project: {project_name}")

def return_home():
    # When going "Home", save only if modifications have occurred.
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

tree_frame = tk.Frame(main_frame)
tree_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col.capitalize())
    tree.column(col, anchor="center")
tree.pack(fill=tk.BOTH, expand=True)

def on_tree_double_click(event):
    selected = tree.focus()
    values = tree.item(selected)["values"]
    if not values or "--" in str(values[1]):
        return
    add_to_basket(values, basket_items, update_basket_table, basket_tree)
    mark_modified()  # Mark that the basket has been changed
    print("🗁 Double-clicked:", values)

tree.bind("<Double-1>", on_tree_double_click)

basket_items = OrderedDict()

basket_frame = tk.Frame(main_frame)
basket_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10)).pack()

basket_columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace", "pocet")
basket_tree = ttk.Treeview(basket_frame, columns=basket_columns, show="tree headings")

basket_tree.bind("<<TreeviewOpen>>", block_expand_collapse)
basket_tree.bind("<<TreeviewClose>>", block_expand_collapse)
basket_tree.bind("<Button-1>", lambda e: "break" if basket_tree.identify_region(e.x, e.y) == "tree" else None)

for col in basket_columns:
    basket_tree.heading(col, text=col.capitalize())
    basket_tree.column(col, anchor="center")
basket_tree.pack(fill=tk.BOTH, expand=True)

create_notes_panel(basket_frame, project_name)
basket_tree.bind("<Double-1>", lambda e: edit_pocet_cell(e, basket_tree, basket_items, update_basket_table) or mark_modified())

tk.Button(basket_frame, text="Odstrániť", 
          command=lambda: (remove_from_basket(basket_tree, basket_items, update_basket_table), mark_modified())
         ).pack(pady=3)

def try_export():
    user_name = user_name_entry.get().strip()
    if not user_name:
        messagebox.showwarning("Meno chýba", "⚠ Prosím zadaj svoje meno pred exportom.")
        return
    update_excel_from_basket(basket_items, project_name)

export_button = tk.Button(basket_frame, text="Exportovať", command=try_export, state=tk.DISABLED)
export_button.pack(pady=3)

# --- Backup Button (on-demand) ---
def backup_project():
    """
    Creates a backup file by saving a new commit.
    """
    save_basket(project_path, project_name, basket_items, user_name_entry.get().strip())
    mark_modified()  # Mark that a new save has been made via backup.
    messagebox.showinfo("Záloha", "Záloha bola vytvorená (nový basket_*.json).")

backup_button = tk.Button(basket_frame, text="Zálohovať", command=backup_project)
backup_button.pack(pady=3)
# ------------------------------

on_name_change()

dragging_item = {"item": None}

def on_drag_start(event):
    iid = basket_tree.identify_row(event.y)
    if not iid:
        return
    dragging_item["item"] = iid

def on_drag_motion(event):
    if not dragging_item["item"]:
        return
    target_iid = basket_tree.identify_row(event.y)
    if not target_iid or target_iid == dragging_item["item"]:
        return
    dragging_is_section = not basket_tree.parent(dragging_item["item"])
    target_is_section = not basket_tree.parent(target_iid)
    if dragging_is_section and target_is_section:
        basket_tree.move(dragging_item["item"], '', basket_tree.index(target_iid))
    elif not dragging_is_section and not target_is_section:
        parent_drag = basket_tree.parent(dragging_item["item"])
        parent_target = basket_tree.parent(target_iid)
        if parent_drag == parent_target:
            basket_tree.move(dragging_item["item"], parent_drag, basket_tree.index(target_iid))

def on_drag_release(event):
    if dragging_item["item"]:
        iid = dragging_item["item"]
        if not basket_tree.parent(iid):
            reorder_basket_sections()
        else:
            reorder_basket_data()
        mark_modified()  # Mark any reordering as a modification.
    dragging_item["item"] = None

def reorder_basket_data():
    for section in basket_tree.get_children():
        reordered = OrderedDict()
        for child in basket_tree.get_children(section):
            values = basket_tree.item(child)["values"]
            produkt = values[0]
            reordered[produkt] = {
                "jednotky": values[1],
                "dodavatel": values[2],
                "odkaz": values[3],
                "koeficient": float(values[4]),
                "nakup_materialu": float(values[5]),
                "cena_prace": float(values[6]),
                "pocet": int(values[7])
            }
        basket_items[section] = reordered

def reorder_basket_sections():
    new_basket = OrderedDict()
    for section in basket_tree.get_children():
        new_basket[section] = basket_items[section]
    basket_items.clear()
    basket_items.update(new_basket)

basket_tree.bind("<ButtonPress-1>", on_drag_start)
basket_tree.bind("<B1-Motion>", on_drag_motion)
basket_tree.bind("<ButtonRelease-1>", on_drag_release)

# Load the basket: if commit_file is specified, load that; otherwise load the newest basket_*.json.
basket_items_loaded, saved_user_name = load_basket(project_path, project_name, file_path=commit_file)
basket_items.update(basket_items_loaded)
user_name_entry.insert(0, saved_user_name)
update_basket_table(basket_tree, basket_items)
apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

def on_closing():
    global basket_modified
    # Only save if modifications have been made.
    if basket_modified:
        save_basket(project_path, project_name, basket_items, user_name_entry.get().strip())
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
