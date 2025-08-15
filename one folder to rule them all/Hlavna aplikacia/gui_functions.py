# gui_functions.py

import socket
import os
import sqlite3
import psycopg2
import decimal
import tkinter as tk
from tkinter import messagebox
import unicodedata
from collections import OrderedDict
import copy
import json
import tkinter.ttk as ttk
from basket import Basket, BasketItem
from types import SimpleNamespace

# Keep track of open notes widgets so we can grab the latest values
NOTES_UI_STATE: dict[str, list[tuple[tk.IntVar, object]]] = {}
# Cache of notes that were saved from the popup but not yet written to disk
UNSAVED_NOTES: dict[str, list[dict[str, object]]] = {}

from helpers import (
    parse_float,
    askfloat_locale,
    format_currency,
)
from excel_processing import update_excel

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

def ensure_indexes(sqlite_conn: sqlite3.Connection) -> None:
    """Create indexes to speed up common filters.

    Safe to call multiple times thanks to ``IF NOT EXISTS``.
    """
    cur = sqlite_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_produkty_name ON produkty(produkt)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_produkt_class_pid ON produkt_class(produkt_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_produkt_class_cid ON produkt_class(class_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_recommendations_pid ON recommendations(produkt_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_recommendations_rid ON recommendations(recommended_id)"
    )
    sqlite_conn.commit()

def sync_postgres_to_sqlite(pg_conn):
    """
    Pull key tables from Postgres into ``local_backup.db`` so the application
    can run in offline mode. Existing tables are dropped and recreated.
    """
    sqlite_conn   = sqlite3.connect("local_backup.db")
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor     = pg_conn.cursor()

    # ── 1) Sync produkty ────────────────────────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS produkty")
    sqlite_cursor.execute(
        """
        CREATE TABLE produkty (
            id INTEGER PRIMARY KEY,
            produkt TEXT,
            jednotky TEXT,
            dodavatel TEXT,
            odkaz TEXT,
            koeficient_material REAL,
            koeficient_prace REAL,
            nakup_materialu REAL,
            cena_prace REAL,
            product_type_id INTEGER
        )
        """
    )
    pg_cursor.execute(
        """
        SELECT
          id, produkt, jednotky, dodavatel, odkaz,
          koeficient_material, koeficient_prace,
          nakup_materialu, cena_prace,
          product_type_id
        FROM produkty
        """
    )
    prod_rows = pg_cursor.fetchall()
    cleaned = [
        tuple(float(col) if isinstance(col, decimal.Decimal) else col
              for col in row)
        for row in prod_rows
    ]
    sqlite_cursor.executemany(
        "INSERT INTO produkty VALUES (?,?,?,?,?,?,?,?,?,?)",
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

    # ── 4) Sync recommendations ──────────────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS recommendations")
    sqlite_cursor.execute(
        """
        CREATE TABLE recommendations (
            produkt_id INTEGER,
            recommended_id INTEGER
        )
        """
    )
    try:
        pg_cursor.execute("SELECT produkt_id, recommended_id FROM recommendations")
        rec_rows = pg_cursor.fetchall()
        sqlite_cursor.executemany(
            "INSERT INTO recommendations VALUES (?,?)",
            rec_rows
        )
    except Exception as e:
        print("Warning: failed to sync recommendations:", e)
    # ── 5) Sync product_type ────────────────────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS product_type")
    sqlite_cursor.execute(
        """
        CREATE TABLE product_type (
            id INTEGER PRIMARY KEY,
            code TEXT
        )
        """
    )
    pg_cursor.execute("SELECT id, code FROM public.product_type")
    pt_rows = pg_cursor.fetchall()
    sqlite_cursor.executemany("INSERT INTO product_type VALUES (?,?)", pt_rows)

    # ── 6) Sync product_type_dependency ────────────────────────────────────
    sqlite_cursor.execute("DROP TABLE IF EXISTS product_type_dependency")
    sqlite_cursor.execute(
        """
        CREATE TABLE product_type_dependency (
            id INTEGER PRIMARY KEY,
            parent_type_id INTEGER,
            child_type_id INTEGER,
            note TEXT
        )
        """
    )
    pg_cursor.execute(
        "SELECT id, parent_type_id, child_type_id, note FROM public.product_type_dependency"
    )
    ptd_rows = pg_cursor.fetchall()
    sqlite_cursor.executemany(
        "INSERT INTO product_type_dependency VALUES (?,?,?,?)",
        ptd_rows,
    )

    sqlite_conn.commit()
    ensure_indexes(sqlite_conn)
    sqlite_conn.close()
    print("✔ Synced PostgreSQL → SQLite (produkty, class, produkt_class, recommendations, product_type, product_type_dependency)")


# ─── Basket Persistence / I/O ────────────────────────────────────────────────


def show_error(msg):
    """Utility to pop up an error and return an empty list so callers can bail."""
    messagebox.showerror("Chyba", msg)
    return []

# ─── Filtering / Tree Population ────────────────────────────────────────────

def remove_accents(s):
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree):
    """
    Load products from ``produkty`` and filter them by the selected class IDs
    and the search term entered in ``name_entry``. The filtered results are
    grouped by table and displayed in ``tree``.
    """

    # Determine which tables are checked and build the search filter
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
        placeholder = ",".join("?" if db_type == "sqlite" else "%s" for _ in sel_ids)
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

    records = []
    row_idx = 0
    for cid in sorted(grouped):
        header = cnames.get(cid, "Uncategorized")
        records.append((("", f"-- {header} --"), ("header",)))
        for row in grouped[cid]:
            tag = "even" if row_idx % 2 == 0 else "odd"
            records.append((row + (header,), (tag,)))
            row_idx += 1

    def insert_chunk(start: int = 0, batch: int = 500):
        end = start + batch
        for vals, tags in records[start:end]:
            tree.insert("", "end", values=vals, tags=tags)
        if end < len(records):
            tree.after(0, lambda: insert_chunk(end, batch))

    insert_chunk()
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
    total_spolu_var,
    total_praca_var=None,
    total_material_var=None,
):
    """
    Add a single product row (8 columns + optional section) into ``basket`` and
    Refresh ``basket_tree`` and update totals when a product is added.
    """
    produkt, jednotky, dodavatel, odkaz, \
        koef_mat, nakup_mat, cena_prace, koef_prace = item[:8]
    section = item[8] if len(item) > 8 and item[8] is not None else "Uncategorized"

    added = basket.add_item(item, section)
    if added:
        basket.update_tree(basket_tree)
        recompute_total_spolu(basket, total_spolu_var,
                              total_praca_var, total_material_var)
        mark_modified()



def reorder_basket_data(basket_tree, basket: Basket):
    """Pull edits from the Treeview back into the Basket object."""
    basket.reorder_from_tree(basket_tree)

def update_excel_from_basket(basket: Basket, project_name, json_path, definicia_text=""):
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

    # Load checked notes if available
    notes_lines = []
    for n in get_current_notes(project_name, json_path):
        if int(n.get("state", 0)) == 1:
            notes_lines.append(n.get("text", ""))

    notes_text = "\n".join(notes_lines) if notes_lines else ""

    update_excel(
        excel_data,
        project_name,
        notes_text=notes_text,
        definicia_text=definicia_text,
    )


def recompute_total_spolu(basket: Basket, total_spolu_var,
                          total_praca_var=None, total_material_var=None):
    """Recalculate totals and update the provided StringVars."""
    mat_total, praca_total, total = basket.recompute_totals()
    total_spolu_var.set(f"Spolu: {format_currency(total)}")
    if total_praca_var is not None:
        total_praca_var.set(f"Spolu práca: {format_currency(praca_total)}")
    if total_material_var is not None:
        total_material_var.set(f"Spolu materiál: {format_currency(mat_total)}")

def apply_global_coefficient(
    basket: Basket,
    basket_tree,
    total_spolu_var,
    mark_modified,
    total_praca_var=None,
    total_material_var=None,
):
    """Prompt for a coefficient and apply it to both material and work."""
    if not basket.items:
        messagebox.showinfo("Info", "Košík je prázdny.")
        return

    factor = askfloat_locale(
        "Nastaviť koeficient",
        "Zadaj novú hodnotu koeficientu (napr. 1.25):",
        minvalue=0.0,
    )
    if factor is None:
        return

    basket.apply_global_coefficient(factor)
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
    mark_modified()

def apply_material_coefficient(
    basket: Basket,
    basket_tree,
    total_spolu_var,
    mark_modified,
    total_praca_var=None,
    total_material_var=None,
):
    """Prompt for a coefficient and apply it only to material."""
    if not basket.items:
        messagebox.showinfo("Info", "Košík je prázdny.")
        return

    factor = askfloat_locale(
        "Nastaviť koeficient materiál",
        "Zadaj novú hodnotu koeficientu (napr. 1.25):",
        minvalue=0.0,
    )
    if factor is None:
        return

    basket.apply_material_coefficient(factor)
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
    mark_modified()

def apply_work_coefficient(
    basket: Basket,
    basket_tree,
    total_spolu_var,
    mark_modified,
    total_praca_var=None,
    total_material_var=None,
):
    """Prompt for a coefficient and apply it only to work."""
    if not basket.items:
        messagebox.showinfo("Info", "Košík je prázdny.")
        return

    factor = askfloat_locale(
        "Nastaviť koeficient práca",
        "Zadaj novú hodnotu koeficientu (napr. 1.25):",
        minvalue=0.0,
    )
    if factor is None:
        return

    basket.apply_work_coefficient(factor)
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
    mark_modified()

def revert_coefficient(
    basket: Basket,
    basket_tree,
    total_spolu_var,
    mark_modified,
    total_praca_var=None,
    total_material_var=None,
):
    """Revert both material and work coefficients to their originals."""
    if not basket.base_coeffs_material and not basket.base_coeffs_work:
        messagebox.showinfo("Info", "Žiadne pôvodné koeficienty nie sú uložené.")
        return

    basket.revert_coefficient()
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
    mark_modified()

def revert_material_coefficient(
    basket: Basket,
    basket_tree,
    total_spolu_var,
    mark_modified,
    total_praca_var=None,
    total_material_var=None,
):
    """Revert only material coefficients to stored originals."""
    if not basket.base_coeffs_material:
        messagebox.showinfo("Info", "Žiadne pôvodné koeficienty nie sú uložené.")
        return

    basket.revert_material_coefficient()
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
    mark_modified()

def revert_work_coefficient(
    basket: Basket,
    basket_tree,
    total_spolu_var,
    mark_modified,
    total_praca_var=None,
    total_material_var=None,
):
    """Revert only work coefficients to stored originals."""
    if not basket.base_coeffs_work:
        messagebox.showinfo("Info", "Žiadne pôvodné koeficienty nie sú uložené.")
        return

    basket.revert_work_coefficient()
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
    mark_modified()

def reset_item(iid, basket_tree, basket: Basket,
               total_spolu_var, mark_modified,
               total_praca_var=None, total_material_var=None):
    """
    Reset a single item’s numeric fields back to their original values.
    """
    reset_items(
        [iid],
        basket_tree,
        basket,
        total_spolu_var,
        mark_modified,
        total_praca_var,
        total_material_var,
    )


def reset_items(iids, basket_tree, basket: Basket,
                total_spolu_var, mark_modified,
                total_praca_var=None, total_material_var=None):
    """Reset multiple items back to their original values."""
    changed = False
    for iid in iids:
        sec = basket_tree.parent(iid)
        if not sec:
            continue
        prod = basket_tree.item(iid)["values"][0]
        section_name = basket_tree.item(sec, "text")
        basket.reset_item(section_name, prod)
        changed = True
    if changed:
        basket.update_tree(basket_tree)
        recompute_total_spolu(
            basket,
            total_spolu_var,
            total_praca_var,
            total_material_var,
        )
        mark_modified()

def add_custom_item(basket_tree, basket: Basket,
                    total_spolu_var, mark_modified,
                    total_praca_var=None, total_material_var=None):
    """
    Open a popup window to fill in a new item’s details, then add it into the basket.
    Styled with a warning (orange) theme.
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
        basket.snapshot()
        basket.items[section] = OrderedDict()

    popup = tk.Toplevel()
    popup.title("⚠️ Nová položka (UPOZORNENIE)")
    popup.transient()
    popup.grab_set()
    popup.configure(bg="#FFF4E5")  # svetlá oranžová

    header = tk.Label(popup, text="⚠️ Zadajte údaje o novej položke", font=("Arial", 14, "bold"),
                      bg="#FFD580", fg="#663300", pady=10)
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

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
    for i, lbl in enumerate(labels, start=1):
        tk.Label(popup, text=lbl + ":", bg="#FFF4E5", anchor="e", width=20).grid(row=i, column=0, sticky="e", padx=5, pady=2)
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
            koef_mat = parse_float(entries["Koeficient materiál"].get())
            nakup_mat = parse_float(entries["Nákup mater."].get())
            koef_pr = parse_float(entries["Koeficient práca"].get())
            cena_pr = parse_float(entries["Cena práca"].get())
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

        basket.snapshot()

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
        recompute_total_spolu(basket, total_spolu_var,
                              total_praca_var, total_material_var)
        mark_modified()
        popup.destroy()

    def on_cancel():
        popup.destroy()

    btn_frame = tk.Frame(popup, bg="#FFF4E5")
    btn_frame.grid(row=len(labels) + 1, column=0, columnspan=2, pady=10)

    tk.Button(btn_frame, text="✅ OK", bg="#FFA500", fg="white", font=("Arial", 10, "bold"),
              width=12, command=on_ok).pack(side="left", padx=5)
    tk.Button(btn_frame, text="❌ Zrušiť", bg="#CC6600", fg="white", font=("Arial", 10, "bold"),
              width=12, command=on_cancel).pack(side="left", padx=5)

    popup.wait_window()

def show_notes_popup(project_name, json_path):
    """Open a popup with checkable notes for the given project."""
    items = []
    if project_name in UNSAVED_NOTES:
        for n in UNSAVED_NOTES[project_name]:
            text = n.get("text", "")
            if text:
                items.append((int(n.get("state", 0)), text))
    elif os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                for n in data.get("notes", []):
                    text = n.get("text", "")
                    if text:
                        items.append((int(n.get("state", 0)), text))
        except Exception:
            items = []

    default_items = [
        "Záručná doba na pasívne časti systému (kabeláž, rozvádzače, konektory) je 60mesiacov.",
        "Záručná doba na aktívne zariadenia je 24mesiacov.",
        "Záručná doba na batérie a napájacie zdroje je 12mesiacov.",
        "Stavebná pripravenosť stien, stropov, podláh a iných stavebných konštrukcií nie je predmetom riešenia cenovej ponuky",
        "V cenovej ponuke je zahrnutá výhradne základná konfigurácia, test a oživenie zariadení.",
        "Množstvo kabeláže a inštalačného materiálu je orientačné, faktúrovaná bude ich skutočná spotreba.",
        "Tento dokument je duševným vlastníctvom autorov a podlieha autorskému zákonu.",
        "O termíne ukončenia inštalačných prác je nutné informovať sa po záväznom objednaní.",
        "Pre uplatnenie si záruky je objednávateľ povinný vyzvať spol. LAST MILE spol. s r.o. k servisu.",
        "Platnosť cenovej ponuky: dd.mm.rrrr",
    ]

    if not items:
        items = [(0, t) for t in default_items]

    notes_window = tk.Toplevel()
    notes_window.title("Poznámky")
    notes_window.geometry("450x400")

    main_frame = tk.Frame(notes_window)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(main_frame)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    def _on_mousewheel(event):
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

    scrollable_frame.bind(
        "<Enter>",
        lambda e: (
            canvas.bind_all("<MouseWheel>", _on_mousewheel),
            canvas.bind_all("<Button-4>", _on_mousewheel),
            canvas.bind_all("<Button-5>", _on_mousewheel),
        )
    )
    scrollable_frame.bind(
        "<Leave>",
        lambda e: (
            canvas.unbind_all("<MouseWheel>"),
            canvas.unbind_all("<Button-4>"),
            canvas.unbind_all("<Button-5>"),
        )
    )

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    vars_items = []
    NOTES_UI_STATE[project_name] = vars_items

    def move_up(frame):
        idx = next((i for i, (_, _, f) in enumerate(vars_items) if f is frame), None)
        if idx is None or idx == 0:
            return
        vars_items[idx], vars_items[idx-1] = vars_items[idx-1], vars_items[idx]
        frame.pack_forget()
        frame.pack(before=vars_items[idx][2])

    def move_down(frame):
        idx = next((i for i, (_, _, f) in enumerate(vars_items) if f is frame), None)
        if idx is None or idx == len(vars_items) - 1:
            return
        vars_items[idx], vars_items[idx+1] = vars_items[idx+1], vars_items[idx]
        frame.pack_forget()
        frame.pack(after=vars_items[idx][2])

    def create_note(text, checked=True, editable=False):
        var = tk.IntVar(value=1 if checked else 0)
        row = tk.Frame(scrollable_frame)
        row.pack(fill="x", pady=2)

        if editable:
            entry = tk.Entry(row, width=50)
            entry.insert(0, text)
            entry.pack(side="left", fill="x", expand=True)
            chk = tk.Checkbutton(row, variable=var)
            chk.pack(side="left", padx=5)
            text_widget = entry
        else:
            chk = tk.Checkbutton(
                row, text=text, variable=var,
                anchor="w", justify="left", wraplength=400
            )
            chk.pack(side="left", fill="x", expand=True)
            text_widget = text

        tk.Button(row, text="↑", width=2, command=lambda f=row: move_up(f)).pack(side="left")
        tk.Button(row, text="↓", width=2, command=lambda f=row: move_down(f)).pack(side="left")

        vars_items.append((var, text_widget, row))

    for state, text in items:
        create_note(text, checked=bool(state))

    # Buttons
    btn_frame = tk.Frame(notes_window)
    btn_frame.pack(fill="x", padx=10, pady=(10, 5))

    def add_empty_note():
        create_note("", checked=True, editable=True)

    def _save_to_cache():
        notes_data = []
        for var, text, _ in vars_items:
            if isinstance(text, tk.Entry):
                t = text.get().strip()
            else:
                t = text.strip()
            if t:
                notes_data.append({"state": int(var.get()), "text": t})
        UNSAVED_NOTES[project_name] = notes_data

    def save_notes():
        try:
            _save_to_cache()
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodarilo sa uložiť poznámky: {e}")
        notes_window.destroy()
        NOTES_UI_STATE.pop(project_name, None)

    def on_close():
        """Close notes window without saving."""
        notes_window.destroy()

    tk.Button(btn_frame, text="➕ Pridať prázdnu poznámku", command=add_empty_note).pack(side="left", padx=5)
    tk.Button(btn_frame, text="✅ Uložiť a zatvoriť", command=save_notes).pack(side="right", padx=5)

    notes_window.protocol("WM_DELETE_WINDOW", on_close)
    notes_window.transient()
    notes_window.grab_set()
    notes_window.wait_window()


def get_current_notes(project_name, json_path):
    """Return a list of note dictionaries currently in the UI or saved on disk."""
    vars_items = NOTES_UI_STATE.get(project_name)
    if vars_items is not None:
        notes = []
        for var, text, _ in vars_items:
            if isinstance(text, tk.Entry):
                t = text.get().strip()
            else:
                t = text.strip()
            if t:
                notes.append({"state": int(var.get()), "text": t})
        UNSAVED_NOTES[project_name] = notes
        return notes

    if project_name in UNSAVED_NOTES:
        return UNSAVED_NOTES[project_name]

    notes = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                for n in data.get("notes", []):
                    text = n.get("text", "")
                    if text:
                        notes.append({"state": int(n.get("state", 0)), "text": text})
        except Exception:
            notes = []
    return notes


def show_recommendations_popup(
    cursor,
    db_type,
    produkt_name,
    basket,
    conn,
    basket_tree,
    mark_modified,
    total_spolu_var,
    total_praca_var=None,
    total_material_var=None,
    filter_ids=None,
):
    """Display recommended products for the given produkt name.

    ``basket`` and related parameters are used so that a double-click on a row
    immediately inserts the product into the basket. ``filter_ids`` can be a
    sequence of selected class IDs to further filter the recommendations.
    """
    placeholder = "?" if db_type == "sqlite" else "%s"
    try:
        cursor.execute(
            f"""
            SELECT r.recommended_id
            FROM recommendations r
            JOIN produkty p ON p.id = r.produkt_id
            WHERE p.produkt = {placeholder}
            """,
            (produkt_name,),
        )
        ids = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        messagebox.showerror("Chyba", str(e))
        return

    if not ids:
        messagebox.showinfo("Odporučené produkty", "Pre tento produkt nie sú odporúčania.")
        return

    ph = ",".join([placeholder] * len(ids))
    params = list(ids)
    query = f"""
        SELECT p.produkt, p.jednotky, p.dodavatel, p.odkaz,
               p.koeficient_material, p.nakup_materialu,
               p.cena_prace, p.koeficient_prace,
               MIN(c.nazov_tabulky)
        FROM produkty p
        LEFT JOIN produkt_class pc ON p.id = pc.produkt_id
        LEFT JOIN class c ON pc.class_id = c.id
        WHERE p.id IN ({ph})
        GROUP BY p.id
    """
    if filter_ids:
        ph2 = ",".join([placeholder] * len(filter_ids))
        query += f" AND pc.class_id IN ({ph2})"
        params.extend(filter_ids)
    try:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Chyba", str(e))
        return

    win = tk.Toplevel()
    win.title("Odporučené produkty")

    # Store all product info and display all columns
    cols = (
        "produkt",
        "jednotky",
        "dodavatel",
        "odkaz",
        "koeficient_material",
        "nakup_materialu",
        "cena_prace",
        "koeficient_prace",
        "section",
    )
    display_cols = cols
    tree = ttk.Treeview(win, columns=cols, show="headings", displaycolumns=display_cols)
    for c in display_cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="center")

    # Normalize rows to include the section name (last column)
    normalized = [
        row[:8] + (row[8] if row[8] else "Uncategorized",)
        for row in rows
    ]
    for idx, row in enumerate(normalized):
        tag = "even" if idx % 2 == 0 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))

    tree.tag_configure("even", background="#f9f9f9")
    tree.tag_configure("odd", background="#ffffff")

    def on_double_click(event):
        sel = tree.focus()
        if not sel:
            return
        vals = tree.item(sel)["values"]
        if not vals:
            return
        add_to_basket_full(
            vals,
            basket,
            conn,
            cursor,
            db_type,
            basket_tree,
            mark_modified,
            total_spolu_var,
            total_praca_var,
            total_material_var,
        )

    tree.bind("<Double-1>", on_double_click)

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def adjust_cols(event):
        total = event.width
        proportions = {
            "produkt":             0.22,
            "jednotky":            0.15,
            "dodavatel":           0.12,
            "odkaz":               0.20,
            "koeficient_material": 0.10,
            "nakup_materialu":     0.13,
            "cena_prace":          0.08,
            "koeficient_prace":    0.08,
        }
        total_pct = sum(proportions.get(c, 0) for c in display_cols)
        if total_pct == 0:
            total_pct = len(display_cols)
        for c in display_cols:
            pct = proportions.get(c, 1 / len(display_cols))
            width = int(total * pct / total_pct)
            tree.column(c, width=width, stretch=True)

    tree.bind("<Configure>", adjust_cols)
    win.update_idletasks()
    adjust_cols(SimpleNamespace(width=tree.winfo_width()))

    tk.Button(win, text="Zatvoriť", command=win.destroy).pack(pady=5)
    win.geometry("1000x450")
    win.transient()
    win.grab_set()
    win.wait_window()



def check_type_dependencies(
    basket: Basket,
    cursor,
    conn,
    db_type,
    basket_tree,
    mark_modified,
    total_spolu_var,
    total_praca_var=None,
    total_material_var=None,
):
    """Suggest required product types missing from the basket."""

    names = [prod for products in basket.items.values() for prod in products.keys()]
    if not names:
        messagebox.showinfo("Kontrola", "Košík je prázdny.")
        return

    placeholder = ",".join("?" if db_type == "sqlite" else "%s" for _ in names)
    produkty_table = "public.produkty" if db_type != "sqlite" else "produkty"
    dependency_table = (
        "public.product_type_dependency" if db_type != "sqlite" else "product_type_dependency"
    )
    type_table = "public.product_type" if db_type != "sqlite" else "product_type"

    try:
        cursor.execute(
            f"""
            SELECT DISTINCT product_type_id
            FROM {produkty_table}
            WHERE produkt IN ({placeholder}) AND product_type_id IS NOT NULL
            """,
            tuple(names),
        )
        current_types = {row[0] for row in cursor.fetchall()}
    except Exception as e:
        messagebox.showerror("Chyba", str(e))
        return

    if not current_types:
        messagebox.showinfo("Kontrola", "Všetko v poriadku ✓")
        return

    ph = ",".join("?" if db_type == "sqlite" else "%s" for _ in current_types)
    try:
        cursor.execute(
            f"""
            SELECT DISTINCT child_type_id
            FROM {dependency_table}
            WHERE parent_type_id IN ({ph})
            """,
            tuple(current_types),
        )
        required_types = {row[0] for row in cursor.fetchall()}
    except Exception as e:
        messagebox.showerror("Chyba", str(e))
        return

    missing_types = required_types - current_types
    if not missing_types:
        messagebox.showinfo("Kontrola", "Všetko v poriadku ✓")
        return

    ph = ",".join("?" if db_type == "sqlite" else "%s" for _ in missing_types)
    try:
        cursor.execute(
            f"SELECT id, code FROM {type_table} WHERE id IN ({ph})",
            tuple(missing_types),
        )
        type_codes = dict(cursor.fetchall())
    except Exception:
        type_codes = {}
    win = tk.Toplevel()
    win.title("Chýbajúce typy")

    ph = "?" if db_type == "sqlite" else "%s"
    rows = []
    for t_id in sorted(missing_types):
        try:
            cursor.execute(
                f"""
                SELECT p.produkt, p.jednotky, p.dodavatel, p.odkaz,
                       p.koeficient_material, p.nakup_materialu,
                       p.cena_prace, p.koeficient_prace,
                       MIN(c.nazov_tabulky)
                FROM {produkty_table} p
                LEFT JOIN produkt_class pc ON p.id = pc.produkt_id
                LEFT JOIN class c ON pc.class_id = c.id
                WHERE p.product_type_id = {ph}
                GROUP BY p.id
                ORDER BY p.produkt
                """,
                (t_id,),
            )
            prod_rows = cursor.fetchall()
        except Exception:
            prod_rows = []
        for r in prod_rows:
            rows.append(r + (type_codes.get(t_id, str(t_id)),))

    if not rows:
        messagebox.showinfo("Kontrola", "Pre chýbajúce typy nie sú dostupné produkty.")
        return

    cols = (
        "produkt",
        "jednotky",
        "dodavatel",
        "odkaz",
        "koeficient_material",
        "nakup_materialu",
        "cena_prace",
        "koeficient_prace",
        "section",
        "type",
    )
    tree = ttk.Treeview(win, columns=cols, show="headings", displaycolumns=cols)
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="center")

    normalized = [
        row[:8] + (row[8] if row[8] else "Uncategorized", row[9])
        for row in rows
    ]
    for idx, row in enumerate(normalized):
        tag = "even" if idx % 2 == 0 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))

    tree.tag_configure("even", background="#f9f9f9")
    tree.tag_configure("odd", background="#ffffff")

    def on_double_click(event):
        sel = tree.focus()
        if not sel:
            return
        vals = tree.item(sel)["values"]
        if not vals:
            return
        add_to_basket_full(
            vals[:-1],
            basket,
            conn,
            cursor,
            db_type,
            basket_tree,
            mark_modified,
            total_spolu_var,
            total_praca_var,
            total_material_var,
        )

    tree.bind("<Double-1>", on_double_click)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add_all():
        for row in normalized:
            add_to_basket_full(
                row[:-1],
                basket,
                conn,
                cursor,
                db_type,
                basket_tree,
                mark_modified,
                total_spolu_var,
                total_praca_var,
                total_material_var,
            )
        win.destroy()

    tk.Button(win, text="Pridať všetko", command=add_all).pack(pady=5)
    win.transient()
    win.grab_set()
    win.wait_window()
