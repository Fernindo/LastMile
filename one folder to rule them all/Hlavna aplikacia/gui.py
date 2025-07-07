# gui.py

import sys
import os
import tkinter as tk
import tkinter.ttk as ttk
import ttkbootstrap as tb
import json
from datetime import datetime
import tkinter.simpledialog
from ttkbootstrap import Style
from ttkbootstrap.widgets import Combobox
from collections import OrderedDict
from praca import show_praca_window

from gui_functions import (
    get_database_connection,
    sync_postgres_to_sqlite,
    load_basket,
    apply_filters,
    update_basket_table,
    add_to_basket_full,         # “silent” version, DOES NOT auto-add recs
    reorder_basket_data,
    update_excel_from_basket,
    remove_from_basket,
    recompute_total_spolu,
    apply_global_coefficient,
    revert_coefficient,
    reset_item,
    add_custom_item,
    show_notes_popup,
    fetch_recommendations_async
)

from filter_panel import create_filter_panel
from tkinter import messagebox, simpledialog

def start(project_dir, json_path):
    """
    Build the entire UI (layout, widgets, geometry) here. All logic lives in gui_functions.py.
    """

    # ─── Prepare paths and DB ────────────────────────────────────────────
    project_name = os.path.basename(project_dir)
    json_dir     = os.path.join(project_dir, "projects")
    commit_file  = json_path

    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    if db_type == "postgres":
        sync_postgres_to_sqlite(conn)

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
    root.title(f"Project: {project_name}")
    root.state("zoomed")
    root.option_add("*Font", ("Segoe UI", 10))

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=0)  # filter column
    root.grid_columnconfigure(1, weight=1)

    # ─── Track whether the basket has been modified ──────────────────────
    basket_modified = [False]  # use a list so nested functions can modify

    def mark_modified():
        basket_modified[0] = True

    # ─── Top-Level Frames ─────────────────────────────────────────────────
    
    main_frame   = tb.Frame(root, padding=10)
    main_frame.grid(row=0, column=0, sticky="nsew")
    
    db_visible = [True]  # Používame list kvôli mutabilite

    def toggle_db_view():
        if db_visible[0]:
            tree_frame.pack_forget()
            toggle_btn.config(text="🔼 Zobraziť databázu")
        else:
            tree_frame.pack(in_=main_frame, before=basket_frame, fill="both", expand=True, padx=10, pady=10)
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
            # hide filter, expand main into column 0
            filter_container.grid_forget()
            main_frame.grid(row=0, column=0, sticky="nsew")
            root.grid_columnconfigure(0, weight=1)
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
        font=("Segoe UI", 12, "bold"),
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
        bootstyle="secondary",
        command=toggle_db_view
    )
    toggle_btn.pack(side="left", padx=(10, 0))
    
    toggle_basket_btn = tb.Button(
    top,
    text="🔽 Skryť košík",
    bootstyle="secondary",
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

    tk.Label(top, text="Vyhľadávanie:").pack(side="left", padx=(20, 5))
    name_entry = tk.Entry(top, width=30)
    name_entry.pack(side="left")
    name_entry.bind(
        "<KeyRelease>",
        lambda e: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
    )

    tk.Label(top, text="Projekt:").pack(side="left", padx=(30, 5))
    project_entry = tk.Entry(top, width=40)
    project_entry.insert(0, project_name)
    project_entry.pack(side="left")

    tk.Label(top, text="Definícia:").pack(side="left", padx=(20, 5))
    definition_entry = tk.Entry(top, width=50)
    definition_entry.insert(0, "")
    definition_entry.pack(side="left")

    # Theme selector
    theme_var = tk.StringVar(value="litera")
    theme_combo = Combobox(
        top,
        textvariable=theme_var,
        values=style.theme_names(),
        width=10,
        state="readonly"
    )
    theme_combo.pack(side="right", padx=(5, 10))

    def change_theme(event=None):
        style.theme_use(theme_var.get())

    theme_combo.bind("<<ComboboxSelected>>", change_theme)

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

    db_checkbox_frame = tb.LabelFrame(tree_frame, text="Zobraziť stĺpce:", padding=5)
    db_checkbox_frame.pack(fill="x", pady=(0, 5))
    for col in db_columns:
        var = tk.BooleanVar(value=True)
        db_column_vars[col] = var
        chk = tk.Checkbutton(
            db_checkbox_frame,
            text=col.capitalize(),
            variable=var,
            command=lambda: update_displayed_db_columns()
        )
        chk.pack(side="left", padx=5)
    
    tree = ttk.Treeview(   
        tree_frame,
        columns=db_columns,
        show="headings",
        displaycolumns=initial_db_display,
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set
    )
    for c in db_columns:
        tree.heading(c, text=c.capitalize())
        tree.column(c, anchor="center", stretch=True)
    tree.pack(fill="both", expand=True)
    tree_scroll_y.config(command=tree.yview)
    tree_scroll_x.config(command=tree.xview)

    def adjust_db_columns(event):
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
        total_prop = sum(proportions.get(c, 1) for c in visible)
        for col in visible:
            pct = proportions.get(col, 1)
            tree.column(col, width=int(total * pct / total_prop), stretch=True)

    def update_displayed_db_columns():
        visible = [col for col, var in db_column_vars.items() if var.get()]
        if not visible:
            visible = ["produkt"]
            db_column_vars["produkt"].set(True)
        tree.config(displaycolumns=visible)
        adjust_db_columns(tk.Event(width=tree.winfo_width()))

    tree.bind("<Configure>", adjust_db_columns)

    # ─── Basket Area ───────────────────────────────────────────────────────
    basket_frame = tb.Frame(main_frame, padding=5)
    basket_frame.pack(fill="both", expand=True, padx=10, pady=10)
    tk.Label(basket_frame, text="Košík - vybraté položky:").pack(anchor="w")
    basket_tree_container = tb.Frame(basket_frame)
    basket_tree_container.pack(fill="both", expand=True)
    basket_tree_container.rowconfigure(0, weight=1)
    basket_tree_container.columnconfigure(0, weight=1)

    # Scrollbary
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
        "sync_qty",
    )
    column_vars = {}
    checkbox_frame = tb.LabelFrame(basket_frame, text="Zobraziť stĺpce:", padding=5)
    checkbox_frame.pack(fill="x", pady=(3, 8))
    for col in basket_columns:
        var = tk.BooleanVar(value=True)
        column_vars[col] = var
        chk = tk.Checkbutton(
            checkbox_frame,
            text=col.capitalize(),
            variable=var,
            command=lambda: update_displayed_columns()
        )
        chk.pack(side="left", padx=5)

    # -- Basket Treeview --
    initial_display = [c for c in basket_columns]
    basket_tree = ttk.Treeview(
        basket_tree_container,
        columns=basket_columns,
        show="tree headings",
        displaycolumns=initial_display,
        yscrollcommand=basket_scroll_y.set,
        xscrollcommand=basket_scroll_x.set,
    )
    basket_tree.heading("#0", text="")
    basket_tree.column("#0", width=20, anchor="w", stretch=False)
    # Maintain a reasonable minimum width per column so text isn't cropped.
    basket_min_width = 150
    for c in basket_columns:
        basket_tree.heading(c, text=c.capitalize())
        basket_tree.column(c, width=basket_min_width, anchor="center",
                          stretch=False)
    basket_tree.grid(row=0, column=0, sticky="nsew")
    basket_scroll_y.grid(row=0, column=1, sticky="ns")
    basket_scroll_x.grid(row=1, column=0, sticky="ew")
    basket_scroll_y.config(command=basket_tree.yview)
    basket_scroll_x.config(command=basket_tree.xview)

    def adjust_basket_columns(event):
        total = event.width
        visible = basket_tree.cget("displaycolumns")
        if isinstance(visible, str):
            visible = (visible,)
        count = len(visible)
        if count == 0:
            return
        width = max(basket_min_width, int(total / count))
        for col in visible:
            basket_tree.column(col, width=width, stretch=False)

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

        # If user double-clicked on the "Produkt" column (#1), show recommendations:
        if col == "#1":
            vals = basket_tree.item(row)["values"]
            produkt_name = vals[0]
            # We already know the parent (section) is basket_tree.parent(row)
            # so just fetch recs for produkt_name:
            fetch_recommendations_async(
                conn=conn,
                cursor=cursor,
                db_type=db_type,
                base_product_name=produkt_name,
                basket_items=basket_items,
                root=root,
                recom_tree=recom_tree,
                max_recs=3
            )
            return

        # Otherwise, do the normal inline-edit (float/int prompt):
        idx_visible = int(col.replace("#", "")) - 1
        visible_cols = basket_tree.cget("displaycolumns")
        if isinstance(visible_cols, str):
            visible_cols = (visible_cols,)
        if idx_visible >= len(visible_cols):
            return
        col_name = visible_cols[idx_visible]
        idx = basket_columns.index(col_name)
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
        if col_name not in editable_cols and col_name != "sync_qty" and col_name not in {"pocet_materialu", "pocet_prace"}:
            # Computed columns
            return

        old = basket_tree.set(row, col_name)
        if col_name == "sync_qty":
            new_val = not basket_items[basket_tree.item(sec, "text")][prod].get("sync_qty", False)
            basket_items[basket_tree.item(sec, "text")][prod]["sync_qty"] = new_val
            if new_val:
                # sync counts
                mat_count = basket_items[basket_tree.item(sec, "text")][prod]["pocet_materialu"]
                basket_items[basket_tree.item(sec, "text")][prod]["pocet_prace"] = mat_count
        elif col_name in ("pocet_materialu", "pocet_prace"):
            if col_name == "pocet_prace" and basket_items[basket_tree.item(sec, "text")][prod].get("sync_qty"):
                return
            new = simpledialog.askinteger(
                "Upraviť bunku",
                f"Nová hodnota pre '{col_name}'",
                initialvalue=int(old),
                parent=root
            )
        else:
            new = simpledialog.askfloat(
                "Upraviť bunku",
                f"Nová hodnota pre '{col_name}'",
                initialvalue=float(old),
                parent=root
            )
        if col_name == "sync_qty":
            update_basket_table(basket_tree, basket_items)
            recompute_total_spolu(basket_items, total_spolu_var)
            mark_modified()
            return
        if new is None:
            return

        basket_tree.set(row, col_name, new)
        sec = basket_tree.parent(row)
        prod = basket_tree.item(row)["values"][0]
        if col_name in editable_cols:
            target = "nakup_materialu" if col_name == "nakup_mat_jedn" else col_name
            basket_items[basket_tree.item(sec, "text")][prod][target] = new
            if (
                basket_items[basket_tree.item(sec, "text")][prod].get("sync_qty")
                and col_name == "pocet_materialu"
            ):
                basket_items[basket_tree.item(sec, "text")][prod]["pocet_prace"] = new

        mark_modified()
        update_basket_table(basket_tree, basket_items)
        recompute_total_spolu(basket_items, total_spolu_var)

    basket_tree.bind("<Double-1>", on_basket_double_click)

    # -- Right-click context menu to Reset item (Basket) --
    def on_basket_right_click(event):
        iid = basket_tree.identify_row(event.y)
        if not iid or not basket_tree.parent(iid):
            return
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(
            label="Reset položky",
            command=lambda: reset_item(
                iid,
                basket_tree,
                basket_items,
                original_basket,
                total_spolu_var,
                mark_modified
            )
        )
        menu.post(event.x_root, event.y_root)

    basket_tree.bind("<Button-3>", on_basket_right_click)

    # -- Drag-drop reordering in basket (just moves items within same parent) --
    _drag = {"item": None}
    basket_tree.bind(
        "<ButtonPress-1>",
        lambda e: _drag.update({"item": basket_tree.identify_row(e.y)})
    )
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
    total_spolu_var = tk.StringVar(value="Spolu: 0.00")
    tk.Label(total_frame, textvariable=total_spolu_var, anchor="e").pack(
        side="right", padx=10
    )

    # ─── Notes button ─────────────────────────────────────────────────────
    

    # ─── NEW Position: Recommendations Label & Treeview ───────────────────
    tk.Label(basket_frame, text="Doporučené položky:").pack(anchor="w", pady=(10, 0))

    # Now include an extra, _hidden_ column at the end called "_section"
    recom_columns = (
        "produkt",
        "jednotky",
        "dodavatel",
        "odkaz",
        "koeficient_material",
        "nakup_materialu",
        "cena_prace",
        "koeficient_prace",
        "_section"     # <-- hidden column
    )
    # Display only the first 8 columns; hide "_section"
    visible_recom_cols = recom_columns[:-1]

    recom_tree = ttk.Treeview(
        basket_frame,
        columns=recom_columns,
        show="headings",
        displaycolumns=visible_recom_cols,  # hide "_section"
        height=4  # show up to 4 rows by default
    )
    # Set up the first 8 column headings (visible):
    for c in visible_recom_cols:
        recom_tree.heading(c, text=c.capitalize())
        recom_tree.column(c, anchor="center", stretch=True)
    # Now configure the hidden "_section" column with zero width:
    recom_tree.heading("_section", text="")         # no heading text
    recom_tree.column("_section", width=0, stretch=False)

    recom_tree.pack(fill="x", expand=False, pady=(0, 5))

    # When you double-click a recommendation, insert it into the basket
    # We do get all 9 fields (including section) out of .item()["values"].
    recom_tree.bind(
        "<Double-1>",
        lambda e: add_to_basket_full(
            recom_tree.item(recom_tree.focus())["values"],
            basket_items,
            original_basket,
            conn, cursor, db_type,
            basket_tree,
            mark_modified
        )
    )
    # ──────────────────────────────────────────────────────────────────────────

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
            remove_from_basket(basket_tree, basket_items, update_basket_table),
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
            basket_items,
            original_basket,
            total_spolu_var,
            mark_modified
        )
    )
    add_custom_btn.pack(side="left", padx=(0, 10))
    
    notes_btn = tb.Button(
        left_btn_frame,
        text="Poznámky",
        bootstyle="secondary",
        command=lambda: show_notes_popup(project_name, json_dir)
    )
    notes_btn.pack(side="left", padx=(0, 10))

    export_btn = tb.Button(
        left_btn_frame,
        text="Exportovať",
        bootstyle="success",
        command=lambda: (
            reorder_basket_data(basket_tree, basket_items),
            update_excel_from_basket(
                basket_items,
                project_entry.get(),
                definicia_text=definition_entry.get()
        )
    )
    )
    export_btn.pack(side="left")

    coeff_set_btn = tb.Button(
        right_btn_frame,
        text="Nastav koeficient",
        bootstyle="info-outline",
        command=lambda: apply_global_coefficient(
            basket_items,
            basket_tree,
            base_coeffs,
            total_spolu_var,
            mark_modified
        )
    )
    coeff_set_btn.pack(side="left", padx=(0, 10))

    coeff_revert_btn = tb.Button(
        right_btn_frame,
        text="Revert koeficient",
        bootstyle="warning-outline",
        command=lambda: revert_coefficient(
            basket_items,
            basket_tree,
            base_coeffs,
            total_spolu_var,
            mark_modified
        )
    )
    coeff_revert_btn.pack(side="left")
    # ──────────────────────────────────────────────────────────────────────────

    # ─── Initialize basket state ──────────────────────────────────────────
    basket_items = OrderedDict()
    original_basket = OrderedDict()
    base_coeffs = {}  # for global coefficient revert

    basket_items_loaded, saved = load_basket(json_dir, project_name, file_path=commit_file)
    for sec, prods in basket_items_loaded.items():
        original_basket.setdefault(sec, OrderedDict()).update(prods)
    basket_items.update(basket_items_loaded)
    update_basket_table(basket_tree, basket_items)
    recompute_total_spolu(basket_items, total_spolu_var)

    # ─── Initial filtering of DB results ─────────────────────────────────
    apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

    # ─── Ensure basket columns display matches checkboxes ───
    def update_displayed_columns():
        visible = [col for col, var in column_vars.items() if var.get()]
        if not visible:
            visible = ["produkt"]
            column_vars["produkt"].set(True)
        basket_tree.config(displaycolumns=visible)
        adjust_basket_columns(tk.Event(width=basket_tree.winfo_width()))

    update_displayed_columns()

    # ── REPLACE the old DB-double-click binding with this new one ─────────────
    def on_db_double_click(event):
        """
        Called when the user double-clicks a row in the main DB Treeview (`tree`):
        1) Add exactly that product into the basket (silently).
        2) Kick off fetch_recommendations_async(...) in a background thread.
        """
        selected = tree.item(tree.focus())
        if not selected:
            return
        db_values = selected["values"]
        base_name = db_values[0]

        # 1) Insert base product into the basket
        add_to_basket_full(
            db_values,
            basket_items,
            original_basket,
            conn, cursor, db_type,
            basket_tree,
            mark_modified
        )

        # 2) Kick off the async recommendation fetch
        fetch_recommendations_async(
            conn=conn,
            cursor=cursor,
            db_type=db_type,
            base_product_name=base_name,
            basket_items=basket_items,
            root=root,
            recom_tree=recom_tree,
            max_recs=3
        )

    tree.bind("<Double-1>", on_db_double_click)
    # ───────────────────────────────────────────────────────────────────────────

    # ─── Handle window close (“X”) ────────────────────────────────────────
    def on_closing():
        resp = tk.messagebox.askyesnocancel(
            "Uložiť zmeny?",
            "Chceš uložiť zmeny pred zatvorením košíka?"
        )
        if resp is None:
            return  # Cancel → do nothing
        if resp is False:
            root.destroy()
            return

        reorder_basket_data(basket_tree, basket_items)
        default_base = "basket"
        fname = tk.simpledialog.askstring(
            "Košík — Uložiť ako",
            "Zadaj názov súboru (bez prípony):",
            initialvalue=default_base,
            parent=root
        )
        if not fname:
            return  # user canceled → stay open

        ts = datetime.now().strftime("_%Y-%m-%d")
        filename = f"{fname}{ts}.json"
        fullpath = os.path.join(json_dir, filename)

        if os.path.exists(fullpath):
            if not tk.messagebox.askyesno(
                "Prepis existujúceho súboru?",
                f"“{filename}” už existuje. Chceš ho prepísať?"
            ):
                return

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

        try:
            with open(fullpath, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror(
                "Chyba pri ukladaní",
                f"Nepodarilo sa uložiť súbor:\n{e}"
            )
            return

        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    project_dir = sys.argv[1]
    json_path   = sys.argv[2]
    start(project_dir, json_path)
