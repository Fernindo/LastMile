import tkinter as tk
from tkinter import ttk, messagebox
import sys
from excel_processing import update_excel
from filter_panel import create_filter_panel
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

if len(sys.argv) < 2:
    print("❌ No project name provided.")
    sys.exit(1)
project_name = sys.argv[1]

conn, db_type = get_database_connection()
cursor = conn.cursor()
if db_type == 'postgres':
    sync_postgres_to_sqlite(conn)

root = tk.Tk()
root.state('zoomed')
root.title(f"Project: {project_name}")

category_structure = {}
cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
for class_id, main_cat, tab_name in cursor.fetchall():
    category_structure.setdefault(main_cat, []).append((class_id, tab_name))

category_vars = {}
table_vars = {}
basket_items = {}

filter_frame, setup_category_tree, category_vars, table_vars = create_filter_panel(
    root,
    lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
)
filter_frame.config(width=280)
filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0), pady=5)

setup_category_tree(category_structure)

main_frame = tk.Frame(root)
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

top_frame = tk.Frame(main_frame)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

name_entry = tk.Entry(top_frame, width=30)
tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
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

tree.bind("<Double-1>", on_tree_double_click)

# 🧺 Basket section (full data)
basket_frame = tk.Frame(main_frame)
basket_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10)).pack()

basket_columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace", "pocet")
basket_tree = ttk.Treeview(basket_frame, columns=basket_columns, show="headings")

for col in basket_columns:
    basket_tree.heading(col, text=col.capitalize())
    basket_tree.column(col, anchor="center")
basket_tree.pack(fill=tk.BOTH, expand=True)

basket_tree.bind("<Double-1>", lambda e: edit_pocet_cell(e, basket_tree, basket_items, update_basket_table))

tk.Button(basket_frame, text="Odstrániť", command=lambda: remove_from_basket(basket_tree, basket_items, update_basket_table)).pack(pady=3)
tk.Button(basket_frame, text="Exportovať", command=lambda: update_excel_from_basket(basket_items, project_name)).pack(pady=3)


root.protocol("WM_DELETE_WINDOW", lambda: (save_basket(project_name, basket_items), conn.close(), root.destroy()))
basket_items = load_basket(project_name)
update_basket_table(basket_tree, basket_items)
apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
root.mainloop()
