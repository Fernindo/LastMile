import socket
import json
import os
import sqlite3
import psycopg2
import decimal
import tkinter as tk
from tkinter import messagebox, filedialog
from excel_processing import update_excel
from collections import OrderedDict
import unicodedata
from datetime import datetime
import glob

def is_online(host="8.8.8.8", port=53, timeout=3):
    """Check if we are online by trying to connect to Google DNS."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def get_database_connection():
    """
    Try connecting to PostgreSQL; if that fails, fall back to SQLite.
    """
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
    """
    Sync data from PostgreSQL (table 'produkty') into a local SQLite database.
    Uses a LEFT JOIN with public.class to fetch the actual category name.
    """
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
            class_id INTEGER,
            class_name TEXT
        )
    """)

    pg_cursor.execute("""
        SELECT 
            p.id,
            p.produkt,
            p.jednotky,
            p.dodavatel,
            p.odkaz,
            p.koeficient,
            p.nakup_materialu,
            p.cena_prace,
            p.class_id,
            c.nazov_tabulky
        FROM produkty p
        LEFT JOIN public.class c ON p.class_id = c.id
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

    sqlite_cursor.executemany(
        "INSERT INTO produkty VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        safe_rows
    )
    sqlite_conn.commit()
    sqlite_conn.close()
    print("✔ Synced PostgreSQL → SQLite")

def save_basket(project_path, project_name, basket_items, user_name=""):
    """
    Save a timestamped JSON that preserves section & product order
    plus all current numeric values.
    """
    out = {
        "user_name": user_name,
        "items": []
    }

    # basket_items is OrderedDict[section, OrderedDict[product, info_dict]]
    for section, products in basket_items.items():
        sec_obj = {"section": section, "products": []}
        for pname, info in products.items():
            sec_obj["products"].append({
                "produkt":         pname,
                "jednotky":        info.get("jednotky", ""),
                "dodavatel":       info.get("dodavatel", ""),
                "odkaz":           info.get("odkaz", ""),
                "koeficient":      info.get("koeficient", 0),
                "nakup_materialu": info.get("nakup_materialu", 0),
                "cena_prace":      info.get("cena_prace", 0),
                "pocet_prace":     info.get("pocet_prace", 1),
                "pocet_materialu": info.get("pocet_materialu", 1),
            })
        out["items"].append(sec_obj)

    os.makedirs(project_path, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(project_path, f"basket_{ts}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

def load_basket(project_path, project_name, file_path=None):
    """
    Load the most recent basket JSON (or the specified file),
    reconstructing an OrderedDict of sections→products and returning
    (basket_items, saved_user_name).
    """
    if file_path and os.path.isfile(file_path):
        path = file_path
    else:
        files = glob.glob(os.path.join(project_path, "basket_*.json"))
        if not files:
            return OrderedDict(), ""
        path = max(files, key=os.path.getmtime)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return OrderedDict(), ""

    user_name = data.get("user_name", "")
    basket_items = OrderedDict()
    for sec_obj in data.get("items", []):
        sec_name = sec_obj.get("section", "")
        prods = OrderedDict()
        for p in sec_obj.get("products", []):
            pname = p.get("produkt")
            if not pname:
                continue
            prods[pname] = {
                "jednotky":        p.get("jednotky", ""),
                "dodavatel":       p.get("dodavatel", ""),
                "odkaz":           p.get("odkaz", ""),
                "koeficient":      float(p.get("koeficient", 0)),
                "nakup_materialu": float(p.get("nakup_materialu", 0)),
                "cena_prace":      float(p.get("cena_prace", 0)),
                "pocet_prace":     int(p.get("pocet_prace", 1)),
                "pocet_materialu": int(p.get("pocet_materialu", 1)),
            }
        basket_items[sec_name] = prods

    return basket_items, user_name

def show_error(message):
    """Show an error message dialog."""
    messagebox.showerror("Chyba", message)
    return []

def remove_accents(text):
    """
    Remove diacritics from the given text.
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree):
    """
    Retrieves products from the SQLite 'produkty' table,
    optionally filtering by selected classes and text search.
    """
    selected_class_ids = [cid for cid, var in table_vars.items() if var.get()]
    name_filter = remove_accents(name_entry.get().strip().lower())
    rows = []
    try:
        query = """
            SELECT produkt, jednotky, dodavatel, odkaz, koeficient, 
                   nakup_materialu, cena_prace, class_id
            FROM produkty
            WHERE 1=1
        """
        params = []
        if selected_class_ids:
            if db_type == 'postgres':
                placeholders = ','.join(['%s'] * len(selected_class_ids))
            else:
                placeholders = ','.join(['?'] * len(selected_class_ids))
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
    try:
        cursor.execute("SELECT id, nazov_tabulky FROM public.class")
        for cid, cname in cursor.fetchall():
            if cid is not None:
                class_name_map[cid] = cname
    except Exception as e:
        print("Warning: Unable to retrieve class names:", e)
    
    for class_id in sorted(grouped):
        class_name = class_name_map.get(class_id, "Uncategorized")
        tree.insert("", "end", values=("", f"-- {class_name} --"), tags=("header",))
        for row in grouped[class_id]:
            tree.insert("", "end", values=row + (class_name,))
    tree.tag_configure("header", font=("Arial", 10, "bold"))

def update_basket_table(basket_tree, basket_items):
    """
    Updates the basket Treeview with data from the basket_items dictionary.
    """
    basket_tree.delete(*basket_tree.get_children())
    for section, products in basket_items.items():
        basket_tree.insert("", "end", iid=section, text=section, open=True)
        for produkt, item_data in products.items():
            basket_tree.insert("", "end", values=(
                produkt,
                item_data["jednotky"],
                item_data["dodavatel"],
                item_data["odkaz"],
                item_data["koeficient"],
                item_data["nakup_materialu"],
                item_data["cena_prace"],
                item_data["pocet_prace"],
                item_data["pocet_materialu"]
            ))

def add_to_basket(item, basket_items, update_basket_table, basket_tree):
    """
    Adds a product (provided as a tuple) to the basket.
    """
    prod, jednotky, dodavatel, odkaz, koef, nakup, cena, *rest = item
    class_name = rest[-1] if rest else "Uncategorized"
    item_data = {
        "jednotky": jednotky,
        "dodavatel": dodavatel,
        "odkaz": odkaz,
        "koeficient": koef,
        "nakup_materialu": nakup,
        "cena_prace": cena,
        "pocet_prace": 1,
        "pocet_materialu": 1
    }
    if class_name not in basket_items:
        basket_items[class_name] = OrderedDict()
    if prod in basket_items[class_name]:
        basket_items[class_name][prod]["pocet_prace"]    += 1
        basket_items[class_name][prod]["pocet_materialu"]+= 1
    else:
        basket_items[class_name][prod] = item_data
    update_basket_table(basket_tree, basket_items)

def edit_pocet_cell(event, basket_tree, basket_items, update_basket_table):
    """
    Allows editing of numeric cell values in the basket via double-click.
    """
    region = basket_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    selected_item = basket_tree.focus()
    if not selected_item or basket_tree.get_children(selected_item):
        return
    item_data = basket_tree.item(selected_item)
    if not item_data.get("values"):
        return
    col = basket_tree.identify_column(event.x)
    col_index = int(col.replace('#', '')) - 1
    if col_index not in [4, 5, 6, 7]:
        return
    x, y, width, height = basket_tree.bbox(selected_item, col)
    entry_popup = tk.Entry(basket_tree)
    entry_popup.place(x=x, y=y, width=width, height=height)
    entry_popup.insert(0, basket_tree.item(selected_item)["values"][col_index])
    entry_popup.focus()
    def save_edit(e):
        try:
            new_value = float(entry_popup.get()) if col_index != 7 else int(entry_popup.get())
        except ValueError:
            entry_popup.destroy()
            return
        prod = item_data['values'][0]
        parent = basket_tree.parent(selected_item)
        key_map = {4: "koeficient", 5: "nakup_materialu", 6: "cena_prace", 7: "pocet_prace"}
        if parent in basket_items and prod in basket_items[parent]:
            basket_items[parent][prod][key_map[col_index]] = new_value
        update_basket_table(basket_tree, basket_items)
        entry_popup.destroy()
    entry_popup.bind("<Return>", save_edit)
    entry_popup.bind("<FocusOut>", save_edit)

def block_expand_collapse(event):
    return "break"

def remove_from_basket(basket_tree, basket_items, update_basket_table):
    """
    Removes the selected product(s) from the basket.
    """
    for iid in basket_tree.selection():
        parent = basket_tree.parent(iid)
        if not parent:
            sec = basket_tree.item(iid, "text")
            basket_items.pop(sec, None)
        else:
            prod = basket_tree.item(iid)["values"][0]
            sec = basket_tree.item(parent, "text")
            basket_items[sec].pop(prod, None)
    update_basket_table(basket_tree, basket_items)

def update_excel_from_basket(basket_items, project_name):
    """
    Exports the current basket to an Excel file on the Desktop.
    """
    if not basket_items:
        messagebox.showwarning("Košík je prázdny", "⚠ Nie sú vybraté žiadne položky na export.")
        return
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, f"{project_name}.xlsx")
    excel_data = []
    for section, products in basket_items.items():
        for produkt, v in products.items():
            excel_data.append((
                section,
                produkt,
                v["jednotky"],
                v["dodavatel"],
                v["odkaz"],
                v["koeficient"],
                v["nakup_materialu"],
                v["cena_prace"],
                v["pocet_prace"]
            ))
    update_excel(excel_data, file_path)
    messagebox.showinfo("Export hotový", f"✅ Súbor bol úspešne uložený na plochu ako:\n{file_path}")
