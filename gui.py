import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
import sqlite3
import socket
import json
import os
import sys
import decimal
from excel_processing import update_excel

def is_online(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def get_database_connection():
    if is_online():
        try:
            conn = psycopg2.connect(
                host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
                port=5432,
                user="neondb_owner",
                password="npg_aYC4yHnQIjV1",
                dbname="neondb",
                sslmode="require"
            )
            print("🟢 Connected to PostgreSQL")
            return conn, 'postgres'
        except Exception as e:
            print("PostgreSQL connection failed:", e)

    conn = sqlite3.connect("local_backup.db")
    print("🟠 Using local SQLite database (offline mode)")
    return conn, 'sqlite'

def sync_postgres_to_sqlite(pg_conn):
    sqlite_conn = sqlite3.connect("local_backup.db")
    pg_cursor = pg_conn.cursor()
    sqlite_cursor = sqlite_conn.cursor()

    sqlite_cursor.execute("DROP TABLE IF EXISTS produkty")
    sqlite_cursor.execute("""
        CREATE TABLE produkty (
            id INTEGER PRIMARY KEY,
            produkt TEXT,
            jednotky TEXT,
            dodavatel TEXT,
            odkaz TEXT,
            koeficient REAL,
            nakup_materialu REAL,
            cena_prace REAL,
            class_id TEXT,
            class_name TEXT
        )
    """)

    pg_cursor.execute("""
        SELECT p.id, p.produkt, p.jednotky, p.dodavatel, p.odkaz,
               p.koeficient, p.nakup_materialu, p.cena_prace, c.id, c.nazov_tabulky
        FROM produkty p
        JOIN class c ON p.class_id = c.id
    """)
    rows = pg_cursor.fetchall()

    safe_rows = []
    for row in rows:
        safe_row = []
        for value in row:
            if isinstance(value, decimal.Decimal):
                safe_row.append(float(value))
            else:
                safe_row.append(value)
        safe_rows.append(tuple(safe_row))

    sqlite_cursor.executemany("INSERT INTO produkty VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", safe_rows)
    sqlite_conn.commit()
    sqlite_conn.close()
    print("✔ Synced PostgreSQL → SQLite with Decimal fix")

if len(sys.argv) < 2:
    print("❌ No project name provided.")
    sys.exit(1)
project_name = sys.argv[1]

def get_basket_filename():
    return f"{project_name}.json"

conn, db_type = get_database_connection()
cursor = conn.cursor()
if db_type == 'postgres':
    sync_postgres_to_sqlite(conn)

root = tk.Tk()
root.title(f"Project: {project_name}")
root.state("zoomed")

project_label = tk.Label(root, text=f"Projekt: {project_name}", font=("Arial", 16, "bold"), pady=10)
project_label.pack()

category_structure = {}
cursor.execute("SELECT id, hlavna_kategoria FROM class")
for class_id, main_cat in cursor.fetchall():
    category_structure.setdefault(main_cat, []).append(class_id)

filter_frame = tk.Frame(root)
filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

category_vars = {}
table_vars = {}
basket_items = {}

def save_basket():
    with open(get_basket_filename(), "w", encoding="utf-8") as f:
        json.dump(basket_items, f)

def load_basket():
    global basket_items
    basket_items = {}
    filename = get_basket_filename()
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r", encoding="utf-8") as f:
            try:
                raw_items = json.load(f)
                basket_items = {int(k): v for k, v in raw_items.items()}
            except json.JSONDecodeError:
                print("⚠ JSON decode error - basket file is not valid.")
    update_basket_table()

def apply_filters():
    selected_class_ids = [t for t, var in table_vars.items() if var.get()]
    name_filter = name_entry.get().strip().lower()
    rows = []
    try:
        query = "SELECT id, produkt, jednotky, dodavatel, odkaz, koeficient, nakup_materialu, cena_prace FROM produkty WHERE 1=1"
        params = []
        if selected_class_ids:
            placeholders = ','.join(['?'] * len(selected_class_ids))
            query += f" AND class_id IN ({placeholders})"
            params.extend(selected_class_ids)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Chyba pri filtrovaní", str(e))
        return

    tree.delete(*tree.get_children())
    for row in rows:
        if not name_filter or name_filter in row[1].lower():
            tree.insert("", tk.END, values=row)

def reset_filters():
    for var in table_vars.values():
        var.set(False)
    name_entry.delete(0, tk.END)
    apply_filters()

def build_filter_tree():
    tk.Label(filter_frame, text="Prehliadač databázových tabuliek", font=("Arial", 10, "bold")).pack(anchor="w")
    for category, tables in category_structure.items():
        cat_frame = tk.Frame(filter_frame)
        cat_var = tk.BooleanVar(value=True)
        category_vars[category] = cat_var
        cat_label = ttk.Checkbutton(cat_frame, text=category, variable=cat_var)
        cat_label.pack(anchor="w", padx=2)
        inner_frame = tk.Frame(cat_frame)
        for table in tables:
            table_vars[table] = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(inner_frame, text=table, variable=table_vars[table], command=apply_filters)
            chk.pack(anchor="w", padx=20)
        inner_frame.pack()
        cat_frame.pack(anchor="w", fill="x", pady=2)
    tk.Button(filter_frame, text="Resetovať filtre", command=reset_filters).pack(anchor="w", pady=10, padx=5)

build_filter_tree()

main_frame = tk.Frame(root)
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

top_frame = tk.Frame(main_frame)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
name_entry = tk.Entry(top_frame, width=30)
name_entry.pack(side=tk.LEFT, padx=5)
name_entry.bind("<KeyRelease>", lambda event: apply_filters())

tree_frame = tk.Frame(main_frame)
tree_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

columns = ("id", "produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col.capitalize())
    tree.column(col, anchor="center")
tree.pack(fill=tk.BOTH, expand=True)

basket_frame = tk.Frame(main_frame)
basket_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10)).pack()

basket_tree = ttk.Treeview(basket_frame, columns=("id", "produkt", "nakup_materialu", "koeficient", "pocet"), show="headings")
for col in basket_tree["columns"]:
    basket_tree.heading(col, text=col.capitalize())
    basket_tree.column(col, anchor="center")
basket_tree.pack(fill=tk.BOTH, expand=True)

basket_tree.bind("<Double-1>", lambda e: edit_pocet_cell(e))
tree.bind("<Double-1>", lambda e: add_to_basket(tree.item(tree.focus())["values"]))

def add_to_basket(item):
    pocet = 1
    item_id = item[0]
    if item_id in basket_items:
        basket_items[item_id]["pocet"] += pocet
    else:
        basket_items[item_id] = {
            "id": item_id,
            "produkt": item[1],
            "nakup_materialu": item[6],
            "koeficient": item[5],
            "pocet": pocet
        }
    update_basket_table()

def update_basket_table():
    basket_tree.delete(*basket_tree.get_children())
    for item in basket_items.values():
        basket_tree.insert("", tk.END, values=(item["id"], item["produkt"], item["nakup_materialu"], item["koeficient"], item["pocet"]))

def edit_pocet_cell(event):
    selected_item = basket_tree.focus()
    if not selected_item:
        return
    col = basket_tree.identify_column(event.x)
    col_index = int(col.replace('#', '')) - 1
    if col not in ["#4", "#5"]:
        return
    x, y, width, height = basket_tree.bbox(selected_item, col)
    entry_popup = tk.Entry(basket_tree)
    entry_popup.place(x=x, y=y, width=width, height=height)
    current_value = basket_tree.item(selected_item)['values'][col_index]
    entry_popup.insert(0, current_value)
    entry_popup.focus()

    def save_edit(event):
        try:
            new_value = float(entry_popup.get()) if col == "#4" else int(entry_popup.get())
        except ValueError:
            new_value = current_value
        values = list(basket_tree.item(selected_item)["values"])
        values[col_index] = new_value
        basket_tree.item(selected_item, values=values)
        item_id = values[0]
        if item_id in basket_items:
            if col == "#4":
                basket_items[item_id]["koeficient"] = new_value
            elif col == "#5":
                basket_items[item_id]["pocet"] = new_value
        entry_popup.destroy()

    entry_popup.bind("<Return>", save_edit)
    entry_popup.bind("<FocusOut>", save_edit)

def remove_from_basket():
    selected_items = basket_tree.selection()
    for item in selected_items:
        item_id = basket_tree.item(item)["values"][0]
        if item_id in basket_items:
            del basket_items[item_id]
        basket_tree.delete(item)
    update_basket_table()

def update_excel_from_basket():
    if not basket_items:
        messagebox.showwarning("No Items", "⚠ Košík je prázdny.")
        return
    excel_data = [(v["id"], v["produkt"], v["nakup_materialu"], v["koeficient"], v["pocet"]) for v in basket_items.values()]
    update_excel(excel_data)

tk.Button(basket_frame, text="Odstrániť", command=remove_from_basket).pack(pady=3)
tk.Button(basket_frame, text="Exportovať", command=update_excel_from_basket).pack(pady=3)

def on_close():
    save_basket()
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
load_basket()
apply_filters()
root.mainloop()
