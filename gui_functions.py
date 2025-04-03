import socket
import json
import os
import sqlite3
import psycopg2
import decimal
import tkinter as tk
from tkinter import messagebox, filedialog
from excel_processing import update_excel
import unicodedata

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
    print("🕠 Using local SQLite database (offline mode)")
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
    print("✔ Synced PostgreSQL → SQLite")

def get_basket_filename(project_name):
    return f"{project_name}.json"

def save_basket(project_name, basket_items):
    with open(get_basket_filename(project_name), "w", encoding="utf-8") as f:
        json.dump(basket_items, f)

def load_basket(project_name):
    basket_items = {}
    filename = get_basket_filename(project_name)
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "r", encoding="utf-8") as f:
            try:
                basket_items = json.load(f)
            except json.JSONDecodeError:
                print("⚠ JSON decode error - basket file is not valid.")
    return basket_items

def show_error(message):
    messagebox.showerror("Chyba", message)
    return []

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree):
    selected_class_ids = [str(cid) for cid, var in table_vars.items() if var.get()]
    name_filter = remove_accents(name_entry.get().strip().lower())

    rows = []
    try:
        query = "SELECT produkt, jednotky, dodavatel, odkaz, koeficient, nakup_materialu, cena_prace, class_id FROM produkty WHERE 1=1"
        params = []
        if selected_class_ids:
            placeholders = ','.join(['%s' if db_type == 'postgres' else '?'] * len(selected_class_ids))
            query += f" AND class_id IN ({placeholders})"
            params.extend(selected_class_ids)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    except Exception as e:
        show_error(str(e))
        return

    tree.delete(*tree.get_children())

    grouped = {}
    for row in rows:
        produkt = row[0]
        if not name_filter or name_filter in remove_accents(produkt.lower()):
            class_id = row[-1]
            grouped.setdefault(class_id, []).append(row[:-1])

    class_name_map = {}
    cursor.execute("SELECT id, nazov_tabulky FROM class")
    for cid, cname in cursor.fetchall():
        class_name_map[str(cid)] = cname

    for class_id in sorted(grouped):
        class_name = class_name_map.get(class_id, f"Trieda {class_id}")
        tree.insert("", "end", values=("", f"-- {class_name} --"), tags=("header",))
        for row in grouped[class_id]:
            tree.insert("", "end", values=row)

    tree.tag_configure("header", font=("Arial", 10, "bold"))

def update_basket_table(basket_tree, basket_items):
    basket_tree.delete(*basket_tree.get_children())
    for section, products in basket_items.items():
        basket_tree.insert("", "end", iid=section, text=section, open=True)
        for produkt, item_data in products.items():
            basket_tree.insert(
                section,
                "end",
                values=(
                    produkt,
                    item_data["jednotky"],
                    item_data["dodavatel"],
                    item_data["odkaz"],
                    item_data["koeficient"],
                    item_data["nakup_materialu"],
                    item_data["cena_prace"],
                    item_data["pocet"]
                )
            )




def add_to_basket(item, basket_items, update_basket_table, basket_tree):
    produkt = item[0]
    class_name = item[7]  # section name

    item_data = {
        "jednotky": item[1],
        "dodavatel": item[2],
        "odkaz": item[3],
        "koeficient": item[4],
        "nakup_materialu": item[5],
        "cena_prace": item[6],
        "pocet": 1
    }

    if class_name not in basket_items:
        basket_items[class_name] = {}

    if produkt in basket_items[class_name]:
        basket_items[class_name][produkt]["pocet"] += 1
    else:
        basket_items[class_name][produkt] = item_data

    update_basket_table(basket_tree, basket_items)


def edit_pocet_cell(event, basket_tree, basket_items, update_basket_table):
    selected_item = basket_tree.focus()
    if not selected_item:
        return
    col = basket_tree.identify_column(event.x)
    col_index = int(col.replace('#', '')) - 1
    if col not in ["#8"]:
        return
    x, y, width, height = basket_tree.bbox(selected_item, col)
    entry_popup = tk.Entry(basket_tree)
    entry_popup.place(x=x, y=y, width=width, height=height)
    current_value = basket_tree.item(selected_item)['values'][col_index]
    entry_popup.insert(0, current_value)
    entry_popup.focus()

    def save_edit(event):
        produkt = basket_tree.item(selected_item)['values'][0]
        try:
            new_value = int(entry_popup.get())
        except ValueError:
            new_value = current_value
        if produkt in basket_items:
            basket_items[produkt]["pocet"] = new_value
        update_basket_table(basket_tree, basket_items)
        entry_popup.destroy()

    entry_popup.bind("<Return>", save_edit)
    entry_popup.bind("<FocusOut>", save_edit)

def remove_from_basket(basket_tree, basket_items, update_basket_table):
    for item in basket_tree.selection():
        produkt = basket_tree.item(item)["values"][0]
        basket_items.pop(produkt, None)
        basket_tree.delete(item)
    update_basket_table(basket_tree, basket_items)

def update_excel_from_basket(basket_items, project_name):
    if not basket_items:
        messagebox.showwarning("Košík je prázdny", "⚠ Nie sú vybraté žiadne položky na export.")
        return

    # Build path to Desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, f"{project_name}.xlsx")

    # Format the data to match what excel_processing expects
    excel_data = []
    for section, products in basket_items.items():
        for produkt, v in products.items():
            excel_data.append((
                section,  # <-- pass section name as first item
                produkt,
                v["jednotky"],
                v["dodavatel"],
                v["odkaz"],
                v["koeficient"],
                v["nakup_materialu"],
                v["cena_prace"],
                v["pocet"]
            ))


    update_excel(excel_data, file_path)

    # Notify the user
    messagebox.showinfo("Export hotový", f"✅ Súbor bol úspešne uložený na plochu ako:\n{file_path}")