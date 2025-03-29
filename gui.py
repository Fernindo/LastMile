import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from excel_processing import update_excel

root = tk.Tk()
root.title("Database & Excel GUI")
root.state("zoomed")

try:
    conn = psycopg2.connect(
        host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
        port=5432,
        user="neondb_owner",
        password="npg_aYC4yHnQIjV1",
        dbname="neondb",
        sslmode="require"
    )
    cursor = conn.cursor()
except psycopg2.Error as err:
    messagebox.showerror("Database Error", f"Error connecting to PostgreSQL: {err}")
    exit()

class_name_map = {
    "ustredne": "Ústredne",
    "rozhrania": "Rozhrania",
    "komunikatory": "Komunikátory",
    "radiove_moduly": "Rádiové moduly",
    "pristupove_moduly": "Prístupové moduly (Bezdrôtové)"
}

filter_frame = tk.Frame(root)
filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

category_structure = {
    "EZS": list(class_name_map.keys())
}

category_vars = {}
table_vars = {}

def apply_filters():
    selected_tables = [class_name_map[t] for t, var in table_vars.items() if var.get() and t in class_name_map]

    name_filter = name_entry.get().strip().lower()

    query = """
        SELECT p.id, p.nazov, p.jednotka, p.dodavatel, p.odkaz, p.koeficient, p.nakup_material, c.class_name
        FROM produkt p
        JOIN class c ON p.class_id = c.id
        WHERE 1=1
    """
    params = []

    if selected_tables:
        placeholders = ', '.join(['%s'] * len(selected_tables))
        query += f" AND c.class_name IN ({placeholders})"
        params.extend(selected_tables)

    cursor.execute(query, tuple(params))
    filtered_rows = cursor.fetchall()

    tree.delete(*tree.get_children())
    for row in filtered_rows:
        if not name_filter or name_filter in row[1].lower():
            tree.insert("", tk.END, values=row[:-1])

def reset_filters():
    for var in table_vars.values():
        var.set(False)
    name_entry.delete(0, tk.END)
    apply_filters()

def build_filter_tree():
    tk.Label(filter_frame, text="Prehliadač databázových tabuliek", font=("Arial", 10, "bold")).pack(anchor="w")
    for category, tables in category_structure.items():
        cat_frame = tk.Frame(filter_frame)
        cat_var = tk.BooleanVar(value=True)
        category_vars[category] = cat_var
        cat_label = ttk.Checkbutton(cat_frame, text=category, variable=cat_var)
        cat_label.pack(anchor="w", padx=2)
        inner_frame = tk.Frame(cat_frame)
        for table in tables:
            table_vars[table] = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(inner_frame, text=table, variable=table_vars[table], command=apply_filters)
            chk.pack(anchor="w", padx=20)
        inner_frame.pack()
        cat_frame.pack(anchor="w", fill="x", pady=2)

    reset_button = tk.Button(filter_frame, text="Resetovať filtre", command=reset_filters)
    reset_button.pack(anchor="w", pady=10, padx=5)

build_filter_tree()

main_frame = tk.Frame(root)
main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

top_frame = tk.Frame(main_frame)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

label_name = tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10))
label_name.pack(side=tk.LEFT, padx=5)

name_entry = tk.Entry(top_frame, width=30)
name_entry.pack(side=tk.LEFT, padx=5)
name_entry.bind("<KeyRelease>", lambda event: apply_filters())

tree_frame = tk.Frame(main_frame)
tree_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

tree = ttk.Treeview(tree_frame, columns=(
    "id", "nazov", "jednotka", "dodavatel", "odkaz", "koeficient", "nakup_material"
), show="headings")

for col in tree["columns"]:
    tree.heading(col, text=col.capitalize())
    tree.column(col, anchor="center")

tree.pack(fill=tk.BOTH, expand=True)

cursor.execute("""
    SELECT p.id, p.nazov, p.jednotka, p.dodavatel, p.odkaz, p.koeficient, p.nakup_material
    FROM produkt p
    JOIN class c ON p.class_id = c.id
""")
rows = cursor.fetchall()
for row in rows:
    tree.insert("", tk.END, values=row)

basket_items = {}

def add_to_basket(item):
    pocet = 1
    item_id = item[0]
    if item_id in basket_items:
        basket_items[item_id]["pocet"] += pocet
    else:
        basket_items[item_id] = {
            "id": item_id,
            "nazov": item[1],
            "nakup_material": item[6],
            "koeficient": item[5],
            "pocet": pocet
        }
    update_basket_table()

def update_basket_table():
    basket_tree.delete(*basket_tree.get_children())
    for item in basket_items.values():
        basket_tree.insert("", tk.END, values=(
            item["id"], item["nazov"], item["nakup_material"], item["koeficient"], item["pocet"]
        ))

def edit_pocet_cell(event):
    selected_item = basket_tree.focus()
    if not selected_item:
        return
    col = basket_tree.identify_column(event.x)
    col_index = int(col.replace('#', '')) - 1

    if col not in ["#4", "#5"]:
        return

    x, y, width, height = basket_tree.bbox(selected_item, col)
    entry_popup = tk.Entry(basket_tree)
    entry_popup.place(x=x, y=y, width=width, height=height)
    current_value = basket_tree.item(selected_item)['values'][col_index]
    entry_popup.insert(0, current_value)
    entry_popup.focus()

    def save_edit(event):
        try:
            new_value = float(entry_popup.get()) if col == "#4" else int(entry_popup.get())
        except ValueError:
            new_value = current_value
        values = list(basket_tree.item(selected_item)["values"])
        values[col_index] = new_value
        basket_tree.item(selected_item, values=values)
        item_id = values[0]
        if item_id in basket_items:
            if col == "#4":
                basket_items[item_id]["koeficient"] = new_value
            elif col == "#5":
                basket_items[item_id]["pocet"] = new_value
        entry_popup.destroy()

    entry_popup.bind("<Return>", save_edit)
    entry_popup.bind("<FocusOut>", save_edit)

basket_frame = tk.Frame(main_frame)
basket_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

basket_label = tk.Label(basket_frame, text="Košík - vybraté položky:", font=("Arial", 10))
basket_label.pack()

basket_tree = ttk.Treeview(basket_frame, columns=("id", "nazov", "nakup_material", "koeficient", "pocet"), show="headings")
for col in basket_tree["columns"]:
    basket_tree.heading(col, text=col.capitalize())
    basket_tree.column(col, anchor="center")

basket_tree.pack(fill=tk.BOTH, expand=True)
basket_tree.bind("<Double-1>", edit_pocet_cell)

def remove_from_basket():
    selected_items = basket_tree.selection()
    for item in selected_items:
        item_id = basket_tree.item(item)["values"][0]
        if item_id in basket_items:
            del basket_items[item_id]
        basket_tree.delete(item)
    update_basket_table()

def update_excel_from_basket():
    if not basket_items:
        messagebox.showwarning("No Items", "⚠ Košík je prázdny.")
        return
    excel_data = [
        (v["id"], v["nazov"], v["nakup_material"], v["koeficient"], v["pocet"])
        for v in basket_items.values()
    ]
    update_excel(excel_data)

tk.Button(basket_frame, text="Odstrániť", command=remove_from_basket).pack(pady=3)
tk.Button(basket_frame, text="Exportovať", command=update_excel_from_basket).pack(pady=3)

tree.bind("<Double-1>", lambda event: add_to_basket(tree.item(tree.focus())["values"]))

root.mainloop()
conn.close()
