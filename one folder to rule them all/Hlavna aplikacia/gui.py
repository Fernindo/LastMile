# gui.py

import sys
import os
import tkinter as tk
import tkinter.ttk as ttk
import ttkbootstrap as tb
import json

UI_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "ui_settings.json")

def _load_ui_settings():
    if os.path.exists(UI_SETTINGS_FILE):
        try:
            with open(UI_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_ui_settings(data):
    try:
        with open(UI_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
from datetime import datetime
import tkinter.simpledialog
from ttkbootstrap import Style
import threading
from helpers import (
    show_praca_window,
    create_filter_panel,
    askfloat_locale,
    format_currency,
    
)
from exportVv import export_vv
from exportCp import export_cp
from basket import Basket
from basket_io import load_basket
from doprava import show_doprava_window


from gui_functions import (
    get_database_connection,
    sync_postgres_to_sqlite,
    ensure_indexes,
    apply_filters,
    update_basket_table,
    add_to_basket_full,         # “silent” version, DOES NOT auto-add recs
    reorder_basket_data,
    update_excel_from_basket,
    remove_from_basket,
    recompute_total_spolu,
    apply_material_coefficient,
    apply_work_coefficient,
    revert_material_coefficient,
    revert_work_coefficient,
    reset_items,
    add_custom_item,
    show_notes_popup,
    get_current_notes,
    show_recommendations_popup,
    check_type_dependencies,
    UNSAVED_NOTES
)

from tkinter import messagebox, simpledialog

def start(project_dir, json_path, meno="", priezvisko="", username="", user_id=None):
    global CURRENT_USER
    CURRENT_USER = {
        "id": user_id,
        "meno": meno or "",
        "priezvisko": priezvisko or "",
        "username": username or ""
    }


    # ─── Prepare paths and DB ────────────────────────────────────────────
    project_name = os.path.basename(project_dir)
    json_dir     = os.path.join(project_dir, "projects")
    commit_file  = json_path

    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    if db_type == "postgres":
        sync_postgres_to_sqlite(conn)
    else:
        ensure_indexes(conn)

    # ─── Create main window via ttkbootstrap ─────────────────────────────
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

    # --- Dynamic scaling based on screen size -----------------------------
    screen_w = root.winfo_screenwidth()

    # Use a slightly smaller reference width so laptops don't scale down
    base_w = 1600
    scale = max(1.0, min(1.5, screen_w / base_w))

    

    root.tk.call("tk", "scaling", scale)

    ui_settings = _load_ui_settings()
    font_size_var = [int(ui_settings.get("table_font_size", int(10 * scale)))]
    row_h = int(2.4 * font_size_var[0])

    style.configure("Main.Treeview", rowheight=row_h, font=("Segoe UI", font_size_var[0]))
    style.configure("Basket.Treeview", rowheight=row_h, font=("Segoe UI", font_size_var[0]))
    root.title(f"Project: {project_name}")
    root.state("zoomed")
    root.option_add("*Font", ("Segoe UI", font_size_var[0]))

    root.grid_rowconfigure(0, weight=1)
    # Start with the filter hidden so the main area spans the full width
    root.grid_columnconfigure(0, weight=1)  # main content
    root.grid_columnconfigure(1, weight=0)  # placeholder for filter panel

    # ─── Track whether the basket has been modified ──────────────────────
    basket_modified = [False]  # use a list so nested functions can modify

    def mark_modified():
        basket_modified[0] = True

    def undo_action():
        if basket.undo():
            update_basket_table(basket_tree, basket)
            recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
            mark_modified()

    def redo_action():
        if basket.redo():
            update_basket_table(basket_tree, basket)
            recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
            mark_modified()

    # ─── Top-Level Frames ─────────────────────────────────────────────────
    
    main_frame   = tb.Frame(root, padding=10)
    main_frame.grid(row=0, column=0, sticky="nsew")
    
    db_visible = [True]  # Používame list kvôli mutabilite

    def toggle_db_view():
        if db_visible[0]:
            tree_frame.pack_forget()
            toggle_btn.config(text="🔼 Zobraziť databázu")
        else:
            if basket_frame.winfo_manager():
                tree_frame.pack(
                    in_=main_frame,
                    before=basket_frame,
                    fill="both",
                    expand=True,
                    padx=10,
                    pady=10,
                )
            else:
                tree_frame.pack(
                    in_=main_frame,
                    fill="both",
                    expand=True,
                    padx=10,
                    pady=10,
                )
            toggle_btn.config(text="🔽 Skryť databázu")
        db_visible[0] = not db_visible[0]

    # ─── Track whether the basket is visible ────────────────────────────
    basket_visible = [True]

    def toggle_basket_view():
        if basket_visible[0]:
            basket_frame.pack_forget()
            toggle_basket_btn.config(text="🔼 Zobraziť košík")
        else:
            basket_frame.pack(
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )
            toggle_basket_btn.config(text="🔽 Skryť košík")
        basket_visible[0] = not basket_visible[0]

    
   

    # ─── Filter Panel (left) ──────────────────────────────────────────────
    category_structure = {}
    try:
        cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
        for cid, main_cat, tablename in cursor.fetchall():
            category_structure.setdefault(main_cat, []).append((cid, tablename))
    except:
        pass

    # --- Filter panel (create + toggle) --------------------------------------
    filter_container, filter_frame, setup_cat_tree, category_vars, table_vars = create_filter_panel(
        root,
        lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
    )
    filter_container.config(width=350)

    setup_cat_tree(category_structure)

    filter_visible = [False]  # stav panelu

    def toggle_filter():
        if filter_visible[0]:
            # hide filter, expand main into column 0 and reclaim full width
            filter_container.grid_forget()
            main_frame.grid(row=0, column=0, sticky="nsew")
            root.grid_columnconfigure(0, weight=1)
            # remove extra column so main_frame truly stretches fullscreen
            root.grid_columnconfigure(1, weight=0)
            filter_toggle_btn.config(text="▶")
        else:
            # show filter in column 0, push main to column 1
            filter_container.grid(row=0, column=0, sticky="ns")
            main_frame.grid(row=0, column=1, sticky="nsew")
            root.grid_columnconfigure(0, weight=0)
            root.grid_columnconfigure(1, weight=1)
            filter_toggle_btn.config(text="◀")
        filter_visible[0] = not filter_visible[0]


    toggle_filter_container = tk.Frame(root, bg="#f0f4f8")
    toggle_filter_container.place(relx=0.0, rely=0.5, anchor="w")

    filter_toggle_btn = tk.Button(
        toggle_filter_container,
        text="▶",
        font=("Segoe UI", int(12 * scale), "bold"),
        width=2,
        height=1,
        bg="#e0e0e0",
        relief="flat",
        command=toggle_filter
    )
    filter_toggle_btn.pack()

    # ─── Main Area (right) ────────────────────────────────────────────────
    # Top bar (Home button + Search entry)
    top = tb.Frame(main_frame, padding=5)
    top.pack(side="top", fill="x")

    toggle_btn = tb.Button(
        top,
        text="🔽 Skryť databázu",
        bootstyle="seconwarningdary",
        command=toggle_db_view
    )
    toggle_btn.pack(side="left", padx=(10, 0))
    
    toggle_basket_btn = tb.Button(
    top,
    text="🔽 Skryť košík",
    bootstyle="warning",
    command=toggle_basket_view
    )
    toggle_basket_btn.pack(side="left", padx=(10, 0))


    praca_btn = tb.Button(
        top,
        text="🛠️ Práca",
        bootstyle="light",
        command=lambda: show_praca_window(cursor)
    )
    praca_btn.pack(side="left", padx=(10, 0))

    doprava_btn = tb.Button(
        top,
        text="🚗 Doprava",
        bootstyle="light",
        command=show_doprava_window
    )
    doprava_btn.pack(side="left", padx=(10, 0))

    def show_selected_recommendations():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Výber", "Najprv vyber produkt v databáze.")
            return
        vals = tree.item(sel).get("values")
        if not vals:
            messagebox.showwarning("Výber", "Najprv vyber produkt v databáze.")
            return
        produkt_name = vals[0]
        sel_ids = [cid for cid, var in table_vars.items() if var.get()]
        show_recommendations_popup(
            cursor,
            db_type,
            produkt_name,
            basket,
            conn,
            basket_tree,
            mark_modified,
            total_spolu_var,
            total_praca_var,
            total_material_var,
            sel_ids,
        )

    def on_db_right_click(event):
        iid = tree.identify_row(event.y)
        if not iid:
            return
        tree.selection_set(iid)
        tree.focus(iid)
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(
            label="⭐ Odporúčania",
            command=show_selected_recommendations,
        )
        menu.post(event.x_root, event.y_root)


    tk.Label(top, text="Vyhľadávanie:").pack(side="left", padx=(20, 5))
    name_entry = tk.Entry(top, width=30)
    name_entry.pack(side="left")
    filter_job = [None]

    def on_name_change(event=None):
        if filter_job[0]:
            root.after_cancel(filter_job[0])
        filter_job[0] = root.after(
            200,
            lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree),
        )

    name_entry.bind("<KeyRelease>", on_name_change)

    tk.Label(top, text="Objekt:").pack(side="left", padx=(30, 5))
    project_entry = tk.Entry(top, width=40)
    project_entry.insert(0, project_name)
    project_entry.pack(side="left")

    tk.Label(top, text="Systémy:").pack(side="left", padx=(20, 5))
    definition_entry = tk.Entry(top, width=50)
    definition_entry.insert(0, "")
    definition_entry.pack(side="left")
    def back_to_archive():
        try:
            on_closing()
        except Exception:
            return  # ak niečo zlyhá pri ukladaní, zostaneme v GUI

        # ak už root zanikol, spustíme späť Project Selector
        try:
            if root.winfo_exists():
                return  # používateľ dal Cancel -> zostaň v GUI
        except tk.TclError:
            # root bol zničený → môžeme otvoriť selector
            pass

        import subprocess, sys, os
        selector_path = os.path.join(os.path.dirname(__file__), "project_selector.py")
        if os.path.isfile(selector_path):
            subprocess.Popen([sys.executable, selector_path],
                             cwd=os.path.dirname(selector_path) or None)

    archive_btn = tb.Button(
        top,
        text="📂 Archív",
        bootstyle="secondary",
        command=back_to_archive
    )
    archive_btn.pack(side="right", padx=(5, 10))

    # Settings button to configure basket visibility
    settings_btn = tb.Button(
        top,
        text="⚙️ Nastavenia",
        bootstyle="secondary",
        command=lambda: open_settings()
    )
    settings_btn.pack(side="right", padx=(5, 10))

    # ─── Database Treeview (DB results) ───────────────────────────────────
    tree_frame = tb.Frame(main_frame)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
    tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

    tree_scroll_y.pack(side="right", fill="y")
    tree_scroll_x.pack(side="bottom", fill="x")

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
    db_column_vars = {}
    initial_db_display = [c for c in db_columns]

    for col in db_columns:
        var = tk.BooleanVar(value=True)
        db_column_vars[col] = var
    
    tree = ttk.Treeview(
        tree_frame,
        columns=db_columns,
        show="headings",
        displaycolumns=initial_db_display,
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set,
        style="Main.Treeview",
        selectmode="extended"  # allow Ctrl/Shift multi-select
    )
    for c in db_columns:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="center", stretch=True)
    tree.pack(fill="both", expand=True)
    tree_scroll_y.config(command=tree.yview)
    tree_scroll_x.config(command=tree.xview)

    def adjust_db_columns(event):
        """Resize visible DB columns proportionally to the widget width."""
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

        visible = tree.cget("displaycolumns")
        if isinstance(visible, str):
            visible = (visible,)
        total_pct = sum(proportions.get(col, 0) for col in visible)
        if total_pct == 0:
            total_pct = len(visible)

        shrink = 0.75  # show DB columns a bit narrower

        for col in visible:
            pct = proportions.get(col, 1 / len(visible))
            width = int(total * pct / total_pct * shrink)
            tree.column(col, width=width, stretch=True)

    def update_displayed_db_columns():
        visible = [col for col, var in db_column_vars.items() if var.get()]
        if not visible:
            visible = ["produkt"]
            db_column_vars["produkt"].set(True)
        tree.config(displaycolumns=visible)
        event = tk.Event()
        event.width = tree.winfo_width()
        adjust_db_columns(event)

    tree.bind("<Configure>", adjust_db_columns)

    # ─── Basket Area ───────────────────────────────────────────────────────
    basket_frame = tb.Frame(main_frame, padding=5)
    basket_frame.pack(fill="both", expand=True, padx=10, pady=10)

    basket_header = tk.Frame(basket_frame)
    basket_header.pack(fill="x")

    tk.Label(basket_header, text="Košík - vybraté položky:").pack(side="left")

    undo_btn = tb.Button(
        basket_header,
        text="Krok späť",
        bootstyle="secondary",
        command=undo_action
    )

    redo_btn = tb.Button(
        basket_header,
        text="Krok vpred",
        bootstyle="secondary",
        command=redo_action
    )

    # Pack redo button first so it appears to the right of the undo button
    redo_btn.pack(side="right", padx=(0, 10))
    undo_btn.pack(side="right", padx=(0, 5))

    basket_tree_container = tb.Frame(basket_frame)
    basket_tree_container.pack(fill="both", expand=True)
    basket_tree_container.grid_rowconfigure(0, weight=1)
    basket_tree_container.grid_columnconfigure(0, weight=1)

    # Scrollbars
    basket_scroll_y = ttk.Scrollbar(basket_tree_container, orient="vertical")
    basket_scroll_x = ttk.Scrollbar(basket_tree_container, orient="horizontal")
    # -- Column Toggle Checkboxes (Basket) --
    # Reorder columns so material related fields are grouped together
    # followed by work/praca related fields. Columns are made wider via a
    # larger default width to better fit text.
    basket_columns = (
        "produkt",
        "jednotky",

        # --- Material ---------------------------------------------------
        "pocet_materialu",
        "koeficient_material",
        "nakup_mat_jedn",
        "predaj_mat_jedn",
        "nakup_mat_spolu",
        "predaj_mat_spolu",
        "zisk_material",
        "marza_material",

        # --- Praca ------------------------------------------------------
        "pocet_prace",
        "koeficient_praca",
        "cena_prace",
        "nakup_praca_spolu",
        "predaj_praca_jedn",
        "predaj_praca_spolu",
        "zisk_praca",
        "marza_praca",

        # --- Summary / misc -------------------------------------------
        "predaj_spolu",
        "sync",
    )
    column_vars = {}
    for col in basket_columns:
        column_vars[col] = tk.BooleanVar(value=True)

    # -- Basket Treeview --
    initial_display = [c for c in basket_columns]
    basket_tree = ttk.Treeview(
        basket_tree_container,  # ✅ správne ukotvenie
        columns=basket_columns,
        show="tree headings",
        displaycolumns=initial_display,
        yscrollcommand=basket_scroll_y.set,
        xscrollcommand=basket_scroll_x.set,
        style="Basket.Treeview",
        selectmode="extended",  # enable multi-select with Ctrl
    )
    basket_tree.heading("#0", text="")
    # Provide ample space for section headers so the section name is always
    # visible even when many basket columns are shown.
    basket_tree.column("#0", width=180, anchor="w", stretch=False)

    for c in basket_columns:
        basket_tree.heading(c, text=c.capitalize())
        # Estimate a width that fits the entire column name. Longer names get a
        # bit more room so the heading text isn't truncated.
        heading_width = max(150, len(c) * 8 + 30)
        basket_tree.column(c, width=heading_width, anchor="center", stretch=True)

    basket_tree.grid(row=0, column=0, sticky="nsew")
    basket_scroll_y.grid(row=0, column=1, sticky="ns")
    basket_scroll_x.grid(row=1, column=0, sticky="ew")
    basket_scroll_y.config(command=basket_tree.yview)
    basket_scroll_x.config(command=basket_tree.xview)

    def adjust_basket_columns(event):
        """Resize visible basket columns to fit within the widget width."""
        total = event.width
        section_width = 180  # width reserved for the "#0" section column
        remaining = max(total - section_width, 0)

        visible = basket_tree.cget("displaycolumns")
        if isinstance(visible, str):
            visible = (visible,)
        if not visible:
            return

        per_col = int(remaining / len(visible)) if visible else remaining

        for col in visible:
            basket_tree.column(col, width=per_col, stretch=True)

    basket_tree.bind("<Configure>", adjust_basket_columns)




    # ─── Inline edit on double-click (Basket), but intercept "produkt" column to show recs ─
    def on_basket_double_click(event):
        row = basket_tree.identify_row(event.y)
        col = basket_tree.identify_column(event.x)
        if not row:
            return

        # If this is a section header (parent == ""), do nothing
        if basket_tree.parent(row) == "":
            return

        basket.snapshot()

        # Use all currently selected rows (excluding section headers)
        selected = [
            r for r in basket_tree.selection()
            if basket_tree.parent(r) != ""
        ]
        if not selected:
            selected = [row]

        # Determine which column is being edited
        idx_visible = int(col.replace("#", "")) - 1
        visible_cols = basket_tree.cget("displaycolumns")
        if isinstance(visible_cols, str):
            visible_cols = (visible_cols,)
        if idx_visible >= len(visible_cols):
            return
        col_name = visible_cols[idx_visible]
        sec = basket_tree.parent(row)
        prod = basket_tree.item(row)["values"][0]
        editable_cols = {
            "jednotky",
            "koeficient_material",
            "nakup_mat_jedn",
            "koeficient_praca",
            "cena_prace",
            "pocet_materialu",
            "pocet_prace",
        }
        if col_name not in editable_cols and col_name != "sync" and col_name not in {"pocet_materialu", "pocet_prace"}:
            # Computed columns
            return

        old = basket_tree.set(row, col_name)
        section_name = basket_tree.item(sec, "text")
        if col_name == "sync":
            new_val = not basket.items[section_name][prod].sync
            for iid in selected:
                sec_name = basket_tree.item(basket_tree.parent(iid), "text")
                prod_name = basket_tree.item(iid)["values"][0]
                basket.items[sec_name][prod_name].sync = new_val
                if new_val:
                    mat_c = basket.items[sec_name][prod_name].pocet_materialu
                    basket.items[sec_name][prod_name].pocet_prace = mat_c
            update_basket_table(basket_tree, basket)
            recompute_total_spolu(basket, total_spolu_var,
                                total_praca_var, total_material_var)
            mark_modified()
            return
        elif col_name in ("pocet_materialu", "pocet_prace"):
            if col_name == "pocet_prace" and basket.items[section_name][prod].sync:
                messagebox.showinfo(
                    "Synchronizácia",
                    "Počet práce je synchronizovaný s počtom materiálu.\nVypnite Sync pre úpravu."
                )
                return
            new = simpledialog.askinteger(
                "Upraviť bunku",
                f"Nová hodnota pre '{col_name}'",
                initialvalue=int(old),
                parent=root
            )
        else:
            new = askfloat_locale(
                "Upraviť bunku",
                f"Nová hodnota pre '{col_name}'",
                initialvalue=old,
                parent=root
            )
        if new is None:
            return

        for iid in selected:
            sec_i = basket_tree.item(basket_tree.parent(iid), "text")
            prod_i = basket_tree.item(iid)["values"][0]
            basket_tree.set(iid, col_name, new)
            if col_name in editable_cols:
                attr = col_name
                if attr == "nakup_mat_jedn":
                    attr = "nakup_materialu"
                if attr == "koeficient_praca":
                    attr = "koeficient_prace"

                old_val = getattr(basket.items[sec_i][prod_i], attr)
                if attr == "koeficient_material":
                    key = (sec_i, prod_i)
                    if key not in basket.base_coeffs_material:
                        basket.base_coeffs_material[key] = old_val
                if attr == "koeficient_prace":
                    key = (sec_i, prod_i)
                    if key not in basket.base_coeffs_work:
                        basket.base_coeffs_work[key] = old_val

                setattr(basket.items[sec_i][prod_i], attr, new)
                if basket.items[sec_i][prod_i].sync and col_name == "pocet_materialu":
                    basket.items[sec_i][prod_i].pocet_prace = new

        mark_modified()
        update_basket_table(basket_tree, basket)
        recompute_total_spolu(basket, total_spolu_var,
                            total_praca_var, total_material_var)

    basket_tree.bind("<Double-1>", on_basket_double_click)

    # Inline cell editor (rebind Double-Click to edit in place)
    _cell_editor = {"widget": None}

    def _destroy_editor(commit=False):
        ed = _cell_editor.get("widget")
        if not ed or not ed.winfo_exists():
            _cell_editor["widget"] = None
            return

        row = getattr(ed, "_edit_row", None)
        col_name = getattr(ed, "_edit_col", None)
        dtype = getattr(ed, "_edit_type", None)
        value_text = ed.get()

        ed.destroy()
        _cell_editor["widget"] = None

        if not commit or not row or not col_name:
            return

        # Determine targets: apply to all selected items in same column, or only the edited row
        selected = [r for r in basket_tree.selection() if basket_tree.parent(r)]
        if not selected or row not in selected:
            selected = [row]

        # Parse value according to type
        try:
            if dtype == "int":
                new_val = int(float(str(value_text).replace(",", ".")))
            elif dtype == "float":
                new_val = float(str(value_text).replace(",", "."))
            else:
                new_val = value_text
        except Exception:
            root.bell()
            return

        # Update model and UI
        basket.snapshot()
        for iid in selected:
            sec_name = basket_tree.item(basket_tree.parent(iid), "text")
            prod_name = basket_tree.item(iid)["values"][0]

            # map visible column to BasketItem attribute
            attr = col_name
            if attr == "nakup_mat_jedn":
                attr = "nakup_materialu"
            if attr == "koeficient_praca":
                attr = "koeficient_prace"

            # protect against editing of computed/unsupported columns
            if attr not in {
                "pocet_materialu",
                "pocet_prace",
                "koeficient_material",
                "koeficient_prace",
                "nakup_materialu",
                "cena_prace",
            }:
                continue

            # Respect sync when editing pocet_prace
            if col_name == "pocet_prace" and basket.items[sec_name][prod_name].sync:
                continue

            # Remember original coefficients for revert actions
            if attr == "koeficient_material":
                key = (sec_name, prod_name)
                if key not in basket.base_coeffs_material:
                    basket.base_coeffs_material[key] = getattr(basket.items[sec_name][prod_name], attr)
            if attr == "koeficient_prace":
                key = (sec_name, prod_name)
                if key not in basket.base_coeffs_work:
                    basket.base_coeffs_work[key] = getattr(basket.items[sec_name][prod_name], attr)

            setattr(basket.items[sec_name][prod_name], attr, new_val)
            if basket.items[sec_name][prod_name].sync and col_name == "pocet_materialu":
                basket.items[sec_name][prod_name].pocet_prace = new_val

        mark_modified()
        update_basket_table(basket_tree, basket)
        recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)

    def on_basket_cell_double_click(event):
        # If an editor is active, commit and remove it first
        _destroy_editor(commit=True)

        row = basket_tree.identify_row(event.y)
        col = basket_tree.identify_column(event.x)
        if not row:
            return

        # If this is a section header (parent == ""), do nothing
        if basket_tree.parent(row) == "":
            return

        # Determine which column is being edited
        idx_visible = int(col.replace("#", "")) - 1
        visible_cols = basket_tree.cget("displaycolumns")
        if isinstance(visible_cols, str):
            visible_cols = (visible_cols,)
        if idx_visible >= len(visible_cols):
            return
        col_name = visible_cols[idx_visible]

        sec = basket_tree.parent(row)
        prod = basket_tree.item(row)["values"][0]

        # Toggle sync without editor
        section_name = basket_tree.item(sec, "text")
        if col_name == "sync":
            basket.snapshot()
            new_val = not basket.items[section_name][prod].sync
            selected = [r for r in basket_tree.selection() if basket_tree.parent(r)]
            if not selected or row not in selected:
                selected = [row]
            for iid in selected:
                sec_name = basket_tree.item(basket_tree.parent(iid), "text")
                prod_name = basket_tree.item(iid)["values"][0]
                basket.items[sec_name][prod_name].sync = new_val
                if new_val:
                    mat_c = basket.items[sec_name][prod_name].pocet_materialu
                    basket.items[sec_name][prod_name].pocet_prace = mat_c
            update_basket_table(basket_tree, basket)
            recompute_total_spolu(basket, total_spolu_var, total_praca_var, total_material_var)
            mark_modified()
            return

        # Establish editor type
        if col_name in ("pocet_materialu", "pocet_prace"):
            if col_name == "pocet_prace" and basket.items[section_name][prod].sync:
                messagebox.showinfo(
                    "Synchronizácia",
                    "Počet práce je synchronizovaný s počtom materiálu.\nVypnite Sync pre úpravu.",
                )
                return
            dtype = "int"
        elif col_name in ("koeficient_material", "nakup_mat_jedn", "koeficient_praca", "cena_prace"):
            dtype = "float"
        else:
            # Computed or unsupported columns are not editable
            return

        old = basket_tree.set(row, col_name)
        # Place editor over the cell
        try:
            x, y, w, h = basket_tree.bbox(row, col)
        except Exception:
            basket_tree.see(row)
            try:
                x, y, w, h = basket_tree.bbox(row, col)
            except Exception:
                return

        ed = tk.Entry(basket_tree)
        ed.insert(0, str(old))
        ed.select_range(0, "end")
        ed.focus_set()
        ed.place(x=x, y=y, width=w, height=h)
        ed._edit_row = row
        ed._edit_col = col_name
        ed._edit_type = dtype
        _cell_editor["widget"] = ed

        # Commit/cancel bindings
        ed.bind("<Return>", lambda e: _destroy_editor(commit=True))
        ed.bind("<Escape>", lambda e: _destroy_editor(commit=False))
        ed.bind("<FocusOut>", lambda e: _destroy_editor(commit=True))

    # Override the earlier double-click binding with inline editor
    basket_tree.bind("<Double-1>", on_basket_cell_double_click)

    # -- Right-click context menu to Reset item (Basket) --
    def on_basket_right_click(event):
        iid = basket_tree.identify_row(event.y)
        if not iid or not basket_tree.parent(iid):
            return
        menu = tk.Menu(root, tearoff=0)

        def do_reset():
            selected = [
                r for r in basket_tree.selection()
                if basket_tree.parent(r)
            ]
            if iid not in selected:
                selected = [iid]
            reset_items(
                selected,
                basket_tree,
                basket,
                total_spolu_var,
                mark_modified,
                total_praca_var,
                total_material_var,
            )

        prod_name = basket_tree.item(iid)["values"][0]

        def do_show_recs():
            show_recommendations_popup(
                cursor,
                db_type,
                prod_name,
                basket,
                conn,
                basket_tree,
                mark_modified,
                total_spolu_var,
                total_praca_var,
                total_material_var,
            )

        menu.add_command(
            label="Reset položky",
            command=do_reset,
        )
        menu.add_command(
            label="⭐ Odporúčané",
            command=do_show_recs,
        )
        menu.post(event.x_root, event.y_root)

    basket_tree.bind("<Button-3>", on_basket_right_click)

    # -- Drag-drop reordering in basket (just moves items within same parent) --
    _drag = {"item": None}

    def on_basket_press(event):
        iid = basket_tree.identify_row(event.y)
        _drag["item"] = iid
        if event.state & 0x4:  # Ctrl held
            if iid and iid not in basket_tree.selection():
                basket_tree.selection_add(iid)
            basket_tree.focus(iid)
            return "break"

    basket_tree.bind("<ButtonPress-1>", on_basket_press)
    basket_tree.bind(
        "<B1-Motion>",
        lambda e: (
            basket_tree.move(
                _drag["item"],
                basket_tree.parent(_drag["item"]),
                basket_tree.index(basket_tree.identify_row(e.y))
            )
            if (_drag.get("item")
                and basket_tree.parent(basket_tree.identify_row(e.y)) ==
                    basket_tree.parent(_drag["item"]))
            else None
        )
    )
    basket_tree.bind(
        "<ButtonRelease-1>",
        lambda e: _drag.update({"item": None})
    )

    # ─── Grand Total Label (“Spolu: …”) ───────────────────────────────────
    total_frame = tk.Frame(basket_frame)
    total_frame.pack(fill="x", pady=(2, 0))
    total_spolu_var = tk.StringVar(value=f"Spolu: {format_currency(0)}")
    total_praca_var = tk.StringVar(value=f"Spolu práca: {format_currency(0)}")
    total_material_var = tk.StringVar(value=f"Spolu materiál: {format_currency(0)}")
    tk.Label(total_frame, textvariable=total_spolu_var, anchor="e").pack(
        side="right", padx=10
    )
    tk.Label(total_frame, textvariable=total_praca_var, anchor="e").pack(
        side="right", padx=10
    )
    tk.Label(total_frame, textvariable=total_material_var, anchor="e").pack(
        side="right", padx=10
    )

    # ─── Notes button ─────────────────────────────────────────────────────

    # ─── Buttons Row: Remove, Add, Export (left) and Coeff Buttons (right) ─
    btn_container = tk.Frame(basket_frame)
    btn_container.pack(fill="x", pady=5)

    left_btn_frame = tk.Frame(btn_container)
    left_btn_frame.pack(side="left")

    right_btn_frame = tk.Frame(btn_container)
    right_btn_frame.pack(side="right")

    remove_btn = tb.Button(
        left_btn_frame,
        text="Odstrániť",
        bootstyle="danger-outline",
        command=lambda: (
            remove_from_basket(basket_tree, basket),
            mark_modified()
        )
    )
    remove_btn.pack(side="left", padx=(0, 10))


    add_custom_btn = tb.Button(
        left_btn_frame,
        text="Pridať",
        bootstyle="primary-outline",
        command=lambda: add_custom_item(
            basket_tree,
            basket,
            total_spolu_var,
            mark_modified,
            total_praca_var,
            total_material_var
        )
    )
    add_custom_btn.pack(side="left", padx=(0, 10))
    
    notes_btn = tb.Button(
        left_btn_frame,
        text="Poznámky",
        bootstyle="secondary",
        command=lambda: show_notes_popup(project_name, commit_file)
    )
    notes_btn.pack(side="left", padx=(0, 10))


    def export_with_progress():
        reorder_basket_data(basket_tree, basket)

        progress_win = tk.Toplevel(root)
        progress_win.title("Export")
        pb = tb.Progressbar(progress_win, mode="indeterminate", length=200)
        pb.pack(padx=20, pady=20)
        pb.start()

        def worker():
            try:
                update_excel_from_basket(
                    basket,
                    project_entry.get(),
                    commit_file,
                    definicia_text=definition_entry.get()
                )
            finally:
                pb.stop()
                progress_win.destroy()

        threading.Thread(target=worker, daemon=True).start()

    exportCPINT_btn = tb.Button(
        left_btn_frame,
        text="Exportovať CP INT",
        bootstyle="success",
        command=export_with_progress
    )
    exportCPINT_btn.pack(side="left", padx=(0, 10))
    def export_simple_excel_from_basket(basket, project_name, definicia_text=""):
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

        export_cp(excel_data, project_name, definicia_text)

    exportCP_btn = tb.Button(
        left_btn_frame,
        text="Exportovať CP",
        bootstyle="success",
        command=lambda: export_simple_excel_from_basket(
            basket,
            project_entry.get(),
            definition_entry.get()
    )
    )
    exportCP_btn.pack(side="left", padx=(0, 10))

    exportVV_btn = tb.Button(
        left_btn_frame,
        text="Exportovať Vv",
        bootstyle="success",
        command=lambda: export_vv(
            [
                (
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
                )
                for section, products in basket.items.items()
                for produkt, v in products.items()
            ],
            project_entry.get(),
            "",  # poznámky
            definition_entry.get()
    )
    )
    exportVV_btn.pack(side="left", padx=(0, 10))

    kontrola_btn = tb.Button(
        right_btn_frame,
        text="Kontrola",
        bootstyle="secondary",
        command=lambda: check_type_dependencies(
            basket,
            cursor,
            conn,
            db_type,
            basket_tree,
            mark_modified,
            total_spolu_var,
            total_praca_var,
            total_material_var,
        ),
    )
    kontrola_btn.pack(side="left", padx=(0, 10))

    coeff_set_mat_btn = tb.Button(
        right_btn_frame,
        text="Nastav koef. materiál",
        bootstyle="info-outline",
        command=lambda: apply_material_coefficient(
            basket,
            basket_tree,
            total_spolu_var,
            mark_modified,
            total_praca_var,
            total_material_var,
        ),
    )
    coeff_set_mat_btn.pack(side="left", padx=(0, 10))

    coeff_rev_mat_btn = tb.Button(
        right_btn_frame,
        text="Revert koef. materiál",
        bootstyle="warning-outline",
        command=lambda: revert_material_coefficient(
            basket,
            basket_tree,
            total_spolu_var,
            mark_modified,
            total_praca_var,
            total_material_var,
        ),
    )
    coeff_rev_mat_btn.pack(side="left", padx=(0, 10))

    coeff_set_work_btn = tb.Button(
        right_btn_frame,
        text="Nastav koef. práca",
        bootstyle="info-outline",
        command=lambda: apply_work_coefficient(
            basket,
            basket_tree,
            total_spolu_var,
            mark_modified,
            total_praca_var,
            total_material_var,
        ),
    )
    coeff_set_work_btn.pack(side="left", padx=(0, 10))

    coeff_rev_work_btn = tb.Button(
        right_btn_frame,
        text="Revert koef. práca",
        bootstyle="warning-outline",
        command=lambda: revert_work_coefficient(
            basket,
            basket_tree,
            total_spolu_var,
            mark_modified,
            total_praca_var,
            total_material_var,
        ),
    )
    coeff_rev_work_btn.pack(side="left")
    # ──────────────────────────────────────────────────────────────────────────

    # ─── Initialize basket state ──────────────────────────────────────────
    basket = Basket()
    basket_items_loaded, saved, _ = load_basket(json_dir, project_name, file_path=commit_file)
    for sec, prods in basket_items_loaded.items():
        for pname, data in prods.items():
            basket.add_item(
                (
                    pname,
                    data.get("jednotky", ""),
                    data.get("dodavatel", ""),
                    data.get("odkaz", ""),
                    data.get("koeficient_material", 1.0),
                    data.get("nakup_materialu", 0.0),
                    data.get("cena_prace", 0.0),
                    data.get("koeficient_prace", 1.0),
                    sec,
                ),
                section=sec,
            )
            # Restore additional fields that are not handled by add_item
            basket.items[sec][pname].pocet_materialu = int(data.get("pocet_materialu", 1))
            basket.items[sec][pname].pocet_prace = int(data.get("pocet_prace", 1))
            basket.original[sec][pname].pocet_materialu = int(data.get("pocet_materialu", 1))
            basket.original[sec][pname].pocet_prace = int(data.get("pocet_prace", 1))

            sync_state = data.get("sync", data.get("sync_qty", True))
            basket.items[sec][pname].sync = sync_state
            basket.original[sec][pname].sync = sync_state
    update_basket_table(basket_tree, basket)
    recompute_total_spolu(basket, total_spolu_var,
                          total_praca_var, total_material_var)
    basket._undo_stack.clear()
    basket._redo_stack.clear()

    # ─── Initial filtering of DB results ─────────────────────────────────
    apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

    # ─── Ensure basket columns display matches checkboxes ───
    def update_displayed_columns():
        visible = [col for col, var in column_vars.items() if var.get()]
        if not visible:
            visible = ["produkt"]
            column_vars["produkt"].set(True)
        basket_tree.config(displaycolumns=visible)
        event = tk.Event()
        event.width = basket_tree.winfo_width()
        adjust_basket_columns(event)

    update_displayed_columns()

    # ─── Settings window for basket visibility ────────────────────────────
    settings_window = [None]

    def open_settings():
        if settings_window[0] and settings_window[0].winfo_exists():
            settings_window[0].focus()
            return

        settings_win = tk.Toplevel(root)
        settings_window[0] = settings_win
        settings_win.title("Nastavenia")
        settings_win.geometry("1000x350")
        settings_win.resizable(False, False)

        container = tk.Frame(settings_win, bg="white")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        h_scroll = tk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=h_scroll.set)

        inner = tk.Frame(canvas, bg="white")
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.pack(fill="both", expand=True)
        h_scroll.pack(side="bottom", fill="x")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        label_font = ("Segoe UI", 10, "bold")

        # --- Database column visibility ---------------------------------
        tk.Label(inner, text="Stĺpce databázy", font=label_font, bg="white").pack(anchor="w", padx=5, pady=(5, 0))
        db_chk_frame = tk.Frame(inner, bg="white")
        db_chk_frame.pack(anchor="w", padx=20, pady=(0, 10))

        db_cols_per_row = 8
        for idx, col in enumerate(db_columns):
            chk = tk.Checkbutton(
                db_chk_frame,
                text=col.capitalize(),
                variable=db_column_vars[col],
                command=update_displayed_db_columns,
                bg="white",
            )
            r = idx // db_cols_per_row
            c = idx % db_cols_per_row
            chk.grid(row=r, column=c, sticky="w", padx=5, pady=2)

        # --- Basket column visibility -----------------------------------
        tk.Label(inner, text="Zobraziť stĺpce:", font=label_font, bg="white").pack(anchor="w", padx=5, pady=(10, 0))
        basket_chk_frame = tk.Frame(inner, bg="white")
        basket_chk_frame.pack(anchor="w", padx=20, pady=(0, 10))

        basket_cols_per_row = 8
        for idx, col in enumerate(basket_columns):
            chk = tk.Checkbutton(
                basket_chk_frame,
                text=col.capitalize(),
                variable=column_vars[col],
                command=update_displayed_columns,
                bg="white",
            )
            r = idx // basket_cols_per_row
            c = idx % basket_cols_per_row
            chk.grid(row=r, column=c, sticky="w", padx=5, pady=2)

        # --- Table font size -------------------------------------------
        tk.Label(inner, text="Veľkosť textu tabuliek:", font=label_font, bg="white").pack(anchor="w", padx=5, pady=(10, 0))
        font_frame = tk.Frame(inner, bg="white")
        font_frame.pack(anchor="w", padx=20, pady=(0, 10))

        spin = tk.Spinbox(font_frame, from_=8, to=24, textvariable=tk.IntVar(value=font_size_var[0]), width=5)
        spin.pack(side="left", padx=5)

        # --- Save button -----------------------------------------------
        btn_frame = tk.Frame(inner, bg="white")
        btn_frame.pack(pady=15)

        def close_settings():
            update_displayed_columns()
            try:
                font_size_var[0] = int(spin.get())
            except Exception:
                font_size_var[0] = font_size_var[0]
            row_h = int(2.4 * font_size_var[0])
            style.configure("Main.Treeview", rowheight=row_h, font=("Segoe UI", font_size_var[0]))
            style.configure("Basket.Treeview", rowheight=row_h, font=("Segoe UI", font_size_var[0]))
            root.option_add("*Font", ("Segoe UI", font_size_var[0]))
            _save_ui_settings({"table_font_size": font_size_var[0]})
            settings_window[0] = None
            settings_win.destroy()

        save_btn = tk.Button(
            btn_frame,
            text="💾 Uložiť",
            command=close_settings,
            bg="#007BFF",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=5
        )
        save_btn.pack()

        settings_win.protocol("WM_DELETE_WINDOW", close_settings)


        

    # ── REPLACE the old DB-double-click binding with this new one ─────────────
    def on_db_double_click(event):
        """
        Called when the user double-clicks a row in the main DB Treeview (`tree`):
        it simply adds that product to the basket.
        """
        selected = tree.item(tree.focus())
        if not selected:
            return
        db_values = selected["values"]
        # Skip header rows which only contain two values
        if len(db_values) < 8:
            return

        # 1) Insert base product into the basket
        add_to_basket_full(
            db_values,
            basket,
            conn, cursor, db_type,
            basket_tree,
            mark_modified,
            total_spolu_var,
            total_praca_var,
            total_material_var
        )

    tree.bind("<Double-1>", on_db_double_click)
    tree.bind("<Button-3>", on_db_right_click)
    # ───────────────────────────────────────────────────────────────────────────

    # ─── Handle window close (“X”) ────────────────────────────────────────
    def on_closing():
        resp = tk.messagebox.askyesnocancel(
            "Uložiť zmeny?",
            "Chceš uložiť zmeny pred zatvorením košíka?"
        )
        if resp is None:
            return  # Cancel
        if resp is False:
            if root.winfo_exists():
                root.destroy()
            return

        reorder_basket_data(basket_tree, basket)
        default_base = "basket"
        fname = tk.simpledialog.askstring(
            "Košík — Uložiť ako",
            "Zadaj názov súboru (bez prípony):",
            initialvalue=default_base,
            parent=root
        )
        if not fname:
            return  # user canceled

        ts = datetime.now().strftime("_%Y-%m-%d_%H-%M-%S")
        filename = f"{fname}{ts}.json"
        fullpath = os.path.join(json_dir, filename)

        if os.path.exists(fullpath):
            if not tk.messagebox.askyesno(
                "Prepis existujúceho súboru?",
                f"“{filename}” už existuje. Chceš ho prepísať?"
            ):
                return

        notes_list = get_current_notes(project_name, commit_file)

        history_entry = {"timestamp": datetime.now().isoformat(), "notes": notes_list}
        if os.path.exists(commit_file):
            try:
                with open(commit_file, "r", encoding="utf-8") as cf:
                    prev = json.load(cf)
                    notes_history = prev.get("notes_history", [])
            except Exception:
                notes_history = []
        else:
            notes_history = []
        notes_history.append(history_entry)

        # autor z CURRENT_USER (stabilný – nemení sa pri neskorších prihláseniach)
        user = globals().get("CURRENT_USER", {}) or {}
        meno_u = user.get("meno", "")
        priezvisko_u = user.get("priezvisko", "")
        username_u = user.get("username", "")
        user_id_u = user.get("id")

        if priezvisko_u or meno_u:
            author = f"{priezvisko_u} {meno_u[:1]}.".strip()
        elif username_u:
            author = username_u
        else:
            author = ""

        out = {
            
            "author": author,            # pre rýchle čítanie
            "user_id": user_id_u,        # pre DB mapovanie
            "username": username_u, 
            "project": project_name,
            "author": author,
            "items": [],
            "notes": notes_list,
            "notes_history": notes_history,
        }

        for section, prods in basket.items.items():
            sec_obj = {"section": section, "products": []}
            for pname, info in prods.items():
                sec_obj["products"].append({
                    "produkt":              pname,
                    "jednotky":             info.jednotky,
                    "dodavatel":            info.dodavatel,
                    "odkaz":                info.odkaz,
                    "koeficient_material":  info.koeficient_material,
                    "nakup_materialu":      info.nakup_materialu,
                    "koeficient_prace":     info.koeficient_prace,
                    "cena_prace":           info.cena_prace,
                    "pocet_prace":          info.pocet_prace,
                    "pocet_materialu":      info.pocet_materialu,
                    "sync":                 info.sync,
                })
            out["items"].append(sec_obj)

        try:
            with open(fullpath, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            with open(commit_file, "w", encoding="utf-8") as cf:
                json.dump(out, cf, ensure_ascii=False, indent=2)
            UNSAVED_NOTES.pop(project_name, None)
        except Exception as e:
            messagebox.showerror(
                "Chyba pri ukladaní",
                f"Nepodarilo sa uložiť súbor:\n{e}"
            )
            return

        if root.winfo_exists():
            root.destroy()




    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    project_dir = sys.argv[1]
    json_path   = sys.argv[2]
    start(project_dir, json_path)
