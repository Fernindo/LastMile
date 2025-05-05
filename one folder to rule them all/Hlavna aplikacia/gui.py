import sys
import os
import subprocess
import copy
from collections import OrderedDict

import ttkbootstrap as tb
from ttkbootstrap import Style
import tkinter as tk
from tkinter import messagebox, simpledialog
import tkinter.ttk as ttk

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
        "produkt":         0.22,  # a bit more room for long names
        "jednotky":        0.15,
        "dodavatel":       0.12,
        "odkaz":           0.20,  # trimmed down from 30%
        "koeficient":      0.10,  # up from .08
        "nakup_materialu": 0.13,  # up from .12
        "cena_prace":      0.08,  # down from .10
    }
    def adjust_db_columns(event):
        total = event.width
        for col, pct in db_column_proportions.items():
            tree.column(col, width=int(total * pct), stretch=True)

    # ─── Basket Table Helpers (responsive columns)
    basket_columns = (
        "produkt", "jednotky", "dodavatel", "odkaz",
        "koeficient", "nakup_materialu", "pocet_materialu",
        "cena_prace", "pocet_prace"
    )
    basket_column_proportions = {
        "produkt":         0.12,
        "jednotky":        0.07,
        "dodavatel":       0.12,
        "odkaz":           0.16,
        "koeficient":      0.10,
        "nakup_materialu": 0.12,
        "pocet_materialu": 0.12,
        "cena_prace":      0.07,
        "pocet_prace":     0.071,
    }
    def adjust_basket_columns(event):
        total = event.width
        icon_w = int(total * 0.11)
        # keep expand/collapse icon small & fixed
        basket_tree.column("#0", width=icon_w, anchor="w", stretch=False)
        avail = max(total - icon_w, 100)
        for col, pct in basket_column_proportions.items():
            basket_tree.column(col, width=int(avail * pct), stretch=True)

    def update_basket_table(basket_tree, basket_items):
        basket_tree.delete(*basket_tree.get_children())
        for section, products in basket_items.items():
            sec_id = basket_tree.insert("", "end", text=section, open=True)
            for produkt, d in products.items():
                basket_tree.insert(
                    sec_id, "end", text="",  # first column blank
                    values=(
                        produkt,
                        d.get("jednotky",""),
                        d.get("dodavatel",""),
                        d.get("odkaz",""),
                        float(d.get("koeficient",0)),
                        float(d.get("nakup_materialu",0)),
                        int(d.get("pocet_materialu",1)),
                        float(d.get("cena_prace",0)),
                        int(d.get("pocet_prace",1))
                    )
                )

    def reorder_basket_data():
        new_basket = OrderedDict()
        for sec in basket_tree.get_children(""):
            sec_name = basket_tree.item(sec, "text")
            prods = OrderedDict()
            for child in basket_tree.get_children(sec):
                vals = basket_tree.item(child, "values")
                prods[vals[0]] = {
                    "jednotky": vals[1],
                    "dodavatel": vals[2],
                    "odkaz": vals[3],
                    "koeficient": float(vals[4]),
                    "nakup_materialu": float(vals[5]),
                    "pocet_materialu": int(vals[6]),
                    "cena_prace": float(vals[7]),
                    "pocet_prace": int(vals[8])
                }
            new_basket[sec_name] = prods
        basket_items.clear()
        basket_items.update(new_basket)

    # ─── Define add_to_basket *before* binding it on the DB tree
    def add_to_basket(item):
        produkt, jednotky, dodavatel, odkaz, koef, nakup = item[:6]
        data = {
            'jednotky': jednotky,
            'dodavatel': dodavatel,
            'odkaz': odkaz,
            'koeficient': float(koef),
            'nakup_materialu': float(nakup),
            'cena_prace': float(item[6]) if len(item)>6 else 0.0,
            'pocet_materialu': 1,
            'pocet_prace': 1,
        }
        section = item[7] if len(item) > 7 else 'Uncategorized'
        if section not in basket_items:
            basket_items[section] = OrderedDict()
        if produkt in basket_items[section]:
            basket_items[section][produkt]['pocet_materialu'] += 1
            basket_items[section][produkt]['pocet_prace']    += 1
        else:
            basket_items[section][produkt] = data
            original_basket.setdefault(section, OrderedDict())[produkt] = copy.deepcopy(data)
        update_basket_table(basket_tree, basket_items)
        mark_modified()

    # ─── Edit basket cell on double-click
    def edit_basket_cell(event):
        row = basket_tree.identify_row(event.y)
        col = basket_tree.identify_column(event.x)
        if not row or basket_tree.parent(row) == "":
            return
        idx = int(col.replace("#","")) - 1
        if idx < 4 or idx > 8:
            return
        old = basket_tree.set(row, col)
        names = [
            "Produkt","Jednotky","Dodavatel","Odkaz","Koeficient",
            "Nakup_materialu","Pocet_materialu","Cena_prace","Pocet_prace"
        ]
        prompt = f"Nová hodnota pre '{names[idx]}'"
        if idx in (6,8):
            new = simpledialog.askinteger("Upraviť bunku", prompt, initialvalue=int(old), parent=root)
        else:
            new = simpledialog.askfloat("Upraviť bunku", prompt, initialvalue=float(old), parent=root)
        if new is None:
            return
        basket_tree.set(row, col, new)
        sec = basket_tree.parent(row)
        prod = basket_tree.item(row)["values"][0]
        key_map = {4:"koeficient",5:"nakup_materialu",6:"pocet_materialu",
                   7:"cena_prace",8:"pocet_prace"}
        basket_items[sec][prod][key_map[idx]] = new
        mark_modified()

    # ─── Reset logic via right-click context menu
    def reset_item(iid):
        sec = basket_tree.parent(iid)
        if not sec:
            return
        prod = basket_tree.item(iid)["values"][0]
        orig = original_basket.get(basket_tree.item(sec,'text'), {}).get(prod)
        if not orig:
            messagebox.showinfo("Chýba originál","Pôvodné hodnoty nie sú k dispozícii.")
            return
        for k in ("koeficient","nakup_materialu","pocet_materialu","cena_prace","pocet_prace"):
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

    # ─── Return Home
    def return_home():
        if basket_modified:
            reorder_basket_data()
            save_basket(json_dir, project_name, basket_items)
            """
            save_basket(json_dir, project_name, basket_items, user_name_entry.get().strip())
            """
        conn.close()
        root.destroy()
        subprocess.Popen([sys.executable, os.path.join(project_dir,"launcher.exe")], cwd=project_dir)

    # ─── Build UI ─────────────────────────────────────────────────────
    # Filter panel
    category_structure = {}
    cursor.execute("SELECT id,hlavna_kategoria,nazov_tabulky FROM class")
    for cid, main_cat, tablename in cursor.fetchall():
        category_structure.setdefault(main_cat,[]).append((cid,tablename))
    filter_frame, setup_cat_tree, category_vars, table_vars = create_filter_panel(
        root, lambda: apply_filters(cursor,db_type,table_vars,category_vars,name_entry,tree)
    )
    filter_frame.config(width=280)
    filter_frame.pack(side="left",fill="y",padx=10,pady=10)
    setup_cat_tree(category_structure)

    # Main area
    main_frame = tb.Frame(root,padding=10)
    main_frame.pack(side="left",fill="both",expand=True)

    # Top bar
    top = tb.Frame(main_frame,padding=5)
    top.pack(side="top",fill="x")
    tb.Button(top,text="🏠 Home",bootstyle="light",command=return_home).pack(side="left")
    """
    tb.Label(top,text="Tvoje meno:").pack(side="left",padx=(10,5))
    user_name_entry = tb.Entry(top,width=20)
    user_name_entry.pack(side="left")
    """
    tb.Label(top,text="Vyhľadávanie:").pack(side="left",padx=(20,5))
    name_entry = tb.Entry(top,width=30)
    name_entry.pack(side="left")
    name_entry.bind("<KeyRelease>",lambda e: apply_filters(cursor,db_type,table_vars,category_vars,name_entry,tree))

    # Database tree
    tree_frame = tb.Frame(main_frame)
    tree_frame.pack(fill="both",expand=True,padx=10,pady=10)
    db_columns = ("produkt","jednotky","dodavatel","odkaz","koeficient","nakup_materialu","cena_prace")
    tree = ttk.Treeview(tree_frame,columns=db_columns,show="headings")
    for c in db_columns:
        tree.heading(c,text=c.capitalize())
        tree.column(c,anchor="center",stretch=True)
    tree.pack(fill="both",expand=True)
    tree.bind("<Configure>",adjust_db_columns)
    tree.bind("<Double-1>",lambda e: add_to_basket(tree.item(tree.focus())["values"]))

    # Basket tree
    basket_items = OrderedDict()
    original_basket = OrderedDict()
    basket_frame = tb.Frame(main_frame,padding=5)
    basket_frame.pack(fill="both",expand=True,padx=10,pady=10)
    tb.Label(basket_frame,text="Košík - vybraté položky:").pack(anchor="w")

    basket_tree = ttk.Treeview(basket_frame,columns=basket_columns,show="tree headings")
    basket_tree.heading("#0",text="")
    basket_tree.column("#0",width=20,anchor="w",stretch=False)
    for c in basket_columns:
        basket_tree.heading(c,text=c.capitalize())
        basket_tree.column(c,anchor="center",stretch=True)
    basket_tree.pack(fill="both",expand=True)
    basket_tree.bind("<Configure>",adjust_basket_columns)
    basket_tree.bind("<Double-1>",edit_basket_cell)
    basket_tree.bind("<Button-3>",on_basket_right_click)

    # Drag-drop
    _drag={"item":None}
    basket_tree.bind("<ButtonPress-1>",lambda e: _drag.update({"item":basket_tree.identify_row(e.y)}))
    basket_tree.bind("<B1-Motion>",lambda e: (
        basket_tree.move(_drag["item"],basket_tree.parent(_drag["item"]),basket_tree.index(basket_tree.identify_row(e.y)))
        if (_drag.get("item") and basket_tree.parent(basket_tree.identify_row(e.y))==basket_tree.parent(_drag["item"])) else None
    ))
    basket_tree.bind("<ButtonRelease-1>",lambda e:_drag.update({"item":None}))

    # Notes panel
    create_notes_panel(basket_frame,project_name)

    # Remove & Export buttons
    tb.Button(
        basket_frame,
        text="Odstrániť",
        bootstyle="danger-outline",
        command=lambda: (remove_from_basket(basket_tree,basket_items,update_basket_table),mark_modified())
    ).pack(pady=3)
    export_btn = tb.Button(
        
        basket_frame,
        text="Exportovať",
        bootstyle="success",
        command=lambda: (    
            
           update_excel_from_basket(basket_items,project_name)
        )
    )
    export_btn.pack(pady=3)
    """
    def on_name_change(*_):
        export_btn.config(state=tb.DISABLED if not user_name_entry.get().strip() else tb.NORMAL)
    user_name_entry.bind("<KeyRelease>",on_name_change)
    on_name_change()

    """
    
    # Initial load & record originals
    basket_items_loaded, saved = load_basket(json_dir,project_name,file_path=commit_file)
    for sec, prods in basket_items_loaded.items():
        original_basket.setdefault(sec,OrderedDict()).update(copy.deepcopy(prods))
    basket_items.update(basket_items_loaded)
    update_basket_table(basket_tree,basket_items)

    # Initial filter
    apply_filters(cursor,db_type,table_vars,category_vars,name_entry,tree)

    # Closing handler
    def on_closing():
        ans = messagebox.askyesnocancel(
            "Uložiť zmeny?",
            "Chceš uložiť zmeny pred zatvorením košíka?"
        )
        if ans is None:
            return
        if ans:
            reorder_basket_data()
            save_basket(json_dir,project_name,basket_items,)
        conn.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
