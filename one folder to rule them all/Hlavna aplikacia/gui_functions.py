# gui_functions.py

import socket
import json
import os
import sqlite3
import psycopg2
import decimal
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import unicodedata
from datetime import datetime
import glob
from collections import OrderedDict
import copy

from basket import Basket, BasketItem
import threading

from helpers import (
    update_excel,
    create_filter_panel,
    create_notes_panel,
)

# ─── Network / Database Helpers ─────────────────────────────────────────────

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
    Returns (conn, db_type), where db_type is 'postgres' or 'sqlite'.
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
    # fallback to local SQLite
    conn = sqlite3.connect("local_backup.db", check_same_thread=False)
    print("🕠 Using local SQLite database (offline mode)")
    return conn, 'sqlite'

sqlite3.register_adapter(decimal.Decimal, float)

def sync_postgres_to_sqlite(pg_conn):
    """
    Pull produkty, class, and produkt_class from Postgres into local_backup.db.
    Ensures local SQLite mirror for offline use.
    """
    sqlite_conn   = sqlite3.connect("local_backup.db")
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor     = pg_conn.cursor()

    # ── 1) Sync produkty ────────────────────────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS produkty")
    sqlite_cursor.execute("""
        CREATE TABLE produkty (
            id INTEGER PRIMARY KEY,
            produkt TEXT,
            jednotky TEXT,
            dodavatel TEXT,
            odkaz TEXT,
            koeficient_material REAL,
            koeficient_prace REAL,
            nakup_materialu REAL,
            cena_prace REAL
        )
    """)
    pg_cursor.execute("""
        SELECT
          id, produkt, jednotky, dodavatel, odkaz,
          koeficient_material, koeficient_prace,
          nakup_materialu, cena_prace
        FROM produkty
    """)
    prod_rows = pg_cursor.fetchall()
    cleaned = [
        tuple(float(col) if isinstance(col, decimal.Decimal) else col
              for col in row)
        for row in prod_rows
    ]
    sqlite_cursor.executemany(
        "INSERT INTO produkty VALUES (?,?,?,?,?,?,?,?,?)",
        cleaned
    )

    # ── 2) Sync class ───────────────────────────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS class")
    sqlite_cursor.execute("""
        CREATE TABLE class (
            id INTEGER PRIMARY KEY,
            hlavna_kategoria TEXT,
            nazov_tabulky TEXT
        )
    """)
    pg_cursor.execute(
        "SELECT id, hlavna_kategoria, nazov_tabulky FROM public.class"
    )
    class_rows = pg_cursor.fetchall()
    sqlite_cursor.executemany(
        "INSERT INTO class VALUES (?,?,?)",
        class_rows
    )

    # ── 3) Sync produkt_class (junction) ───────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS produkt_class")
    sqlite_cursor.execute("""
        CREATE TABLE produkt_class (
            produkt_id INTEGER,
            class_id   INTEGER
        )
    """)
    pg_cursor.execute("SELECT produkt_id, class_id FROM produkt_class")
    pc_rows = pg_cursor.fetchall()
    sqlite_cursor.executemany(
        "INSERT INTO produkt_class VALUES (?,?)",
        pc_rows
    )

    sqlite_conn.commit()
    sqlite_conn.close()
    print("✔ Synced PostgreSQL → SQLite (produkty, class, produkt_class)")


def ensure_recommendation_schema(cursor, db_type):
    """Create recommendation-related tables and indexes if they don't exist."""
    if db_type == "sqlite":
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS co_occurrence (
                base_product_id INTEGER,
                co_product_id   INTEGER,
                count           INTEGER DEFAULT 0,
                last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (base_product_id, co_product_id)
            )
            """
        )
        # ── Ensure `last_updated` column exists (handle older DBs) ─────────────
        try:
            cursor.execute("PRAGMA table_info(co_occurrence)")
            cols = [row[1] for row in cursor.fetchall()]
            if "last_updated" not in cols:
                cursor.execute(
                    "ALTER TABLE co_occurrence ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                )
        except Exception:
            pass
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_co_base ON co_occurrence(base_product_id)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                base_product_id        INTEGER,
                recommended_product_id INTEGER,
                priority               REAL,
                PRIMARY KEY (base_product_id, recommended_product_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rec_base ON recommendations(base_product_id)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_feedback (
                base_product_id        INTEGER,
                recommended_product_id INTEGER,
                action                 TEXT,
                ts                     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    else:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS co_occurrence (
                base_product_id INTEGER,
                co_product_id   INTEGER,
                count           INTEGER DEFAULT 0,
                last_updated    TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (base_product_id, co_product_id)
            )
            """
        )
        # ── Ensure `last_updated` column exists on PostgreSQL ────────────────
        try:
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'co_occurrence' AND column_name = 'last_updated'
                """
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "ALTER TABLE co_occurrence ADD COLUMN last_updated TIMESTAMP DEFAULT NOW()"
                )
        except Exception:
            pass
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_co_base ON co_occurrence(base_product_id)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                base_product_id        INTEGER,
                recommended_product_id INTEGER,
                priority               REAL,
                PRIMARY KEY (base_product_id, recommended_product_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_rec_base ON recommendations(base_product_id)"
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_feedback (
                base_product_id        INTEGER,
                recommended_product_id INTEGER,
                action                 TEXT,
                ts                     TIMESTAMP DEFAULT NOW()
            )
            """
        )


def log_recommendation_feedback(cursor, db_type, base_id, rec_id, action):
    """Insert a feedback record into recommendation_feedback."""
    ensure_recommendation_schema(cursor, db_type)
    if db_type == "postgres":
        cursor.execute(
            "INSERT INTO recommendation_feedback (base_product_id, recommended_product_id, action) VALUES (%s,%s,%s)",
            (base_id, rec_id, action),
        )
    else:
        cursor.execute(
            "INSERT INTO recommendation_feedback (base_product_id, recommended_product_id, action) VALUES (?,?,?)",
            (base_id, rec_id, action),
        )

# ─── Basket Persistence / I/O ────────────────────────────────────────────────

def save_basket(project_path, project_name, basket_items, user_name=""):
    """
    Ask the user for a filename and save the basket JSON there.
    Returns True on success, False if canceled or error.
    """
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
        return False  # user canceled dialog

    out = {
        "user_name": user_name,
        "items": []
    }
    for section, prods in basket_items.items():
        sec_obj = {"section": section, "products": []}
        for pname, info in prods.items():
            sec_obj["products"].append({
                "produkt":             pname,
                "jednotky":            info.get("jednotky", ""),
                "dodavatel":           info.get("dodavatel", ""),
                "odkaz":               info.get("odkaz", ""),
                "koeficient_material": info.get("koeficient_material", 0),
                "koeficient_prace":    info.get("koeficient_prace", 1),
                "nakup_materialu":     info.get("nakup_materialu", 0),
                "cena_prace":          info.get("cena_prace", 0),
                "pocet_prace":         info.get("pocet_prace", 1),
                "pocet_materialu":     info.get("pocet_materialu", 1),
                "sync_qty":            info.get("sync_qty", False)
            })
        out["items"].append(sec_obj)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Chyba pri ukladaní", f"Nepodarilo sa uložiť súbor:\n{e}")
        return False

def load_basket(project_path, project_name, file_path=None):
    """
    Load the most recent basket JSON (or a specified file). Returns (OrderedDict, saved_user_name).
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
                "jednotky":            p.get("jednotky", ""),
                "dodavatel":           p.get("dodavatel", ""),
                "odkaz":               p.get("odkaz", ""),
                "koeficient_material": float(p.get("koeficient_material", 0)),
                "koeficient_prace":    float(p.get("koeficient_prace", 1)),
                "nakup_materialu":     float(p.get("nakup_materialu", 0)),
                "cena_prace":          float(p.get("cena_prace", 0)),
                "pocet_prace":         int(p.get("pocet_prace", 1)),
                "pocet_materialu":     int(p.get("pocet_materialu", 1)),
                "sync_qty":           bool(p.get("sync_qty", False)),
            }
        basket_items[section] = prods

    return basket_items, data.get("user_name","")

def show_error(msg):
    """Utility to pop up an error and return an empty list so callers can bail."""
    messagebox.showerror("Chyba", msg)
    return []

# ─── Filtering / Tree Population ────────────────────────────────────────────

def remove_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree):
    """
    Load products from 'produkty', filter by selected class_ids and search text.
    Populate `tree` (a ttk.Treeview) with grouped rows.
    """
    sel_ids = [cid for cid, var in table_vars.items() if var.get()]
    name_f = remove_accents(name_entry.get().strip().lower())

    query = """
    SELECT
      p.produkt,
      p.jednotky,
      p.dodavatel,
      p.odkaz,
      p.koeficient_material,
      p.nakup_materialu,
      p.cena_prace,
      p.koeficient_prace,
      pc.class_id
    FROM produkty p
    LEFT JOIN produkt_class pc
      ON p.id = pc.produkt_id
    WHERE 1=1
    """
    params = []
    if sel_ids:
        placeholder = ",".join("?" if db_type=="sqlite" else "%s" for _ in sel_ids)
        query += f" AND pc.class_id IN ({placeholder})"
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

    cnames = {}
    try:
        cursor.execute("SELECT id, nazov_tabulky FROM public.class")
        for cid, nm in cursor.fetchall():
            cnames[cid] = nm
    except:
        pass

    row_idx = 0
    for cid in sorted(grouped):
        header = cnames.get(cid, "Uncategorized")
        tree.insert("", "end", values=("", f"-- {header} --"), tags=("header",))
        for row in grouped[cid]:
            tag = "even" if row_idx % 2 == 0 else "odd"
            # row has 8 columns: (produkt, jednotky, dodavatel, odkaz, koef_mat, nakup_mat, cena_prace, koef_prace)
            tree.insert("", "end", values=row + (header,), tags=(tag,))
            row_idx += 1
    tree.tag_configure(
        "header",
        font=("Arial", 10, "bold"),
        background="#e0f7fa",
        foreground="#006064"
    )
    tree.tag_configure("even", background="#f9f9f9")
    tree.tag_configure("odd", background="#ffffff")

# ─── Basket Table Updaters ─────────────────────────────────────────────────

def remove_from_basket(basket_tree, basket: Basket):
    """Remove selected rows/sections and refresh the tree."""
    basket.remove_selection(basket_tree)
    basket.update_tree(basket_tree)

def update_basket_table(basket_tree, basket: Basket):
    """Repopulate the treeview from the Basket object."""
    basket.update_tree(basket_tree)

def add_to_basket_full(
    item,
    basket: Basket,
    conn,
    cursor,
    db_type,
    basket_tree,
    mark_modified,
    *,
    rec_k=3,
    from_recommendation=False,
    base_product_id=None,
):
    """
    Add a single product row (8 columns + optional section) into `basket_items`.
    Also update co-occurrence and recommendations in the database,
    but do NOT auto-add any recommended items to the basket.

    1) If the product (item) is not already in its section, insert it.
    2) Update the co_occurrence table (count pairs with existing basket items).
    3) Recompute the top‐K recommendations for this product and overwrite
       the `recommendations` table. (But do not insert those recs here.)
    4) Refresh the basket_tree and mark the basket as modified.
    """
    # Now item has length 9: last element is the “section” string
    produkt, jednotky, dodavatel, odkaz, \
    koef_mat, nakup_mat, cena_prace, koef_prace = item[:8]
    section = item[8] if len(item) > 8 and item[8] is not None else "Uncategorized"

    added = basket.add_item(item, section)
    if added:
        basket.update_tree(basket_tree)
        mark_modified()

    ensure_recommendation_schema(cursor, db_type)

    # ─── Retrieve this product’s ID from the `produkty` table ─────────
    try:
        if db_type == "postgres":
            cursor.execute(
                "SELECT id FROM produkty WHERE produkt = %s",
                (produkt,)
            )
        else:
            cursor.execute(
                "SELECT id FROM produkty WHERE produkt = ?",
                (produkt,)
            )
        base_id_row = cursor.fetchone()
    except Exception:
        base_id_row = None

    if not base_id_row:
        return  # product not found → skip co-occurrence & recommendations

    base_id = base_id_row[0]

    # ─── Update co-occurrence counts ───────────────────────────
    other_product_names = [
        p_name
        for sec_name, prod_dict in basket.items.items()
        for p_name in prod_dict.keys()
        if p_name != produkt
    ]
    other_product_names = list(set(other_product_names))

    for other_name in other_product_names:
        try:
            if db_type == "postgres":
                cursor.execute(
                    "SELECT id FROM produkty WHERE produkt = %s",
                    (other_name,)
                )
            else:
                cursor.execute(
                    "SELECT id FROM produkty WHERE produkt = ?",
                    (other_name,)
                )
            other_id_row = cursor.fetchone()
        except Exception:
            other_id_row = None

        if not other_id_row:
            continue
        other_id = other_id_row[0]

        # Upsert for (base_id, other_id) and (other_id, base_id)
        if db_type == "postgres":
            cursor.execute(
                """
                INSERT INTO co_occurrence (base_product_id, co_product_id, count, last_updated)
                VALUES (%s, %s, 1, NOW())
                ON CONFLICT (base_product_id, co_product_id)
                DO UPDATE SET count = co_occurrence.count + 1, last_updated = NOW()
                """,
                (base_id, other_id)
            )
            cursor.execute(
                """
                INSERT INTO co_occurrence (base_product_id, co_product_id, count, last_updated)
                VALUES (%s, %s, 1, NOW())
                ON CONFLICT (base_product_id, co_product_id)
                DO UPDATE SET count = co_occurrence.count + 1, last_updated = NOW()
                """,
                (other_id, base_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO co_occurrence (base_product_id, co_product_id, count, last_updated)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(base_product_id, co_product_id)
                DO UPDATE SET count = count + 1, last_updated = CURRENT_TIMESTAMP
                """,
                (base_id, other_id)
            )
            cursor.execute(
                """
                INSERT INTO co_occurrence (base_product_id, co_product_id, count, last_updated)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(base_product_id, co_product_id)
                DO UPDATE SET count = count + 1, last_updated = CURRENT_TIMESTAMP
                """,
                (other_id, base_id)
            )

    try:
        conn.commit()
    except Exception:
        pass

    # ─── Compute top-K recommendations ─────────────────────────────
    K = rec_k
    try:
        if db_type == "postgres":
            cursor.execute(
                """
                SELECT
                  co_product_id,
                  count * 1.0 / (1 + EXTRACT(EPOCH FROM (now() - last_updated))/86400) AS score
                FROM co_occurrence
                WHERE base_product_id = %s
                ORDER BY score DESC
                LIMIT %s
                """,
                (base_id, K)
            )
        else:
            cursor.execute(
                """
                SELECT
                  co_product_id,
                  count * 1.0 / (1 + (strftime('%s','now') - strftime('%s', last_updated))/86400.0) AS score
                FROM co_occurrence
                WHERE base_product_id = ?
                ORDER BY score DESC
                LIMIT ?
                """,
                (base_id, K)
            )
        top_co = cursor.fetchall()
    except Exception:
        top_co = []

    # ─── Overwrite recommendations for this base_id ─────────────────
    try:
        if db_type == "postgres":
            cursor.execute(
                "DELETE FROM recommendations WHERE base_product_id = %s",
                (base_id,)
            )
        else:
            cursor.execute(
                "DELETE FROM recommendations WHERE base_product_id = ?",
                (base_id,)
            )
    except Exception:
        pass

    for rec_id, score in top_co:
        try:
            if db_type == "postgres":
                cursor.execute(
                    """
                    INSERT INTO recommendations (
                        base_product_id,
                        recommended_product_id,
                        priority
                    ) VALUES (%s, %s, %s)
                    ON CONFLICT (base_product_id, recommended_product_id)
                    DO UPDATE SET priority = EXCLUDED.priority
                    """,
                    (base_id, rec_id, score)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO recommendations (
                        base_product_id,
                        recommended_product_id,
                        priority
                    ) VALUES (?, ?, ?)
                    ON CONFLICT(base_product_id, recommended_product_id)
                    DO UPDATE SET priority = excluded.priority
                    """,
                    (base_id, rec_id, score)
                )
        except Exception:
            pass

    try:
        conn.commit()
    except Exception:
        pass

    if from_recommendation and base_product_id is not None:
        try:
            log_recommendation_feedback(cursor, db_type, base_product_id, base_id, "accepted")
            conn.commit()
        except Exception:
            pass

    return

def reorder_basket_data(basket_tree, basket: Basket):
    """Pull edits from the Treeview back into the Basket object."""
    basket.reorder_from_tree(basket_tree)

def update_excel_from_basket(basket: Basket, project_name, definicia_text=""):
    """
    Otvorí dialógové okno na výber miesta uloženia a vytvorí Excel súbor.
    """
    if not basket.items:
        messagebox.showwarning("Košík je prázdny", "⚠ Nie sú vybraté žiadne položky na export.")
        return

    excel_data = []
    for section, products in basket.items.items():
        for produkt, v in products.items():
            excel_data.append((
                section,
                produkt,
                v.jednotky,
                v.dodavatel,
                v.odkaz,
                v.koeficient_material,
                v.koeficient_prace,
                v.nakup_materialu,
                v.cena_prace,
                v.pocet_materialu,
                v.pocet_prace,
            ))

    update_excel(excel_data, project_name, definicia_text=definicia_text)


def recompute_total_spolu(basket: Basket, total_spolu_var):
    """Recalculate the basket total and update ``total_spolu_var``."""
    total = basket.recompute_total()
    total_spolu_var.set(f"Spolu: {total:.2f}")

def apply_global_coefficient(basket: Basket, basket_tree, total_spolu_var, mark_modified):
    """
    Prompt for a new coefficient value, then override every item's
    koeficient_material and koeficient_prace to exactly that value.
    Store originals in base_coeffs on first use to allow revert.
    """
    if not basket.items:
        messagebox.showinfo("Info", "Košík je prázdny.")
        return

    factor = simpledialog.askfloat(
        "Nastaviť koeficient",
        "Zadaj novú hodnotu koeficientu (napr. 1.25):",
        minvalue=0.0
    )
    if factor is None:
        return  # user cancelled

    if not basket.base_coeffs:
        for section, products in basket.items.items():
            for pname, info in products.items():
                basket.base_coeffs[(section, pname)] = (
                    float(info.koeficient_material),
                    float(info.koeficient_prace)
                )

    basket.apply_global_coefficient(factor)
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var)
    mark_modified()

def revert_coefficient(basket: Basket, basket_tree, total_spolu_var, mark_modified):
    """
    Revert all coefficients to their originals from base_coeffs, then clear base_coeffs.
    """
    if not basket.base_coeffs:
        messagebox.showinfo("Info", "Žiadne pôvodné koeficienty nie sú uložené.")
        return

    basket.revert_coefficient()
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var)
    mark_modified()

def reset_item(iid, basket_tree, basket: Basket, total_spolu_var, mark_modified):
    """
    Reset a single item’s numeric fields back to their original values.
    """
    sec = basket_tree.parent(iid)
    if not sec:
        return
    prod = basket_tree.item(iid)["values"][0]
    section_name = basket_tree.item(sec, 'text')
    basket.reset_item(section_name, prod)
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var)
    mark_modified()

def add_custom_item(basket_tree, basket: Basket,
                    total_spolu_var, mark_modified):
    """
    Open a popup window to fill in a new item’s details, then add it into the basket.
    """
    sel = basket_tree.focus()
    if not sel:
        section = "Uncategorized"
    else:
        parent = basket_tree.parent(sel)
        if parent == "":
            section = basket_tree.item(sel, "text")
        else:
            section = basket_tree.item(parent, "text")

    if section not in basket.items:
        basket.items[section] = OrderedDict()

    popup = tk.Toplevel()
    popup.title("Nová položka")
    popup.transient()
    popup.grab_set()

    labels = [
        "Produkt",
        "Jednotky",
        "Dodavatel",
        "Odkaz",
        "Koeficient materiál",
        "Nákup mater.",
        "Koeficient práca",
        "Cena práca",
        "Pocet materiálu",
        "Pocet práce"
    ]
    entries = {}
    for i, lbl in enumerate(labels):
        tk.Label(popup, text=lbl).grid(row=i, column=0, sticky="e", padx=5, pady=2)
        ent = tk.Entry(popup, width=30)
        ent.grid(row=i, column=1, sticky="w", padx=5, pady=2)
        entries[lbl] = ent

    entries["Koeficient materiál"].insert(0, "1.0")
    entries["Nákup mater."].insert(0, "0.0")
    entries["Koeficient práca"].insert(0, "1.0")
    entries["Cena práca"].insert(0, "0.0")
    entries["Pocet materiálu"].insert(0, "1")
    entries["Pocet práce"].insert(0, "1")

    def on_ok():
        prod_name = entries["Produkt"].get().strip()
        if not prod_name:
            messagebox.showerror("Chyba", "Produkt nemôže byť prázdny.", parent=popup)
            return
        try:
            jednotky = entries["Jednotky"].get().strip()
            dodavatel = entries["Dodavatel"].get().strip()
            odkaz = entries["Odkaz"].get().strip()
            koef_mat = float(entries["Koeficient materiál"].get())
            nakup_mat = float(entries["Nákup mater."].get())
            koef_pr = float(entries["Koeficient práca"].get())
            cena_pr = float(entries["Cena práca"].get())
            poc_mat = int(entries["Pocet materiálu"].get())
            poc_pr = int(entries["Pocet práce"].get())
        except ValueError:
            messagebox.showerror("Chyba", "Skontroluj číselné hodnoty.", parent=popup)
            return

        name = prod_name
        counter = 1
        while name in basket.items[section]:
            counter += 1
            name = f"{prod_name} ({counter})"

        data = BasketItem(
            jednotky=jednotky,
            dodavatel=dodavatel,
            odkaz=odkaz,
            koeficient_material=koef_mat,
            nakup_materialu=nakup_mat,
            koeficient_prace=koef_pr,
            cena_prace=cena_pr,
            pocet_materialu=poc_mat,
            pocet_prace=poc_pr,
        )
        basket.items[section][name] = data
        basket.original.setdefault(section, OrderedDict())[name] = copy.deepcopy(data)

        basket.update_tree(basket_tree)
        recompute_total_spolu(basket, total_spolu_var)
        mark_modified()
        popup.destroy()

    def on_cancel():
        popup.destroy()

    btn_frame = tk.Frame(popup)
    btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)
    tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Zrušiť", width=10, command=on_cancel).pack(side="left", padx=5)

    popup.wait_window()

def show_notes_popup(project_name, json_dir):
    """
    Create (and place) a notes popup. Loading/saving from notes_<project>.txt.
    """
    notes_path = os.path.join(json_dir, f"notes_{project_name}.txt")
    notes_window = tk.Toplevel()
    notes_window.title("Poznámky")
    notes_window.geometry("400x300")
    notes_text = tk.Text(notes_window, wrap="word")
    notes_text.pack(fill="both", expand=True)

    if os.path.exists(notes_path):
        try:
            with open(notes_path, "r", encoding="utf-8") as f:
                notes_text.insert("1.0", f.read())
        except Exception as e:
            messagebox.showerror("Chyba pri načítaní", f"Nepodarilo sa načítať poznámky:{e}")

    def save_notes():
        try:
            with open(notes_path, "w", encoding="utf-8") as f:
                f.write(notes_text.get("1.0", "end-1c"))
        except Exception as e:
            messagebox.showerror("Chyba pri ukladaní", f"Nepodarilo sa uložiť poznámky:{e}")
        notes_window.destroy()

    notes_window.protocol("WM_DELETE_WINDOW", save_notes)
    notes_window.transient()
    notes_window.grab_set()
    notes_window.wait_window()



def fetch_recommendations_async(
    conn,
    cursor,
    db_type,
    base_product_name,
    basket: Basket,
    root,
    recom_tree,
    max_recs=3
):
    """
    1) Immediately clear `recom_tree` and insert a “Loading…” row.
    2) Spawn a background thread that:
       a) Looks up `base_id` from `produkty` WHERE `produkt = base_product_name`.
       b) Runs a single JOIN + GROUP BY query on `recommendations → produkty → class` 
          to fetch up to `max_recs` distinct products (produkt, jednotky, dodavatel, odkaz, 
          koeficient_material, nakup_materialu, cena_prace, koeficient_prace, section_name).
       c) Filters out any row whose (section_name, produkt) is already in `basket`.
       d) Calls `root.after(0, lambda: update_recommendation_tree(recom_tree, filtered_list))`.
    """
    # 1) Show “Loading…” placeholder in the Treeview
    recom_tree.delete(*recom_tree.get_children())
    recom_tree.insert(
        "",
        "end",
        values=("Loading recommendations…",) + ("",) * 8 + ("",)
        # We must supply 10 empty slots when inserting: 9 visible columns + 1 hidden "_section"
    )

    def _worker():
        # If using SQLite, create a fresh cursor per thread (sqlite3 is not threadsafe on same cursor):
        if db_type == "sqlite":
            thread_cursor = conn.cursor()
        else:
            # For Postgres, you can either reuse `cursor` or create a new one via conn.cursor()
            thread_cursor = cursor

        # ─────────────────────────────────────────────────────────────────────
        # 2a) Look up base_id from produkty WHERE produkt = base_product_name
        try:
            if db_type == "sqlite":
                thread_cursor.execute(
                    "SELECT id FROM produkty WHERE produkt = ?",
                    (base_product_name,)
                )
            else:
                thread_cursor.execute(
                    "SELECT id FROM produkty WHERE produkt = %s",
                    (base_product_name,)
                )
            row = thread_cursor.fetchone()
            if not row:
                # No such product found → update Treeview with empty list
                root.after(0, lambda: update_recommendation_tree(recom_tree, []))
                return
            base_id = row[0]
            root.after(0, lambda: setattr(recom_tree, "base_product_id", base_id))
        except Exception:
            # On any error, just clear the recommendations
            root.after(0, lambda: update_recommendation_tree(recom_tree, []))
            return

        # ─────────────────────────────────────────────────────────────────────
        # 2b) Single JOIN + GROUP BY query: pull all rec fields + "one" section_name per product
        try:
            if db_type == "sqlite":
                thread_cursor.execute("""
                    SELECT
                      p.produkt,
                      MAX(r.priority) AS score,
                      p.jednotky,
                      p.dodavatel,
                      p.odkaz,
                      p.koeficient_material,
                      p.nakup_materialu,
                      p.cena_prace,
                      p.koeficient_prace,
                      COALESCE(MIN(c.nazov_tabulky), 'Uncategorized') AS section_name
                    FROM recommendations r
                    JOIN produkty p
                      ON r.recommended_product_id = p.id
                    LEFT JOIN produkt_class pc
                      ON p.id = pc.produkt_id
                    LEFT JOIN class c
                      ON pc.class_id = c.id
                    WHERE r.base_product_id = ?
                    GROUP BY
                      p.id,
                      p.produkt,
                      p.jednotky,
                      p.dodavatel,
                      p.odkaz,
                      p.koeficient_material,
                      p.nakup_materialu,
                      p.cena_prace,
                      p.koeficient_prace
                    ORDER BY score DESC
                    LIMIT ?
                """, (base_id, max_recs))
            else:
                # PostgreSQL version uses %s placeholders
                thread_cursor.execute("""
                    SELECT
                      p.produkt,
                      MAX(r.priority) AS score,
                      p.jednotky,
                      p.dodavatel,
                      p.odkaz,
                      p.koeficient_material,
                      p.nakup_materialu,
                      p.cena_prace,
                      p.koeficient_prace,
                      COALESCE(MIN(c.nazov_tabulky), 'Uncategorized') AS section_name
                    FROM recommendations r
                    JOIN produkty p
                      ON r.recommended_product_id = p.id
                    LEFT JOIN produkt_class pc
                      ON p.id = pc.produkt_id
                    LEFT JOIN class c
                      ON pc.class_id = c.id
                    WHERE r.base_product_id = %s
                    GROUP BY
                      p.id,
                      p.produkt,
                      p.jednotky,
                      p.dodavatel,
                      p.odkaz,
                      p.koeficient_material,
                      p.nakup_materialu,
                      p.cena_prace,
                      p.koeficient_prace
                    ORDER BY score DESC
                    LIMIT %s
                """, (base_id, max_recs))
            all_recs = thread_cursor.fetchall()
        except Exception:
            all_recs = []

        # ─────────────────────────────────────────────────────────────────────
        # 2c) Filter out anything already in the basket
        filtered_recs = []
        for rec in all_recs:
            if len(rec) < 10:
                print(f"⚠️ Skipping malformed recommendation: {rec}")
                continue

            produkt_name = rec[0]
            section_name = rec[9]
            if section_name in basket.items and produkt_name in basket.items[section_name]:
                continue
            filtered_recs.append(rec)

        # ─────────────────────────────────────────────────────────────────────
        # 2d) Hand off to main thread to update the Treeview
        root.after(0, lambda: update_recommendation_tree(recom_tree, filtered_recs))

    # 3) Fire off the background thread (daemon=True so it won't block on exit)
    threading.Thread(target=_worker, daemon=True).start()


def update_recommendation_tree(recom_tree, rec_list):
    """
    Clear `recom_tree` and insert each tuple in `rec_list` as a new row.
    Each rec tuple must have exactly 10 columns:
      ( produkt, score, jednotky, dodavatel, odkaz,
        koeficient_material, nakup_materialu,
        cena_prace, koeficient_prace, section_name )

    We ignore the last element when displaying, but it is stored so that
    add_to_basket_full(...) uses that correct section.
    """
    # 1) Clear existing rows
    recom_tree.delete(*recom_tree.get_children())

    # 2) Insert each rec: values = rec (all 10 fields)
    for rec in rec_list:
        # If section name is missing (only 9 elements), append empty string
        if len(rec) == 9:
            rec = rec + ("",)
        elif len(rec) < 9:
            continue  # skip malformed row

        recom_tree.insert("", "end", values=rec)


def show_all_recommendations_popup(root, basket: Basket, conn, cursor, db_type,
                                   basket_tree, mark_modified, max_recs=20):
    """Open a window listing aggregated recommendations for all basket items."""
    ensure_recommendation_schema(cursor, db_type)

    product_names = [
        pname
        for section, prods in basket.items.items()
        for pname in prods.keys()
    ]
    if not product_names:
        messagebox.showinfo("Odporučené", "Košík je prázdny")
        return

    placeholders = ",".join(["%s" if db_type == "postgres" else "?" for _ in product_names])
    try:
        cursor.execute(
            f"SELECT id, produkt FROM produkty WHERE produkt IN ({placeholders})",
            tuple(product_names),
        )
        rows = cursor.fetchall()
        id_list = [row[0] for row in rows]
    except Exception:
        id_list = []

    if not id_list:
        messagebox.showinfo("Odporučené", "Nepodarilo sa získať odporúčania")
        return

    id_placeholders = ",".join(["%s" if db_type == "postgres" else "?" for _ in id_list])
    try:
        cursor.execute(
            f"""
            SELECT
              p.produkt,
              SUM(r.priority) AS score,
              p.jednotky,
              p.dodavatel,
              p.odkaz,
              p.koeficient_material,
              p.nakup_materialu,
              p.cena_prace,
              p.koeficient_prace,
              COALESCE(MIN(c.nazov_tabulky), 'Uncategorized') AS section_name
            FROM recommendations r
            JOIN produkty p ON r.recommended_product_id = p.id
            LEFT JOIN produkt_class pc ON p.id = pc.produkt_id
            LEFT JOIN class c ON pc.class_id = c.id
            WHERE r.base_product_id IN ({id_placeholders})
            GROUP BY p.id, p.produkt, p.jednotky, p.dodavatel, p.odkaz,
                     p.koeficient_material, p.nakup_materialu,
                     p.cena_prace, p.koeficient_prace
            ORDER BY score DESC
            LIMIT {max_recs}
            """,
            tuple(id_list),
        )
        recs = cursor.fetchall()
    except Exception:
        recs = []

    filtered = []
    for rec in recs:
        if len(rec) < 10:
            continue
        pname = rec[0]
        section = rec[9]
        if section in basket.items and pname in basket.items[section]:
            continue
        filtered.append(rec)

    win = tk.Toplevel(root)
    win.title("Odporučené položky")

    scroll_y = ttk.Scrollbar(win, orient="vertical")
    scroll_y.pack(side="right", fill="y")

    columns = (
        "produkt",
        "score",
        "jednotky",
        "dodavatel",
        "odkaz",
        "koeficient_material",
        "nakup_materialu",
        "cena_prace",
        "koeficient_prace",
        "_section",
    )
    visible = columns[:-1]

    tree = ttk.Treeview(
        win,
        columns=columns,
        show="headings",
        displaycolumns=visible,
        yscrollcommand=scroll_y.set,
        height=min(15, len(filtered) + 1),
    )
    for c in visible:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="center", stretch=True)
    tree.heading("_section", text="")
    tree.column("_section", width=0, stretch=False)
    tree.pack(fill="both", expand=True)
    scroll_y.config(command=tree.yview)

    for rec in filtered:
        tree.insert("", "end", values=rec)

    tree.bind(
        "<Double-1>",
        lambda e: add_to_basket_full(
            tree.item(tree.focus())["values"],
            basket,
            conn,
            cursor,
            db_type,
            basket_tree,
            mark_modified,
            from_recommendation=True,
        ),
    )

    win.transient(root)
    win.grab_set()
    win.wait_window()
