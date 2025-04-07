import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import sys
import shutil
from datetime import datetime
from collections import OrderedDict
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
    update_basket_table,
    add_to_basket,
    edit_pocet_cell,
    remove_from_basket,
    update_excel_from_basket
)
import json

def run_gui(project_path, basket_version=None):
    project_name = os.path.basename(project_path)
    conn, db_type = get_database_connection()
    cursor = conn.cursor()
    if db_type == 'postgres':
        sync_postgres_to_sqlite(conn)

    root = tk.Tk()
    root.state('zoomed')
    root.title(f"Project: {project_name}")

    basket_items = OrderedDict()
    metadata_label = tk.StringVar()

    def save_current_state():
        user_name = user_name_entry.get().strip()
        data = {
            "basket": basket_items,
            "user_name": user_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        custom_name = simpledialog.askstring("Názov archívu", "Zadaj názov pre uložený súbor:")
        if not custom_name:
            custom_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_file = os.path.join(project_path, f"project_{custom_name}.json")
        with open(archive_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        notes_file = f"{project_name}_notes.txt"
        if os.path.exists(notes_file):
            shutil.copy(notes_file, os.path.join(project_path, f"notes_{custom_name}.txt"))
        messagebox.showinfo("Uložené", f"✅ Uložené ako: {custom_name}")
        metadata_label.set(f"Súbor: {custom_name} | Dátum: {data['timestamp']} | Autor: {user_name}")

    def return_home():
        user_name = user_name_entry.get().strip()
        data = {"basket": basket_items, "user_name": user_name}
        with open(os.path.join(project_path, "project.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        conn.close()
        root.destroy()

    category_structure = {}
    cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
    for class_id, main_cat, tab_name in cursor.fetchall():
        category_structure.setdefault(main_cat, []).append((class_id, tab_name))

    filter_frame, setup_category_tree, category_vars, table_vars = create_filter_panel(
        root,
        lambda: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)
    )
    filter_frame.config(width=280)
    filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0), pady=5)
    setup_category_tree(category_structure)

    main_frame = tk.Frame(root)
    main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    top_frame = tk.Frame(main_frame)
    top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    home_button = tk.Button(top_frame, text="🏠 Home", command=return_home)
    home_button.pack(side=tk.LEFT, padx=(0, 10))

    save_button = tk.Button(top_frame, text="💾 Uložiť", command=save_current_state)
    save_button.pack(side=tk.LEFT, padx=(0, 10))

    tk.Label(top_frame, text="Tvoje meno:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
    user_name_entry = tk.Entry(top_frame, width=20)
    user_name_entry.pack(side=tk.LEFT, padx=(0, 15))

    metadata_display = tk.Label(top_frame, textvariable=metadata_label, font=("Arial", 9), fg="gray")
    metadata_display.pack(side=tk.RIGHT)

    def on_name_change(*args):
        export_button.config(state=(tk.NORMAL if user_name_entry.get().strip() else tk.DISABLED))

    user_name_entry.bind("<KeyRelease>", lambda event: on_name_change())

    tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    name_entry = tk.Entry(top_frame, width=30)
    name_entry.pack(side=tk.LEFT, padx=5)
    name_entry.bind("<KeyRelease>", lambda event: apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree))

    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

    columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True)

    def on_tree_double_click(event):
        selected = tree.focus()
        values = tree.item(selected)["values"]
        if not values or "--" in str(values[1]):
            return
        add_to_basket(values, basket_items, update_basket_table, basket_tree)

    tree.bind("<Double-1>", on_tree_double_click)

    basket_frame = tk.Frame(main_frame)
    basket_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
    tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10)).pack()

    basket_columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace", "pocet")
    basket_tree = ttk.Treeview(basket_frame, columns=basket_columns, show="tree headings")
    for col in basket_columns:
        basket_tree.heading(col, text=col.capitalize())
        basket_tree.column(col, anchor="center")
    basket_tree.pack(fill=tk.BOTH, expand=True)

    # Drag preview setup
    ghost_label = None
    canvas = tk.Canvas(basket_tree, highlightthickness=0, bd=0, bg="SystemWindow")

    def on_drag_start(event):
        nonlocal ghost_label
        iid = basket_tree.identify_row(event.y)
        if iid:
            label = basket_tree.item(iid)['text'] or basket_tree.item(iid)['values'][0]
            if ghost_label:
                ghost_label.destroy()
            ghost_label = tk.Label(root, text=label, bg="lightyellow", relief="solid", bd=1)
            ghost_label.place(x=event.x_root + 10, y=event.y_root + 10)
            canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

    def on_drag_motion(event):
        if ghost_label:
            ghost_label.place(x=event.x_root + 10, y=event.y_root + 10)
        canvas.delete("all")
        iid = basket_tree.identify_row(event.y)
        if iid:
            bbox = basket_tree.bbox(iid)
            if bbox:
                y = bbox[1]
                h = bbox[3]
                drop_y = y if event.y < (y + h // 2) else y + h
                canvas.create_rectangle(2, drop_y - 1, basket_tree.winfo_width() - 2, drop_y + 1, fill="red", outline="", width=0)

    def on_drag_release(event):
        if ghost_label:
            ghost_label.destroy()
        canvas.delete("all")
        canvas.place_forget()

    basket_tree.bind("<ButtonPress-1>", on_drag_start)
    basket_tree.bind("<B1-Motion>", on_drag_motion)
    basket_tree.bind("<ButtonRelease-1>", on_drag_release)

    create_notes_panel(basket_frame, project_name)
    basket_tree.bind("<Double-1>", lambda e: edit_pocet_cell(e, basket_tree, basket_items, update_basket_table))
    tk.Button(basket_frame, text="Odstrániť", command=lambda: remove_from_basket(basket_tree, basket_items, update_basket_table)).pack(pady=3)

    def try_export():
        user_name = user_name_entry.get().strip()
        if not user_name:
            messagebox.showwarning("Meno chýba", "⚠ Prosím zadaj svoje meno pred exportom.")
            return
        update_excel_from_basket(basket_items, project_name)

    export_button = tk.Button(basket_frame, text="Exportovať", command=try_export, state=tk.DISABLED)
    export_button.pack(pady=3)

    on_name_change()

    basket_file = os.path.join(project_path, basket_version) if basket_version else os.path.join(project_path, "project.json")
    if os.path.exists(basket_file):
        with open(basket_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                basket_items.update(OrderedDict(data.get("basket", {})))
                user_name_entry.insert(0, data.get("user_name", ""))
                timestamp = data.get("timestamp", "")
                metadata_label.set(f"Súbor: {os.path.basename(basket_file)} | Dátum: {timestamp} | Autor: {data.get('user_name', '')}")
            except json.JSONDecodeError:
                print("⚠ Could not load project file")

    update_basket_table(basket_tree, basket_items)
    apply_filters(cursor, db_type, table_vars, category_vars, name_entry, tree)

    root.protocol("WM_DELETE_WINDOW", return_home)
    root.mainloop()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ No project path provided.")
        sys.exit(1)
    path = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None
    run_gui(path, version)
