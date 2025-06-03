import sys
import os
import subprocess
import copy
from collections import OrderedDict
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap import Style
import tkinter as tk
from tkinter import messagebox, simpledialog
import tkinter.ttk as ttk
import json
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
    update_excel_from_basket,
    remove_from_basket
)

def start(project_dir, json_path):
    """
    Entrypoint for the GUI.
    project_dir: folder containing launcher.exe and this gui.py
    json_path:   full path to the selected projects/<name>.json
    """
    # ─── Prepare paths
    project_name = os.path.basename(project_dir)
    json_dir     = os.path.join(project_dir, "projects")
    commit_file  = json_path

    # ─── Database setup
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    if db_type == "postgres":
        sync_postgres_to_sqlite(conn)

    # ─── Themed Window
    style = Style(theme="litera")
    root  = style.master
    style.configure(
        "Main.Treeview.Heading",
        background="#e6e6fa",
        foreground="#006064",
        relief="flat"
    )
    style.configure(
        "Basket.Treeview.Heading",
        background="#e6e6fa",
        foreground="#006064",
        relief="flat"
    )
    root.title(f"Project: {project_name}")
    root.state("zoomed")
    root.option_add("*Font", ("Segoe UI", 10))

    # ─── Modification flag
    basket_modified = False
    def mark_modified():
        nonlocal basket_modified
        basket_modified = True

    # ─── Helpers for the database Treeview (responsive columns)
    db_column_proportions = {
        "produkt":             0.22,
        "jednotky":            0.15,
        "dodavatel":           0.12,
        "odkaz":               0.20,
        "koeficient_material": 0.10,
        "nakup_materialu":     0.13,
        "cena_prace":          0.08,
        "koeficient_prace":    0.08,
    }

    def adjust_db_columns(event):
        total = event.width
        for col, pct in db_column_proportions.items():
            tree.column(col, width=int(total * pct), stretch=True)

    # ─── Basket Table Helpers (responsive columns)
    # 1. Define basket columns (no “spolu” as a column)
    basket_columns = (
        "produkt",
        "jednotky",
        "dodavatel",
        "odkaz",
        "koeficient_material",   # user‐editable
        "nakup_materialu",       # user‐editable
        "predaj_material",       # computed
        "koeficient_prace",      # user‐editable
        "cena_prace",            # user‐editable
        "predaj_praca",          # computed
        "pocet_materialu",       # user‐editable
        "pocet_prace"            # user‐editable
    )

    # 2. Assign a weight to each column for proportional resizing
    basket_column_proportions = {
        "produkt":             0.13,
        "jednotky":            0.07,
        "dodavatel":           0.12,
        "odkaz":               0.16,
        "koeficient_material": 0.07,
        "nakup_materialu":     0.07,
        "predaj_material":     0.07,
        "koeficient_prace":    0.07,
        "cena_prace":          0.07,
        "predaj_praca":        0.07,
        "pocet_materialu":     0.07,
        "pocet_prace":         0.07,
    }

    def adjust_visible_basket_columns(event=None):
        """
        Recompute widths for only the currently visible columns, so they fill the Treeview width.
        """
        total_width = basket_tree.winfo_width()
        if total_width <= 0:
            return

        # Reserve a small, fixed width for the "expand/collapse" icon (#0).
        icon_width = max(int(total_width * 0.11), 20)
        basket_tree.column("#0", width=icon_width, anchor="w", stretch=False)

        available = max(total_width - icon_width, 100)

        # Determine which columns are currently visible
        visible_cols = basket_tree.cget("displaycolumns")
        if isinstance(visible_cols, str):
            visible_cols = (visible_cols,)

        # Sum weights only for visible columns
        sum_weights = sum(basket_column_proportions[col] for col in visible_cols)

        # Distribute available width proportionally among visible columns
        for col in visible_cols:
            weight = basket_column_proportions[col]
            pct = weight / sum_weights
            basket_tree.column(col, width=int(available * pct), stretch=True)

    # ─── Placeholder for column_vars, will be populated after basket_tree is created
    column_vars = {}

    def update_displayed_columns():
        """
        Update the set of displaycolumns based on which checkboxes are checked,
        then immediately recalculate column widths.
        """
        visible = [col for col, var in column_vars.items() if var.get()]
        if not visible:
            # Force at least "produkt" if all boxes get unchecked
            visible = ["produkt"]
            column_vars["produkt"].set(True)

        basket_tree.config(displaycolumns=visible)
        adjust_visible_basket_columns()

    # ─── StringVar to hold the grand total “spolu”
    total_spolu_var = tk.StringVar(value="Spolu: 0.00")

    def recompute_total_spolu():
        """
        Walk through basket_items and sum (predaj_material + predaj_praca) for each product.
        Update total_spolu_var accordingly.
        """
        total = 0.0
        for section, products in basket_items.items():
            for pname, info in products.items():
                koef_mat = float(info.get("koeficient_material", 0))
                nakup_mat = float(info.get("nakup_materialu", 0))
                predaj_mat = nakup_mat * koef_mat

                koef_pr = float(info.get("koeficient_prace", 1))
                cena_pr = float(info.get("cena_prace", 0))
                predaj_pr = cena_pr * koef_pr

                total += (predaj_mat + predaj_pr)
        total_spolu_var.set(f"Spolu: {total:.2f}")

    def update_basket_table(basket_tree, basket_items):
        """
        Clear and repopulate the basket Treeview from basket_items.
        Compute derived fields on the fly and then call recompute_total_spolu().
        """
        basket_tree.delete(*basket_tree.get_children())
        for section, products in basket_items.items():
            sec_id = basket_tree.insert("", "end", text=section, open=True)
            for produkt, d in products.items():
                # Compute derived columns
                koef_mat = float(d.get("koeficient_material", 0))
                nakup_mat = float(d.get("nakup_materialu", 0))
                predaj_mat = nakup_mat * koef_mat

                koef_pr = float(d.get("koeficient_prace", 1))
                cena_pr = float(d.get("cena_prace", 0))
                predaj_pr = cena_pr * koef_pr

                basket_tree.insert(
                    sec_id, "end", text="",
                    values=(
                        produkt,
                        d.get("jednotky", ""),
                        d.get("dodavatel", ""),
                        d.get("odkaz", ""),
                        koef_mat,
                        nakup_mat,
                        predaj_mat,
                        koef_pr,
                        cena_pr,
                        predaj_pr,
                        int(d.get("pocet_materialu", 1)),
                        int(d.get("pocet_prace", 1))
                    )
                )
        # Update total “spolu”
        recompute_total_spolu()

    def reorder_basket_data():
        """
        After edits in the Treeview, pull everything back into basket_items.
        Only user‐editable fields are saved; derived fields are recalculated later.
        """
        new_basket = OrderedDict()
        for sec in basket_tree.get_children(""):
            sec_name = basket_tree.item(sec, "text")
            prods = OrderedDict()
            for child in basket_tree.get_children(sec):
                vals = basket_tree.item(child, "values")
                # Indices in basket_columns:
                # 0: produkt
                # 1: jednotky
                # 2: dodavatel
                # 3: odkaz
                # 4: koeficient_material
                # 5: nakup_materialu
                # 6: predaj_material (computed - skip)
                # 7: koeficient_prace
                # 8: cena_prace
                # 9: predaj_praca (computed - skip)
                # 10: pocet_materialu
                # 11: pocet_prace
                prods[vals[0]] = {
                    "jednotky":            vals[1],
                    "dodavatel":           vals[2],
                    "odkaz":               vals[3],
                    "koeficient_material": float(vals[4]),
                    "nakup_materialu":     float(vals[5]),
                    "koeficient_prace":    float(vals[7]),
                    "cena_prace":          float(vals[8]),
                    "pocet_materialu":     int(vals[10]),
                    "pocet_prace":         int(vals[11])
                }
            new_basket[sec_name] = prods
        basket_items.clear()
        basket_items.update(new_basket)

    # ─── For global coefficient adjustment:
    # Store original coefficients once, so we can revert later.
    base_coeffs = {}

    def apply_global_coefficient():
        """
        Prompt for a new coefficient value, then override every item's
        koeficient_material and koeficient_prace to exactly that value.
        Store originals in base_coeffs on first use to allow revert.
        """
        if not basket_items:
            messagebox.showinfo("Info", "Košík je prázdny.", parent=root)
            return

        factor = simpledialog.askfloat(
            "Nastaviť koeficient",
            "Zadaj novú hodnotu koeficientu (napr. 1.25):",
            minvalue=0.0,
            parent=root
        )
        if factor is None:
            return  # user cancelled

        # On first apply, save original coefficients
        if not base_coeffs:
            for section, products in basket_items.items():
                for pname, info in products.items():
                    base_coeffs[(section, pname)] = (
                        float(info.get("koeficient_material", 1.0)),
                        float(info.get("koeficient_prace", 1.0))
                    )

        # Override each to exactly `factor`
        for section, products in basket_items.items():
            for pname, info in products.items():
                info["koeficient_material"] = factor
                info["koeficient_prace"]    = factor

        update_basket_table(basket_tree, basket_items)
        mark_modified()

    def revert_coefficient():
        """
        Revert all coefficients to their originals from base_coeffs, then clear base_coeffs.
        """
        if not base_coeffs:
            messagebox.showinfo("Info", "Žiadne pôvodné koeficienty nie sú uložené.", parent=root)
            return

        for (section, pname), (orig_mat, orig_pr) in base_coeffs.items():
            if section in basket_items and pname in basket_items[section]:
                basket_items[section][pname]["koeficient_material"] = orig_mat
                basket_items[section][pname]["koeficient_prace"]    = orig_pr

        base_coeffs.clear()
        update_basket_table(basket_tree, basket_items)
        mark_modified()

    # ─── Define add_to_basket *before* binding it on the DB tree
    def add_to_basket(item):
        produkt, jednotky, dodavatel, odkaz, \
        koef_mat, nakup_mat, cena_prace, koef_prace = item[:8]
        section = item[8] if len(item) > 8 and item[8] is not None else "Uncategorized"

        # ─── (A) Add or increment in the in-memory basket ─────────────────────────
        data = {
            "jednotky":            jednotky,
            "dodavatel":           dodavatel,
            "odkaz":               odkaz,
            "koeficient_material": float(koef_mat),
            "nakup_materialu":     float(nakup_mat),
            "koeficient_prace":    float(koef_prace),
            "cena_prace":          float(cena_prace),
            "pocet_materialu":     1,
            "pocet_prace":         1
        }
        if section not in basket_items:
            basket_items[section] = OrderedDict()
        if produkt in basket_items[section]:
            basket_items[section][produkt]["pocet_materialu"] += 1
            basket_items[section][produkt]["pocet_prace"]    += 1
        else:
            basket_items[section][produkt] = data
            original_basket.setdefault(section, OrderedDict())[produkt] = copy.deepcopy(data)

        update_basket_table(basket_tree, basket_items)
        mark_modified()
        # ──────────────────────────────────────────────────────────────────────────

        # ─── (B) Lookup this product’s ID from the `produkty` table ────────────────
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
            # If the product is not found in the database, exit early
            return

        base_id = base_id_row[0]

        # ─── (C) Update co_occurrence counts for each other product in the basket ───
        # 1) Collect all other product names currently in the basket (excluding the newly added one)
        other_product_names = []
        for sec_name, prod_dict in basket_items.items():
            for p_name in prod_dict.keys():
                if p_name != produkt:
                    other_product_names.append(p_name)
        other_product_names = list(set(other_product_names))

        # 2) For each other product, lookup its ID and upsert co_occurrence both ways
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

            # Upsert (base_id, other_id)
            if db_type == "postgres":
                cursor.execute(
                    """
                    INSERT INTO co_occurrence (base_product_id, co_product_id, count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (base_product_id, co_product_id)
                    DO UPDATE SET count = co_occurrence.count + 1
                    """,
                    (base_id, other_id)
                )
                # Upsert (other_id, base_id)
                cursor.execute(
                    """
                    INSERT INTO co_occurrence (base_product_id, co_product_id, count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (base_product_id, co_product_id)
                    DO UPDATE SET count = co_occurrence.count + 1
                    """,
                    (other_id, base_id)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO co_occurrence (base_product_id, co_product_id, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(base_product_id, co_product_id)
                    DO UPDATE SET count = count + 1
                    """,
                    (base_id, other_id)
                )
                # Upsert (other_id, base_id)
                cursor.execute(
                    """
                    INSERT INTO co_occurrence (base_product_id, co_product_id, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(base_product_id, co_product_id)
                    DO UPDATE SET count = count + 1
                    """,
                    (other_id, base_id)
                )

        # Commit co_occurrence updates
        try:
            conn.commit()
        except Exception:
            pass

        # ─── (D) Rebuild `recommendations` entries for this base_id ──────────────────
        # 1) Delete any old recommendations for base_id
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

        # 2) Fetch the top K co-occurring products for base_id
        K = 3
        try:
            if db_type == "postgres":
                cursor.execute(
                    """
                    SELECT co_product_id, count
                    FROM co_occurrence
                    WHERE base_product_id = %s
                    ORDER BY count DESC
                    LIMIT %s
                    """,
                    (base_id, K)
                )
            else:
                cursor.execute(
                    f"""
                    SELECT co_product_id, count
                    FROM co_occurrence
                    WHERE base_product_id = ?
                    ORDER BY count DESC
                    LIMIT {K}
                    """,
                    (base_id,)
                )
            top_co = cursor.fetchall()  # List of (other_id, count)
        except Exception:
            top_co = []

        # 3) Insert those top co-occurring products into `recommendations` with priority=count
        for rec_id, cnt in top_co:
            try:
                if db_type == "postgres":
                    cursor.execute(
                        """
                        INSERT INTO recommendations (
                            base_product_id,
                            recommended_product_id,
                            priority
                        ) VALUES (%s, %s, %s)
                        """,
                        (base_id, rec_id, cnt)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO recommendations (
                            base_product_id,
                            recommended_product_id,
                            priority
                        ) VALUES (?, ?, ?)
                        """,
                        (base_id, rec_id, cnt)
                    )
            except Exception:
                pass

        # Commit recommendation updates
        try:
            conn.commit()
        except Exception:
            pass

        # ─── (E) Prompt the user for each of these top recommendations ───────────────
        for rec_id, cnt in top_co:
            # 1) Lookup the suggested product’s name
            try:
                if db_type == "postgres":
                    cursor.execute(
                        "SELECT produkt FROM produkty WHERE id = %s",
                        (rec_id,)
                    )
                else:
                    cursor.execute(
                        "SELECT produkt FROM produkty WHERE id = ?",
                        (rec_id,)
                    )
                rec_name_row = cursor.fetchone()
            except Exception:
                rec_name_row = None

            if not rec_name_row:
                continue

            suggested_name = rec_name_row[0]
            ans = messagebox.askyesno(
                "Doplnkové položky",
                f"Chceli by ste k '{produkt}' pridať aj '{suggested_name}'?"
            )
            if not ans:
                continue

            # 2) User clicked “Yes” → fetch that suggested product’s full row and re-add
            try:
                if db_type == "postgres":
                    cursor.execute(
                        """
                        SELECT produkt,
                            jednotky,
                            dodavatel,
                            odkaz,
                            koeficient_material,
                            nakup_materialu,
                            cena_prace,
                            koeficient_prace,
                            NULL
                        FROM produkty
                        WHERE id = %s
                        """,
                        (rec_id,)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT produkt,
                            jednotky,
                            dodavatel,
                            odkaz,
                            koeficient_material,
                            nakup_materialu,
                            cena_prace,
                            koeficient_prace,
                            NULL
                        FROM produkty
                        WHERE id = ?
                        """,
                        (rec_id,)
                    )
                rec_item = cursor.fetchone()
            except Exception:
                rec_item = None

            if rec_item:
                add_to_basket(rec_item)
            else:
                messagebox.showwarning(
                    "Chyba",
                    f"Produkt s ID={rec_id} nebol nájdený."
                )



    # ─── Edit basket cell on double-click
    def edit_basket_cell(event):
        row = basket_tree.identify_row(event.y)
        col = basket_tree.identify_column(event.x)
        if not row or basket_tree.parent(row) == "":
            return
        idx = int(col.replace("#","")) - 1

        # Columns 6 (predaj_material) and 9 (predaj_praca) are computed → skip editing
        if idx in (6, 9):
            return

        old = basket_tree.set(row, col)
        col_name = basket_columns[idx]

        # Decide prompt type by column
        if col_name in ("pocet_materialu", "pocet_prace"):
            new = simpledialog.askinteger("Upraviť bunku", f"Nová hodnota pre '{col_name}'", initialvalue=int(old), parent=root)
        else:
            # All other editable numeric fields (floats)
            new = simpledialog.askfloat("Upraviť bunku", f"Nová hodnota pre '{col_name}'", initialvalue=float(old), parent=root)

        if new is None:
            return

        # Update the Treeview cell
        basket_tree.set(row, col, new)

        # Update the underlying basket_items dict
        sec = basket_tree.parent(row)
        prod = basket_tree.item(row)["values"][0]
        key_map = {
            1: "jednotky",
            2: "dodavatel",
            3: "odkaz",
            4: "koeficient_material",
            5: "nakup_materialu",
            7: "koeficient_prace",
            8: "cena_prace",
            10: "pocet_materialu",
            11: "pocet_prace"
        }
        if idx in key_map:
            basket_items[basket_tree.item(sec, 'text')][prod][key_map[idx]] = new

        mark_modified()
        # Recompute derived columns, redraw entire basket, and update total
        update_basket_table(basket_tree, basket_items)

    # ─── Reset logic via right-click context menu
    def reset_item(iid):
        sec = basket_tree.parent(iid)
        if not sec:
            return
        prod = basket_tree.item(iid)["values"][0]
        orig = original_basket.get(basket_tree.item(sec,'text'), {}).get(prod)
        if not orig:
            messagebox.showinfo("Chýba originál", "Pôvodné hodnoty nie sú k dispozícii.")
            return
        for k in ("koeficient_material", "nakup_materialu", "koeficient_prace", "cena_prace", "pocet_materialu", "pocet_prace"):
            basket_items[basket_tree.item(sec,'text')][prod][k] = copy.deepcopy(orig[k])

        update_basket_table(basket_tree, basket_items)
        mark_modified()

    def on_basket_right_click(event):
        iid = basket_tree.identify_row(event.y)
        if not iid or not basket_tree.parent(iid):
            return
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="Reset položky", command=lambda: reset_item(iid))
        menu.post(event.x_root, event.y_root)

    # ─── Add a new, custom item via popup
    def add_custom_item():
        """
        Open a popup window to fill in a new item’s details.
        """
        # Determine which section to put this in
        sel = basket_tree.focus()
        if not sel:
            section = "Uncategorized"
        else:
            parent = basket_tree.parent(sel)
            if parent == "":
                # A section header is selected → use that
                section = basket_tree.item(sel, "text")
            else:
                # A product row is selected → use its section
                section = basket_tree.item(parent, "text")

        # Ensure the section exists
        if section not in basket_items:
            basket_items[section] = OrderedDict()

        # Create the popup
        popup = tk.Toplevel(root)
        popup.title("Nová položka")
        popup.transient(root)
        popup.grab_set()

        # Labels and Entries for all editable fields:
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

        # Default values:
        entries["Koeficient materiál"].insert(0, "1.0")
        entries["Nákup mater."].insert(0, "0.0")
        entries["Koeficient práca"].insert(0, "1.0")
        entries["Cena práca"].insert(0, "0.0")
        entries["Pocet materiálu"].insert(0, "1")
        entries["Pocet práce"].insert(0, "1")

        def on_ok():
            # Read and validate inputs
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

            # Ensure unique product name in this section
            name = prod_name
            counter = 1
            while name in basket_items[section]:
                counter += 1
                name = f"{prod_name} ({counter})"

            data = {
                "jednotky":            jednotky,
                "dodavatel":           dodavatel,
                "odkaz":               odkaz,
                "koeficient_material": koef_mat,
                "nakup_materialu":     nakup_mat,
                "koeficient_prace":    koef_pr,
                "cena_prace":          cena_pr,
                "pocet_materialu":     poc_mat,
                "pocet_prace":         poc_pr
            }
            basket_items[section][name] = data
            original_basket.setdefault(section, OrderedDict())[name] = copy.deepcopy(data)

            update_basket_table(basket_tree, basket_items)
            mark_modified()
            popup.destroy()

        def on_cancel():
            popup.destroy()

        btn_frame = tk.Frame(popup)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Zrušiť", width=10, command=on_cancel).pack(side="left", padx=5)

        popup.wait_window()

    # ─── Return Home
    def return_home():
        if basket_modified:
            reorder_basket_data()
            save_basket(json_dir, project_name, basket_items)
        conn.close()
        root.destroy()
        subprocess.Popen([sys.executable, os.path.join(project_dir,"launcher.exe")], cwd=project_dir)

    # ─── Build UI ─────────────────────────────────────────────────────
    # Filter panel
    category_structure = {}
    cursor.execute("SELECT id,hlavna_kategoria,nazov_tabulky FROM class")
    for cid, main_cat, tablename in cursor.fetchall():
        category_structure.setdefault(main_cat, []).append((cid, tablename))
    filter_frame, setup_cat_tree, category_vars, table_vars = create_filter_panel(
        root, lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
    )
    # Increase filter panel width so it has more space
    filter_frame.config(width=350)
    filter_frame.pack(side="left", fill="y", padx=10, pady=10)
    setup_cat_tree(category_structure)

    # Main area
    main_frame = tb.Frame(root, padding=10)
    main_frame.pack(side="left", fill="both", expand=True)

    # Top bar
    top = tb.Frame(main_frame, padding=5)
    top.pack(side="top", fill="x")
    tb.Button(top, text="🏠 Home", bootstyle="light", command=return_home).pack(side="left")
    tk.Label(top, text="Vyhľadávanie:").pack(side="left", padx=(20,5))
    name_entry = tk.Entry(top, width=30)
    name_entry.pack(side="left")
    name_entry.bind("<KeyRelease>", lambda e: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree))

    # Database tree
    tree_frame = tb.Frame(main_frame)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
    db_columns = (
        "produkt",
        "jednotky",
        "dodavatel",
        "odkaz",
        "koeficient_material",
        "nakup_materialu",
        "cena_prace",
        "koeficient_prace"
    )

    tree = ttk.Treeview(tree_frame, columns=db_columns, show="headings")
    for c in db_columns:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="center", stretch=True)
    tree.pack(fill="both", expand=True)
    tree.bind("<Configure>", adjust_db_columns)
    tree.bind("<Double-1>", lambda e: add_to_basket(tree.item(tree.focus())["values"]))

    # Basket tree + Column-Toggle Controls
    basket_items = OrderedDict()
    original_basket = OrderedDict()
    basket_frame = tb.Frame(main_frame, padding=5)
    basket_frame.pack(fill="both", expand=True, padx=10, pady=10)
    tk.Label(basket_frame, text="Košík - vybraté položky:").pack(anchor="w")

    # ─── Frame of checkboxes for each basket column ─────────────────────────────
    checkbox_frame = tb.LabelFrame(basket_frame, text="Show columns:", padding=5)
    checkbox_frame.pack(fill="x", pady=(3,8))

    for col in basket_columns:
        # Default "odkaz" checkbox to off
        if col == "odkaz":
            var = tk.BooleanVar(value=False)
        else:
            var = tk.BooleanVar(value=True)
        column_vars[col] = var
        chk = tk.Checkbutton(
            checkbox_frame,
            text=col.capitalize(),
            variable=var,
            command=update_displayed_columns
        )
        chk.pack(side="left", padx=5)

    # Create the basket Treeview, initially showing all columns except "odkaz"
    initial_display = [c for c in basket_columns if c != "odkaz"]
    basket_tree = ttk.Treeview(
        basket_frame,
        columns=basket_columns,
        show="tree headings",
        displaycolumns=initial_display
    )
    basket_tree.heading("#0", text="")
    basket_tree.column("#0", width=20, anchor="w", stretch=False)
    for c in basket_columns:
        basket_tree.heading(c, text=c.capitalize())
        basket_tree.column(c, anchor="center", stretch=True)
    basket_tree.pack(fill="both", expand=True)

    # Bind resizing → recalc only visible columns
    basket_tree.bind("<Configure>", adjust_visible_basket_columns)
    basket_tree.bind("<Double-1>", edit_basket_cell)
    basket_tree.bind("<Button-3>", on_basket_right_click)

    # Drag-drop in basket
    _drag = {"item": None}
    basket_tree.bind("<ButtonPress-1>", lambda e: _drag.update({"item": basket_tree.identify_row(e.y)}))
    basket_tree.bind("<B1-Motion>", lambda e: (
        basket_tree.move(
            _drag["item"],
            basket_tree.parent(_drag["item"]),
            basket_tree.index(basket_tree.identify_row(e.y))
        ) if (_drag.get("item") and basket_tree.parent(basket_tree.identify_row(e.y)) == basket_tree.parent(_drag["item"]))
        else None
    ))
    basket_tree.bind("<ButtonRelease-1>", lambda e: _drag.update({"item": None}))

    # ─── Place the “Spolu: …” label at the bottom right of the basket_frame ───
    total_frame = tk.Frame(basket_frame)
    total_frame.pack(fill="x", pady=(2,0))
    tk.Label(total_frame, textvariable=total_spolu_var, anchor="e").pack(side="right", padx=10)

    # Notes popup button with save/load
    def show_notes_popup():
        notes_path = os.path.join(json_dir, f"notes_{project_name}.txt")
        notes_window = tk.Toplevel(root)
        notes_window.title("Poznámky")
        notes_window.geometry("400x300")
        notes_text = tk.Text(notes_window, wrap="word")
        notes_text.pack(fill="both", expand=True)

        # Load notes if file exists
        if os.path.exists(notes_path):
            try:
                with open(notes_path, "r", encoding="utf-8") as f:
                    notes_text.insert("1.0", f.read())
            except Exception as e:
                messagebox.showerror("Chyba pri načítaní", f"Nepodarilo sa načítať poznámky:{e}")

        # Save on close
        def save_notes():
            try:
                with open(notes_path, "w", encoding="utf-8") as f:
                    f.write(notes_text.get("1.0", "end-1c"))
            except Exception as e:
                messagebox.showerror("Chyba pri ukladaní", f"Nepodarilo sa uložiť poznámky:{e}")
            notes_window.destroy()

        notes_window.protocol("WM_DELETE_WINDOW", save_notes)
        notes_window.transient(root)
        notes_window.grab_set()

    tb.Button(
        basket_frame,
        text="Poznámky",
        bootstyle="secondary",
        command=show_notes_popup
    ).pack(pady=3)

    # Remove, Add & Export buttons on the left; Coefficient buttons on the right
    btn_container = tk.Frame(basket_frame)
    btn_container.pack(fill="x", pady=5)

    left_btn_frame = tk.Frame(btn_container)
    left_btn_frame.pack(side="left")

    right_btn_frame = tk.Frame(btn_container)
    right_btn_frame.pack(side="right")

    # Left‐aligned buttons: Odstrániť, Pridať, Exportovať
    tb.Button(
        left_btn_frame,
        text="Odstrániť",
        bootstyle="danger-outline",
        command=lambda: (remove_from_basket(basket_tree, basket_items, update_basket_table), mark_modified())
    ).pack(side="left", padx=(0, 10))

    tb.Button(
        left_btn_frame,
        text="Pridať",
        bootstyle="primary-outline",
        command=add_custom_item
    ).pack(side="left", padx=(0, 10))

    export_btn = tb.Button(
        left_btn_frame,
        text="Exportovať",
        bootstyle="success",
        command=lambda: (
            reorder_basket_data(),
            update_excel_from_basket(basket_items, project_name)
        )
    )
    export_btn.pack(side="left")

    # Right‐aligned buttons: Nastav koeficient, Revert koeficient
    tb.Button(
        right_btn_frame,
        text="Nastav koeficient",
        bootstyle="info-outline",
        command=apply_global_coefficient
    ).pack(side="left", padx=(0, 10))

    tb.Button(
        right_btn_frame,
        text="Revert koeficient",
        bootstyle="warning-outline",
        command=revert_coefficient
    ).pack(side="left")

    # Initial load & record originals
    basket_items_loaded, saved = load_basket(json_dir, project_name, file_path=commit_file)
    for sec, prods in basket_items_loaded.items():
        original_basket.setdefault(sec, OrderedDict()).update(copy.deepcopy(prods))
    basket_items.update(basket_items_loaded)
    update_basket_table(basket_tree, basket_items)

    # Initial filter
    apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

    # Ensure displaycolumns matches initial checkbox state and columns fill width
    update_displayed_columns()

    # Closing handler
    def on_closing():
        # 1) Confirm Save / Cancel
        resp = messagebox.askyesnocancel(
            "Uložiť zmeny?",
            "Chceš uložiť zmeny pred zatvorením košíka?"
        )
        if resp is None:
            return            # Cancel → stay open
        if resp is False:
            root.destroy()    # No → just close without saving
            return

        # 2) Make sure all in-memory edits are reflected
        reorder_basket_data()

        # 3) Ask for the base filename
        default_base = "basket"
        fname = simpledialog.askstring(
            "Košík — Uložiť ako",
            "Zadaj názov súboru (bez prípony):",
            initialvalue=default_base,
            parent=root
        )
        if not fname:
            return  # user cancelled → stay open

        # 4) Append timestamp and build the full path
        ts = datetime.now().strftime("_%Y-%m-%d")
        filename = f"{fname}{ts}.json"
        fullpath = os.path.join(json_dir, filename)

        # 5) Confirm overwrite if it already exists
        if os.path.exists(fullpath):
            if not messagebox.askyesno(
                "Prepis existujúceho súboru?",
                f"“{filename}” už existuje. Chceš ho prepísať?"
            ):
                return  # user chose not to overwrite → stay open

        # 6) Build the JSON payload from basket_items
        out = {
            "project": project_name,
            "items": []
        }
        for section, prods in basket_items.items():
            sec_obj = {"section": section, "products": []}
            for pname, info in prods.items():
                sec_obj["products"].append({
                    "produkt":              pname,
                    "jednotky":            info.get("jednotky", ""),
                    "dodavatel":           info.get("dodavatel", ""),
                    "odkaz":               info.get("odkaz", ""),
                    "koeficient_material": info.get("koeficient_material", 0),
                    "nakup_materialu":     info.get("nakup_materialu", 0),
                    "koeficient_prace":    info.get("koeficient_prace", 1),
                    "cena_prace":          info.get("cena_prace", 0),
                    "pocet_prace":         info.get("pocet_prace", 1),
                    "pocet_materialu":     info.get("pocet_materialu", 1),
                })
            out["items"].append(sec_obj)

        # 7) Write the file
        try:
            with open(fullpath, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror(
                "Chyba pri ukladaní",
                f"Nepodarilo sa uložiť súbor:\n{e}"
            )
            return

        # 8) All done → close
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
