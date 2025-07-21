# gui_functions.py

import socket
import os
import sqlite3
import psycopg2
import decimal
import tkinter as tk
from tkinter import messagebox, simpledialog
import unicodedata
from collections import OrderedDict
import copy

from basket import Basket, BasketItem

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


# ─── Basket Persistence / I/O ────────────────────────────────────────────────


def show_error(msg):
    """Utility to pop up an error and return an empty list so callers can bail."""
    messagebox.showerror("Chyba", msg)
    return []

# ─── Filtering / Tree Population ────────────────────────────────────────────

def remove_accents(s):
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

def update_excel_from_basket(basket: Basket, project_name, json_dir, definicia_text=""):
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
    notes_path = os.path.join(json_dir, f"notes_{project_name}.txt")
    notes_lines = []
    if os.path.exists(notes_path):
        try:
            with open(notes_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if "|" in line:
                        state, text = line.split("|", 1)
                        if state == "1":
                            notes_lines.append(text)
        except Exception:
            pass

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

def apply_global_coefficient(basket: Basket, basket_tree, total_spolu_var,
                             mark_modified,
                             total_praca_var=None, total_material_var=None):
    """
    Prompt for a new coefficient value, then override every item's
    koeficient_material and koeficient_prace to exactly that value.
    Store originals in base_coeffs on first use to allow revert.
    """
    if not basket.items:
        messagebox.showinfo("Info", "Košík je prázdny.")
        return

    factor = askfloat_locale(
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
    recompute_total_spolu(basket, total_spolu_var,
                          total_praca_var, total_material_var)
    mark_modified()

def revert_coefficient(basket: Basket, basket_tree, total_spolu_var,
                       mark_modified,
                       total_praca_var=None, total_material_var=None):
    """
    Revert all coefficients to their originals from base_coeffs, then clear base_coeffs.
    """
    if not basket.base_coeffs:
        messagebox.showinfo("Info", "Žiadne pôvodné koeficienty nie sú uložené.")
        return

    basket.revert_coefficient()
    basket.update_tree(basket_tree)
    recompute_total_spolu(basket, total_spolu_var,
                          total_praca_var, total_material_var)
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

def show_notes_popup(project_name, json_dir):
    """Open a popup with checkable notes for the given project."""
    notes_path = os.path.join(json_dir, f"notes_{project_name}.txt")

    default_items = [
        "Záručná doba na pasívne časti systému (kabeláž, rozvádzače, konektory) je 60mesiacov.",
        "Záručná doba na aktívne zariadenia je 24mesiacov.",
        "Záručná doba na batérie a napájacie zdroje je 12mesiacov.",
        "Stavebná pripravenosť stien, stropov, podláh a iných stavebných konštrukcií nie je predmetom riešenia cenovej ponuky",
        "V cenovej ponuke je zahrnutá výhradne základná konfigurácia, test a oživenie zariadení. Dodatočné nastavenia špeciálnych požiadaviek budú spoplatnené sumou 50€/hod.",
        "Množstvo kabeláže a inštalačného materiálu je orientačné, faktúrovaná bude ich skutočná spotreba.",
        "Tento dokument je duševným vlastníctvom autorov a podlieha autorskému zákonu.",
        "O termíne ukončenia inštalačných prác je nutné informovať sa po záväznom objednaní (doba bude určena podľa aktuálne dostupných kapacít technikov).",
        "Pre uplatnenie si záruky je objednávateľ povinný vyzvať spol. LAST MILE spol. s r.o. k predloženiu plánu pravidelných servisných prehliadok.",
        "Platnosť cenovej ponuky: dd.mm.rrrr",
    ]

    items = []
    if os.path.exists(notes_path):
        try:
            with open(notes_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if "|" in line:
                        state, text = line.split("|", 1)
                        items.append((int(state), text))
        except Exception:
            items = [(0, t) for t in default_items]

    if not items:
        items = [(0, t) for t in default_items]

    notes_window = tk.Toplevel()
    notes_window.title("Poznámky")
    notes_window.geometry("420x340")

    frame = tk.Frame(notes_window)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    vars_items = []

    def create_note(text, checked=True):
        var = tk.IntVar(value=1 if checked else 0)
        chk = tk.Checkbutton(
            frame,
            text=text,
            variable=var,
            anchor="w",
            justify="left",
            wraplength=380,
        )
        chk.pack(anchor="w", fill="x", pady=2)
        vars_items.append((var, text))

    for state, text in items:
        create_note(text, checked=bool(state))

    # Entry field to allow adding custom notes
    add_frame = tk.Frame(notes_window)
    add_frame.pack(fill="x", padx=10, pady=(0, 10))

    new_note_var = tk.StringVar()
    new_note_entry = tk.Entry(add_frame, textvariable=new_note_var)
    new_note_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    def add_custom_note():
        text = new_note_var.get().strip()
        if not text:
            return
        create_note(text)
        new_note_var.set("")

    def add_custom_note_dialog():
        text = simpledialog.askstring(
            "Add Custom Note",
            "Enter note text:",
            parent=notes_window,
        )
        if text:
            create_note(text.strip())

    add_btn = tk.Button(add_frame, text="Pridať", command=add_custom_note)
    add_btn.pack(side="left")

    add_popup_btn = tk.Button(add_frame, text="Add custom notes", command=add_custom_note_dialog)
    add_popup_btn.pack(side="left", padx=(5, 0))

    def save_notes():
        try:
            with open(notes_path, "w", encoding="utf-8") as f:
                for var, text in vars_items:
                    f.write(f"{var.get()}|{text}\n")
        except Exception as e:
            messagebox.showerror("Chyba pri ukladaní", f"Nepodarilo sa uložiť poznámky:{e}")
        notes_window.destroy()

    notes_window.protocol("WM_DELETE_WINDOW", save_notes)
    notes_window.transient()
    notes_window.grab_set()
    notes_window.wait_window()



