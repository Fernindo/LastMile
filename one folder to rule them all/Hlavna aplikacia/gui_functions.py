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
    # fallback
    conn = sqlite3.connect("local_backup.db")
    print("🕠 Using local SQLite database (offline mode)")
    return conn, 'sqlite'

def sync_postgres_to_sqlite(pg_conn):
    """
    Sync data from PostgreSQL (table 'produkty') into local SQLite.
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
        for v in row:
            safe_row.append(float(v) if isinstance(v, decimal.Decimal) else v)
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
    Save the basket JSON (with timestamp) in the project's 'projects' folder.
    """
    out = {"user_name": user_name, "items": []}
    for section, prods in basket_items.items():
        sec_obj = {"section": section, "products": []}
        for pname, info in prods.items():
            sec_obj["products"].append({
                "produkt":        pname,
                "jednotky":       info.get("jednotky", ""),
                "dodavatel":      info.get("dodavatel", ""),
                "odkaz":          info.get("odkaz", ""),
                "koeficient":     info.get("koeficient", 0),
                "nakup_materialu":info.get("nakup_materialu", 0),
                "cena_prace":     info.get("cena_prace", 0),
                "pocet_prace":    info.get("pocet_prace", 1),
                "pocet_materialu":info.get("pocet_materialu", 1),
            })
        out["items"].append(sec_obj)

    os.makedirs(project_path, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname = os.path.join(project_path, f"basket_{ts}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

def load_basket(project_path, project_name, file_path=None):
    """
    Load the most recent basket JSON (or a specified path).
    Returns (OrderedDict of items, saved_user_name).
    """
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
    except:
        return OrderedDict(), ""

    basket_items = OrderedDict()
    for sec in data.get("items", []):
        section = sec.get("section", "")
        prods = OrderedDict()
        for p in sec.get("products", []):
            pname = p.get("produkt")
            if not pname: continue
            prods[pname] = {
                "jednotky":        p.get("jednotky",""),
                "dodavatel":       p.get("dodavatel",""),
                "odkaz":           p.get("odkaz",""),
                "koeficient":      float(p.get("koeficient",0)),
                "nakup_materialu": float(p.get("nakup_materialu",0)),
                "cena_prace":      float(p.get("cena_prace",0)),
                "pocet_prace":     int(p.get("pocet_prace",1)),
                "pocet_materialu": int(p.get("pocet_materialu",1)),
            }
        basket_items[section] = prods

    return basket_items, data.get("user_name","")

def show_error(msg):
    messagebox.showerror("Chyba", msg)
    return []

def remove_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree):
    """
    Load products from 'produkty', filter by class_ids and search text.
    Populate `tree` with grouped rows.
    """
    # build class filter
    sel_ids = [cid for cid, var in table_vars.items() if var.get()]
    name_f = remove_accents(name_entry.get().strip().lower())

    query = "SELECT produkt, jednotky, dodavatel, odkaz, koeficient, nakup_materialu, cena_prace, class_id FROM produkty WHERE 1=1"
    params = []
    if sel_ids:
        placeholder = ",".join("?" if db_type=="sqlite" else "%s" for _ in sel_ids)
        query += f" AND class_id IN ({placeholder})"
        params.extend(sel_ids)

    try:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    except Exception as e:
        show_error(str(e))
        return

    tree.delete(*tree.get_children())
    grouped = {}
    for r in rows:
        prod = r[0]
        if not name_f or name_f in remove_accents(prod.lower()):
            cid = r[-1]
            grouped.setdefault(cid, []).append(r[:-1])

    # lookup class names
    cnames = {}
    try:
        cursor.execute("SELECT id, nazov_tabulky FROM public.class")
        for cid, nm in cursor.fetchall():
            cnames[cid] = nm
    except:
        pass

    for cid in sorted(grouped):
        header = cnames.get(cid, "Uncategorized")
        tree.insert("", "end", values=("", f"-- {header} --"), tags=("header",))
        for row in grouped[cid]:
            tree.insert("", "end", values=row + (header,))
    tree.tag_configure("header", font=("Arial", 10, "bold"))

def update_basket_table(basket_tree, basket_items):
    basket_tree.delete(*basket_tree.get_children())
    for section, prods in basket_items.items():
        basket_tree.insert("", "end", iid=section, text=section, open=True)
        for pname, info in prods.items():
            basket_tree.insert("", "end", values=(
                pname,
                info["jednotky"],
                info["dodavatel"],
                info["odkaz"],
                info["koeficient"],
                info["nakup_materialu"],
                info["cena_prace"],
                info["pocet_prace"],
                info["pocet_materialu"],
            ))

def add_to_basket(item, basket_items, update_basket_table, basket_tree):
    prod, jednotky, dodavatel, odkaz, koef, nakup, cena, *rest = item
    section = rest[-1] if rest else "Uncategorized"
    data = {
        "jednotky": jednotky,
        "dodavatel": dodavatel,
        "odkaz":     odkaz,
        "koeficient":koef,
        "nakup_materialu": nakup,
        "cena_prace":cena,
        "pocet_prace":1,
        "pocet_materialu":1
    }
    if section not in basket_items:
        basket_items[section] = OrderedDict()
    if prod in basket_items[section]:
        basket_items[section][prod]["pocet_prace"]    += 1
        basket_items[section][prod]["pocet_materialu"]+= 1
    else:
        basket_items[section][prod] = data
    update_basket_table(basket_tree, basket_items)

def edit_pocet_cell(event, basket_tree, basket_items, update_basket_table):
    region = basket_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    sel = basket_tree.focus()
    if not sel or basket_tree.get_children(sel):
        return
    vals = basket_tree.item(sel)["values"]
    col = basket_tree.identify_column(event.x)
    idx = int(col.replace("#","")) - 1
    if idx not in [4,5,6,7]:
        return
    x,y,w,h = basket_tree.bbox(sel, col)
    entry = tk.Entry(basket_tree)
    entry.place(x=x, y=y, width=w, height=h)
    entry.insert(0, vals[idx])
    entry.focus()

    def save(e=None):
        try:
            newv = float(entry.get()) if idx!=7 else int(entry.get())
        except:
            entry.destroy()
            return
        section = basket_tree.parent(sel)
        prod    = vals[0]
        keymap = {4:"koeficient",5:"nakup_materialu",6:"cena_prace",7:"pocet_prace"}
        basket_items[section][prod][keymap[idx]] = newv
        update_basket_table(basket_tree, basket_items)
        entry.destroy()

    entry.bind("<Return>", save)
    entry.bind("<FocusOut>", save)

def remove_from_basket(basket_tree, basket_items, update_basket_table):
    for iid in basket_tree.selection():
        parent = basket_tree.parent(iid)
        if not parent:
            basket_items.pop(basket_tree.item(iid)["text"], None)
        else:
            prod = basket_tree.item(iid)["values"][0]
            section = basket_tree.item(parent)["text"]
            basket_items[section].pop(prod, None)
    update_basket_table(basket_tree, basket_items)

def update_excel_from_basket(basket_items, project_name):
    """
    Exports the current basket to an Excel file on the Desktop.
    Shows success only if update_excel() returns True.
    """
    if not basket_items:
        messagebox.showwarning("Košík je prázdny", "⚠ Nie sú vybraté žiadne položky na export.")
        return

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    out_file = os.path.join(desktop, f"{project_name}.xlsx")

    # Prepare the data rows
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

    # Call the updated update_excel, which now returns True/False
    success = update_excel(excel_data, out_file)
    if success and os.path.exists(out_file):
        messagebox.showinfo(
            "Export hotový",
            f"✅ Súbor bol úspešne uložený na plochu ako:\n{out_file}"
        )
    else:
        """
        messagebox.showerror(
            "Export zlyhal",
            "❌ Nepodarilo sa vytvoriť Excel súbor.\n"
            "  • Skontrolujte, či máte šablónu 'Vzorova_CP3.xlsx' v rovnakej zložke.\n"
            "  • Skontrolujte, či máte povolenia na zápis na plochu."
        )
        """