import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import sys
import shutil
from datetime import datetime
from collections import OrderedDict
import json
import socket
import sqlite3
import psycopg2
import decimal
import unicodedata

def is_online(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def get_database_connection():
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
    conn = sqlite3.connect("local_backup.db")
    print("🕠 Using local SQLite database (offline mode)")
    return conn, 'sqlite'

def sync_postgres_to_sqlite(pg_conn):
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
        SELECT p.id, p.produkt, p.jednotky, p.dodavatel, p.odkaz,
               p.koeficient, p.nakup_materialu, p.cena_prace,
               c.id::INTEGER, c.nazov_tabulky
        FROM produkty p
        JOIN class c ON p.class_id = c.id

    """)
    rows = pg_cursor.fetchall()
    safe_rows = []
    for row in rows:
        new_row = []
        for val in row:
            if isinstance(val, decimal.Decimal):
                new_row.append(float(val))
            else:
                new_row.append(val)
        safe_rows.append(tuple(new_row))
    sqlite_cursor.executemany("INSERT INTO produkty VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", safe_rows)
    sqlite_conn.commit()
    sqlite_conn.close()
    print("✔ Synced PostgreSQL → SQLite")

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def apply_filters(cursor, db_type, subcat_vars, name_entry, tree):
    selected_subcategories = [name for name, var in subcat_vars.items() if var.get()]
    print("[DEBUG] selected subcategories:", selected_subcategories)

    name_filter_raw = name_entry.get().strip().lower()
    name_filter = remove_accents(name_filter_raw)
    tokens = name_filter.split() if name_filter else []

    query = """
        SELECT p.produkt, p.jednotky, p.dodavatel, p.odkaz,
               p.koeficient, p.nakup_materialu, p.cena_prace,
               c.hlavna_kategoria, c.nazov_tabulky
        FROM produkty p
        JOIN class c ON p.class_id = c.id
        WHERE 1=1
    """
    params = []
    if selected_subcategories:
        placeholders = ','.join(['%s' if db_type == 'postgres' else '?' for _ in selected_subcategories])
        query += f" AND c.nazov_tabulky IN ({placeholders})"
        params.extend(selected_subcategories)

    print("[DEBUG] SQL:", query)
    print("[DEBUG] Params:", params)

    try:
        cursor.execute(query, tuple(params))
        all_rows = cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Chyba", f"Database error:\n{e}")
        return

    print(f"[DEBUG] DB returned {len(all_rows)} rows before text search.")

    filtered_rows = []
    for row in all_rows:
        produkt = row[0] or ""
        dodavatel = row[2] or ""
        norm_produkt = remove_accents(produkt.lower())
        norm_dodavatel = remove_accents(dodavatel.lower())
        if tokens and not all(token in norm_produkt or token in norm_dodavatel for token in tokens):
            continue
        filtered_rows.append(row)

    print(f"[DEBUG] After text filter: {len(filtered_rows)} rows.")

    tree.delete(*tree.get_children())
    filtered_rows.sort(key=lambda r: (r[7], r[8], r[0]))
    grouped = {}
    for row in filtered_rows:
        cat = row[7]
        subcat = row[8]
        grouped.setdefault(cat, {}).setdefault(subcat, []).append(row[:7])

    for cat in sorted(grouped):
        tree.insert("", "end", values=("", f"-- {cat} --"), tags=("header",))
        for subcat in sorted(grouped[cat]):
            tree.insert("", "end", values=("", f"   > {subcat}"), tags=("subheader",))
            for row_data in grouped[cat][subcat]:
                tree.insert("", "end", values=row_data)

    tree.tag_configure("header", font=("Arial", 10, "bold"))
    tree.tag_configure("subheader", font=("Arial", 9, "italic"))



###############################################################################
# 2. BASKET & EXCEL FUNCTIONS
###############################################################################

def update_basket_table(basket_tree, basket_items):
    basket_tree.delete(*basket_tree.get_children())
    for section, products in basket_items.items():
        display_name = f"📁 {section}"
        basket_tree.insert("", "end", iid=section, text=display_name, open=True)
        for produkt, item_data in products.items():
            basket_tree.insert(
                section,
                "end",
                values=(
                    produkt,
                    item_data["jednotky"],
                    item_data["dodavatel"],
                    item_data["odkaz"],
                    item_data["koeficient"],
                    item_data["nakup_materialu"],
                    item_data["cena_prace"],
                    item_data["pocet"]
                )
            )

def add_to_basket(item, basket_items, update_basket_table, basket_tree):
    produkt = item[0]
    class_name = item[7] if len(item) > 7 else "General"
    item_data = {
        "jednotky": item[1],
        "dodavatel": item[2],
        "odkaz": item[3],
        "koeficient": item[4],
        "nakup_materialu": item[5],
        "cena_prace": item[6],
        "pocet": 1
    }
    if class_name not in basket_items:
        basket_items[class_name] = {}
    if produkt in basket_items[class_name]:
        basket_items[class_name][produkt]["pocet"] += 1
    else:
        basket_items[class_name][produkt] = item_data
    update_basket_table(basket_tree, basket_items)

def edit_pocet_cell(event, basket_tree, basket_items, update_basket_table):
    region = basket_tree.identify("region", event.x, event.y)
    if region != "cell":
        return
    selected_item = basket_tree.focus()
    if not selected_item:
        return
    if basket_tree.get_children(selected_item):
        return  # skip parent folder rows
    item_data = basket_tree.item(selected_item)
    if not item_data or not item_data.get("values"):
        return
    col = basket_tree.identify_column(event.x)
    col_index = int(col.replace('#', '')) - 1
    if col_index not in [4, 5, 6, 7]:
        return
    x, y, width, height = basket_tree.bbox(selected_item, col)
    entry_popup = tk.Entry(basket_tree)
    entry_popup.place(x=x, y=y, width=width, height=height)
    entry_popup.insert(0, basket_tree.item(selected_item)['values'][col_index])
    entry_popup.focus()

    def save_edit(event=None):
        try:
            new_value = float(entry_popup.get()) if col_index != 7 else int(entry_popup.get())
        except ValueError:
            entry_popup.destroy()
            return
        produkt = item_data['values'][0]
        parent = basket_tree.parent(selected_item)
        key_map = {4: "koeficient", 5: "nakup_materialu", 6: "cena_prace", 7: "pocet"}
        if parent in basket_items and produkt in basket_items[parent]:
            basket_items[parent][produkt][key_map[col_index]] = new_value
        update_basket_table(basket_tree, basket_items)
        entry_popup.destroy()

    entry_popup.bind("<Return>", save_edit)
    entry_popup.bind("<FocusOut>", save_edit)

def remove_from_basket(basket_tree, basket_items, update_basket_table):
    for item in basket_tree.selection():
        produkt = basket_tree.item(item)["values"][0]
        for section in list(basket_items):
            if produkt in basket_items[section]:
                del basket_items[section][produkt]
                if not basket_items[section]:
                    del basket_items[section]
                break
    update_basket_table(basket_tree, basket_items)

def update_excel_from_basket(basket_items, project_name):
    if not basket_items:
        messagebox.showwarning("Košík je prázdny", "⚠ Nie sú vybraté žiadne položky na export.")
        return
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    file_path = os.path.join(desktop_path, f"{project_name}.xlsx")
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
                v["pocet"]
            ))
    from excel_processing import update_excel
    update_excel(excel_data, file_path)
    messagebox.showinfo("Export hotový", f"✅ Súbor bol úspešne uložený na plochu ako:\n{file_path}")

###############################################################################
# 3. SUBCATEGORY CHECKBOX PANEL (WITH DEBUG PRINTS)
###############################################################################
def create_subcat_checkbox_panel(parent, category_structure, on_filter_callback):
    frame = tk.Frame(parent, bg="white", width=250)
    frame.pack_propagate(False)

    canvas = tk.Canvas(frame, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    main_inner = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=main_inner, anchor="nw")

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    main_inner.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    main_inner.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    main_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    subcat_vars = {}

    tk.Label(main_inner, text="Filtre (subkategórie):",
             font=("Arial", 12, "bold"), bg="white").pack(anchor="w", padx=5, pady=5)

    for cat in sorted(category_structure):
        tk.Label(main_inner, text=cat, font=("Arial", 10, "bold"), bg="white")\
            .pack(anchor="w", padx=5, pady=(5, 1))

        for (class_id, sub_name) in sorted(category_structure[cat], key=lambda x: x[1]):
            var = tk.BooleanVar()
            subcat_vars[sub_name] = var  # <- KEY is the subcategory name from DB

            def var_changed(*args, _sub_name=sub_name, _var=var):
                print(f"[TRACE] Checkbox '{_sub_name}' changed to {_var.get()}")
                on_filter_callback()

            var.trace_add("write", var_changed)

            chk = tk.Checkbutton(
                main_inner,
                text=sub_name,
                variable=var,
                bg="white"
            )
            chk.pack(anchor="w", padx=20, pady=1)

    return frame, subcat_vars






###############################################################################
# 4. MAIN GUI
###############################################################################
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

    # Load the 'class' table
    category_structure = {}
    try:
        cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
        rows = cursor.fetchall()
        print("[DEBUG] class rows =>", rows)
        for class_id, cat, subcat in rows:
            category_structure.setdefault(cat, []).append((class_id, subcat))
        print("[DEBUG] final category_structure =>", category_structure)
    except Exception as e:
        messagebox.showerror("Chyba", f"Couldn't load categories:\n{e}")

    container = tk.Frame(root)
    container.pack(fill=tk.BOTH, expand=True)

    def on_filter_changed():
        apply_filters(cursor, db_type, subcat_vars, name_entry, tree)

    # LEFT subcategory checkboxes
    left_panel, subcat_vars = create_subcat_checkbox_panel(container, category_structure, on_filter_changed)
    left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(5,0), pady=5)

    # MAIN content area
    main_frame = tk.Frame(container)
    main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    top_frame = tk.Frame(main_frame)
    top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    def return_home():
        user_name = user_name_entry.get().strip()
        data = {"basket": basket_items, "user_name": user_name}
        with open(os.path.join(project_path, "project.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        conn.close()
        root.destroy()

    home_button = tk.Button(top_frame, text="🏠 Home", command=return_home)
    home_button.pack(side=tk.LEFT, padx=(0,10))

    def save_current_state():
        user_name = user_name_entry.get().strip()
        data = {
            "basket": basket_items,
            "user_name": user_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    save_button = tk.Button(top_frame, text="💾 Uložiť", command=save_current_state)
    save_button.pack(side=tk.LEFT, padx=(0,10))

    tk.Label(top_frame, text="Tvoje meno:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0,5))
    user_name_entry = tk.Entry(top_frame, width=20)
    user_name_entry.pack(side=tk.LEFT, padx=(0,15))

    metadata_display = tk.Label(top_frame, textvariable=metadata_label, font=("Arial", 9), fg="gray")
    metadata_display.pack(side=tk.RIGHT)

    tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    name_entry = tk.Entry(top_frame, width=30)
    name_entry.pack(side=tk.LEFT, padx=5)
    name_entry.bind("<KeyRelease>", lambda e: on_filter_changed())

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
        extended_values = list(values) + ["General"]
        add_to_basket(extended_values, basket_items, update_basket_table, basket_tree)

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

    ghost_label = None
    canvas = tk.Canvas(basket_tree, highlightthickness=0, bd=0, bg="SystemWindow")

    def on_drag_start(event):
        nonlocal ghost_label
        iid = basket_tree.identify_row(event.y)
        if iid:
            label_text = basket_tree.item(iid)['text'] or basket_tree.item(iid)['values'][0]
            if ghost_label:
                ghost_label.destroy()
            ghost_label = tk.Label(root, text=label_text, bg="lightyellow", relief="solid", bd=1)
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
                drop_y = y if event.y < (y + h//2) else y+h
                canvas.create_rectangle(
                    2, drop_y-1, basket_tree.winfo_width()-2, drop_y+1,
                    fill="red", outline="", width=0
                )

    def on_drag_release(event):
        if ghost_label:
            ghost_label.destroy()
        canvas.delete("all")
        canvas.place_forget()

    basket_tree.bind("<ButtonPress-1>", on_drag_start)
    basket_tree.bind("<B1-Motion>", on_drag_motion)
    basket_tree.bind("<ButtonRelease-1>", on_drag_release)

    from notes_panel import create_notes_panel
    create_notes_panel(basket_frame, project_name)

    basket_tree.bind("<Double-1>", lambda e: edit_pocet_cell(e, basket_tree, basket_items, update_basket_table))
    tk.Button(basket_frame, text="Odstrániť", command=lambda: remove_from_basket(basket_tree, basket_items, update_basket_table))\
      .pack(pady=3)

    def try_export():
        user_name = user_name_entry.get().strip()
        if not user_name:
            messagebox.showwarning("Meno chýba", "⚠ Prosím zadaj svoje meno pred exportom.")
            return
        update_excel_from_basket(basket_items, project_name)

    export_button = tk.Button(basket_frame, text="Exportovať", command=try_export, state=tk.DISABLED)
    export_button.pack(pady=3)

    def check_name(*_):
        export_button.config(state=tk.NORMAL if user_name_entry.get().strip() else tk.DISABLED)
    user_name_entry.bind("<KeyRelease>", check_name)

    basket_file = os.path.join(project_path, basket_version) if basket_version else os.path.join(project_path, "project.json")
    if os.path.exists(basket_file):
        with open(basket_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if "basket" in data:
                    basket_items.update(OrderedDict(data["basket"]))
                if "user_name" in data:
                    user_name_entry.insert(0, data["user_name"])
                if "timestamp" in data:
                    metadata_label.set(
                        f"Súbor: {os.path.basename(basket_file)} | Dátum: {data['timestamp']} | Autor: {data.get('user_name', '')}"
                    )
            except json.JSONDecodeError:
                print("⚠ Could not parse project file")

    # Initial load: no subcategory => show all
    apply_filters(cursor, db_type, subcat_vars, name_entry, tree)
    update_basket_table(basket_tree, basket_items)

    root.protocol("WM_DELETE_WINDOW", return_home)
    root.mainloop()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ No project path provided. Usage: python gui.py <project_path>")
        sys.exit(1)
    path = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None
    run_gui(path, version)
