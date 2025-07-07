# gui.py

import sys
import os
import sqlite3
import tkinter as tk
import tkinter.ttk as ttk
import ttkbootstrap as tb
import json
import datetime
import tkinter.simpledialog
from datetime import datetime
from ttkbootstrap import Style
from collections import OrderedDict
from praca import show_praca_window

from gui_functions import (
    is_online,
    get_database_connection,
    sync_postgres_to_sqlite,
    save_basket,
    load_basket,
    show_error,
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
    show_notes_popup
)

from filter_panel import create_filter_panel
from excel_processing import update_excel
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
    main_frame = tb.Frame(root, padding=10)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # DB toggle
    db_visible = [True]
    def toggle_db_view():
        if db_visible[0]:
            tree_frame.pack_forget()
            toggle_btn.config(text="🔼 Zobraziť databázu")
        else:
            tree_frame.pack(
                in_=main_frame,
                before=basket_frame,
                fill="both",
                expand=True,
                padx=10,
                pady=10
            )
            toggle_btn.config(text="🔽 Skryť databázu")
        db_visible[0] = not db_visible[0]

    # Basket toggle
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

    filter_container, filter_frame, setup_cat_tree, category_vars, table_vars = create_filter_panel(
        root,
        lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
    )
    filter_container.config(width=350)
    setup_cat_tree(category_structure)

    filter_visible = [False]
    def toggle_filter():
        if filter_visible[0]:
            filter_container.grid_forget()
            main_frame.grid(row=0, column=0, sticky="nsew")
            root.grid_columnconfigure(0, weight=1)
            filter_toggle_btn.config(text="▶")
        else:
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
    initial_db_display = list(db_columns)

    # ─── DB column toggles ────────────────────────────────────────────────
    db_checkbox_frame = tb.LabelFrame(tree_frame, text="Zobraziť stĺpce:", padding=5)
    db_checkbox_frame.pack(fill="x", pady=(0, 5))
    for col in db_columns:
        var = tk.BooleanVar(value=True)
        db_column_vars[col] = var
        chk = tk.Checkbutton(
            db_checkbox_frame,
            text=col.capitalize(),
            variable=var,
            command=update_displayed_db_columns
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
        for col, pct in proportions.items():
            tree.column(col, width=int(total * pct), stretch=True)

    def update_displayed_db_columns():
        visible = [col for col, var in db_column_vars.items() if var.get()]
        if not visible:
            visible = ["produkt"]
            db_column_vars["produkt"].set(True)
        tree.config(displaycolumns=visible)
        adjust_db_columns(tk.Event(width=tree.winfo_width()))

    tree.bind("<Configure>", adjust_db_columns)

    # ─── Basket Area (reworked) ──────────────────────────────────────────
    basket_frame = tb.Frame(main_frame, padding=5)
    basket_frame.pack(fill="both", expand=True, padx=10, pady=10)
    tk.Label(basket_frame, text="Košík - vybraté položky:").pack(anchor="w")

    # Column toggles above the treeview
    basket_columns = (
        "produkt",
        "jednotky",
        "dodavatel",
        "odkaz",
        "nakup_materialu",
        "koeficient_material",
        "predaj_material",
        "pocet_materialu",
        "cena_prace",
        "koeficient_prace",
        "predaj_praca",
        "pocet_prace"
    )
    column_vars = {}
    checkbox_frame = tb.LabelFrame(basket_frame, text="Zobraziť stĺpce:", padding=5)
    checkbox_frame.pack(fill="x", pady=(3, 8))
    
    for col in basket_columns:
        var = tk.BooleanVar(value=(col != "odkaz"))
        column_vars[col] = var
        chk = tk.Checkbutton(
            checkbox_frame,
            text=col.capitalize(),
            variable=var,
            command=update_displayed_columns
        )
        chk.pack(side="left", padx=5)

    # Basket Treeview
    basket_tree_container = tb.Frame(basket_frame)
    basket_tree_container.pack(fill="both", expand=True)
    basket_scroll_y = ttk.Scrollbar(basket_tree_container, orient="vertical")
    basket_scroll_x = ttk.Scrollbar(basket_tree_container, orient="horizontal")
    basket_scroll_y.pack(side="right", fill="y")
    basket_scroll_x.pack(side="bottom", fill="x")

    initial_display = [c for c in basket_columns if c != "odkaz"]
    basket_tree = ttk.Treeview(
        basket_tree_container,
        columns=basket_columns,
        show="tree headings",
        displaycolumns=initial_display,
        yscrollcommand=basket_scroll_y.set,
        xscrollcommand=basket_scroll_x.set
    )
    basket_tree.heading("#0", text="")
    basket_tree.column("#0", width=20, anchor="w", stretch=False)
    for c in basket_columns:
        basket_tree.heading(c, text=c.capitalize())
        basket_tree.column(c, anchor="center", stretch=True)
    basket_tree.pack(fill="both", expand=True)
    basket_scroll_y.config(command=basket_tree.yview)
    basket_scroll_x.config(command=basket_tree.xview)

    def adjust_visible_basket_columns(event=None):
        total = basket_tree.winfo_width()
        if total <= 0: return
        icon_w = max(int(total * 0.11), 20)
        basket_tree.column("#0", width=icon_w, stretch=False)
        avail = max(total - icon_w, 100)
        vis = basket_tree.cget("displaycolumns")
        if isinstance(vis, str): vis = (vis,)
        proportions = {
            "produkt":             0.13,
            "jednotky":            0.07,
            "dodavatel":           0.12,
            "odkaz":               0.16,
            "nakup_materialu":     0.07,
            "koeficient_material": 0.07,
            "predaj_material":     0.07,
            "pocet_materialu":     0.07,
            "cena_prace":          0.07,
            "koeficient_prace":    0.07,
            "predaj_praca":        0.07,
            "pocet_prace":         0.07,
        }
        total_w = sum(proportions[c] for c in vis)
        for c in vis:
            pct = proportions[c] / total_w
            basket_tree.column(c, width=int(avail * pct), stretch=True)

    basket_tree.bind("<Configure>", adjust_visible_basket_columns)

    # Recalc helpers
    def recalc_predaj():
        """Recompute predaj_material & predaj_praca on every item."""
        for sec, prods in basket_items.items():
            for info in prods.values():
                qty_m = info.get("pocet_materialu", 1) or 1
                info["predaj_material"] = (
                    info.get("nakup_materialu", 0)
                    * info.get("koeficient_material", 1)
                    / qty_m
                )
                qty_p = info.get("pocet_prace", 1) or 1
                info["predaj_praca"] = (
                    info.get("cena_prace", 0)
                    * info.get("koeficient_prace", 1)
                    / qty_p
                )

    def refresh_basket():
        """Recalc, redraw, and update total."""
        recalc_predaj()
        update_basket_table(basket_tree, basket_items)
        recompute_total_spolu(basket_items, total_spolu_var)

    # Inline edit on double-click
    def on_basket_double_click(event):
        row = basket_tree.identify_row(event.y)
        col = basket_tree.identify_column(event.x)
        if not row or basket_tree.parent(row) == "": return
        idx = int(col.replace("#", "")) - 1
        if idx in (6, 9): return  # skip computed columns
        old = basket_tree.set(row, col)
        name = basket_columns[idx]
        if name in ("pocet_materialu", "pocet_prace"):
            new = simpledialog.askinteger(
                "Upraviť", f"Nová hodnota pre '{name}'", initialvalue=int(old), parent=root
            )
        else:
            new = simpledialog.askfloat(
                "Upraviť", f"Nová hodnota pre '{name}'", initialvalue=float(old), parent=root
            )
        if new is None: return

        sec = basket_tree.parent(row)
        prod = basket_tree.item(row)["values"][0]
        key_map = {
            1: "jednotky",
            2: "dodavatel",
            3: "odkaz",
            4: "nakup_materialu",
            5: "koeficient_material",
            7: "cena_prace",
            8: "koeficient_prace",
            10: "pocet_materialu",
            11: "pocet_prace"
        }
        if idx in key_map:
            basket_items[basket_tree.item(sec, "text")][prod][key_map[idx]] = new

        mark_modified()
        refresh_basket()

    basket_tree.bind("<Double-1>", on_basket_double_click)

    # Notes button
    notes_btn = tb.Button(
        basket_frame,
        text="Poznámky",
        bootstyle="secondary",
        command=lambda: show_notes_popup(project_name, json_dir)
    )
    notes_btn.pack(anchor="w", pady=(10, 0))

    # Buttons row
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
            mark_modified(),
            recompute_total_spolu(basket_items, total_spolu_var)
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

    # Grand Total
    total_frame = tk.Frame(basket_frame)
    total_frame.pack(fill="x", pady=(2, 0))
    total_spolu_var = tk.StringVar(value="Spolu: 0.00")
    tk.Label(total_frame, textvariable=total_spolu_var, anchor="e").pack(
        side="right", padx=10
    )

    # Initialize basket state
    basket_items = OrderedDict()
    original_basket = OrderedDict()
    base_coeffs = {}

    loaded, saved = load_basket(json_dir, project_name, file_path=commit_file)
    for sec, prods in loaded.items():
        original_basket.setdefault(sec, OrderedDict()).update(prods)
    basket_items.update(loaded)

    refresh_basket()

    # Initial filtering and DB double-click
    apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

    def on_db_double_click(event):
        sel = tree.item(tree.focus())
        if not sel: return
        vals = sel["values"]
        add_to_basket_full(
            vals,
            basket_items,
            original_basket,
            conn, cursor, db_type,
            basket_tree,
            mark_modified
        )
        refresh_basket()

    tree.bind("<Double-1>", on_db_double_click)

    # Handle window close
    def on_closing():
        resp = messagebox.askyesnocancel(
            "Uložiť zmeny?",
            "Chceš uložiť zmeny pred zatvorením košíka?"
        )
        if resp is None:
            return
        if resp is False:
            root.destroy()
            return

        reorder_basket_data(basket_tree, basket_items)
        fname = simpledialog.askstring(
            "Košík — Uložiť ako",
            "Zadaj názov súboru (bez prípony):",
            initialvalue="basket",
            parent=root
        )
        if not fname:
            return

        ts = datetime.now().strftime("_%Y-%m-%d")
        filename = f"{fname}{ts}.json"
        fullpath = os.path.join(json_dir, filename)

        if os.path.exists(fullpath):
            if not messagebox.askyesno(
                "Prepis existujúceho súboru?",
                f"“{filename}” už existuje. Chceš ho prepísať?"
            ):
                return

        out = {"project": project_name, "items": []}
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
            messagebox.showerror("Chyba pri ukladaní", f"Nepodarilo sa uložiť súbor:\n{e}")
            return

        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    project_dir = sys.argv[1]
    json_path   = sys.argv[2]
    start(project_dir, json_path)
