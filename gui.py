import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psycopg2
from excel_processing import update_excel
from edit_window import open_edit_window
from remove_window import open_remove_window

# ====== DB pripojenie ======
try:
    conn = psycopg2.connect(
        host="localhost", 
        port=5432,
        user="app_user",
        password="80",
        dbname="LM"
    )
    cursor = conn.cursor()
except psycopg2.Error as err:
    messagebox.showerror("Database Error", f"Error connecting to PostgreSQL: {err}")
    exit()

# ====== Tabuľky ======
cctv_tabs = ["nvr", "monitory"]
ezs_tabs = ["ustredne", "rozhrania", "sireny_vnutorne", "sireny_vonkajsie", "pohybove_detektory", "rele", "indikatory", "radiove_moduly", "komunikatory", "pristupove_moduly"]
dat_tabs = [
    "rozvadzace", "vybava_rozvadzacov", "wifi_ap", "switche",
    "zalozne_zdroje", "zalozne_zdroje_battery_packy", "battery_packy",
    "kabelaz", "datove_zasuvky", "podlahove_krabice"
]

all_tabs = cctv_tabs + ezs_tabs + dat_tabs

# ====== GUI setup ======
root = tk.Tk()
root.title("Prehliadač databázových tabuliek")
root.state("zoomed")

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)
layout_frame = tk.Frame(main_frame)
layout_frame.pack(fill=tk.BOTH, expand=True)

sidebar_visible = True
sidebar_frame = tk.Frame(layout_frame, width=200, bg="#eeeeee")
sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

content_frame = tk.Frame(layout_frame)
content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# ====== Horný panel ======
top_frame = tk.Frame(content_frame)
top_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)

toggle_btn = tk.Button(top_frame, text="⏴")
toggle_btn.pack(side=tk.LEFT, padx=(0, 10))

# Tlačidlá vpravo
right_btn_frame = tk.Frame(top_frame)
right_btn_frame.pack(side=tk.RIGHT)

tree_columns = ("id", "nazov", "jednotka", "pocet", "dodavatel", "odkaz", "koeficient", "nakup_material")

edit_btn = tk.Button(right_btn_frame, text="✏️ Editovať", command=lambda: open_edit_window(root, conn, cursor, all_tabs, tree_columns))
edit_btn.pack(side=tk.LEFT, padx=5)
remove_btn = tk.Button(right_btn_frame, text="🗑️ Odstrániť", command=lambda: open_remove_window(conn, cursor, all_tabs, tree_columns))
remove_btn.pack(side=tk.LEFT, padx=5)

def toggle_sidebar():
    global sidebar_visible
    if sidebar_visible:
        sidebar_frame.pack_forget()
        toggle_btn.config(text="⏵")
    else:
        content_frame.pack_forget()
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        toggle_btn.config(text="⏴")
    sidebar_visible = not sidebar_visible

toggle_btn.config(command=toggle_sidebar)

# ====== Filter checkboxy ======
table_filter_vars = {}
category_select_vars = {}

def update_table_combo():
    load_table()

def toggle_category(category_tabs, category_var):
    value = category_var.get()
    for tab in category_tabs:
        table_filter_vars[tab].set(value)
    update_table_combo()

def add_checkbox_section(label, tab_list):
    section_frame = tk.Frame(sidebar_frame, bg="#eeeeee")
    section_frame.pack(fill=tk.X, padx=5, pady=(10, 0))

    var_category = tk.BooleanVar(value=True)
    category_select_vars[label] = var_category

    master_cb = tk.Checkbutton(section_frame, text=label, variable=var_category, bg="#cccccc", anchor="w", font=("Segoe UI", 10, "bold"), command=lambda: toggle_category(tab_list, var_category))
    master_cb.pack(fill=tk.X)

    for tab in tab_list:
        var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(section_frame, text=tab, variable=var, bg="#eeeeee", anchor="w", command=update_table_combo)
        cb.pack(fill=tk.X, padx=20)
        table_filter_vars[tab] = var

add_checkbox_section("CCTV", cctv_tabs)
add_checkbox_section("EZS", ezs_tabs)
add_checkbox_section("DATABÁZA", dat_tabs)

# ====== Vyhladavanie a strom ======
search_var_main = tk.StringVar()
tk.Label(top_frame, text="Vyhľadávanie:").pack(side=tk.LEFT, padx=(0, 5))
search_entry = tk.Entry(top_frame, textvariable=search_var_main)
search_entry.pack(side=tk.LEFT)

tree_frame = tk.Frame(content_frame)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

tree = ttk.Treeview(tree_frame, columns=tree_columns, show="headings", xscrollcommand=tree_scroll_x.set)
tree_scroll_x.config(command=tree.xview)
tree.pack(fill=tk.BOTH, expand=True)

style = ttk.Style()
style.configure("Treeview", rowheight=24)
tree.tag_configure("bold", font=('Segoe UI', 10, 'bold'))

sort_directions_main = {col: True for col in tree_columns}
for col in tree_columns:
    def sortby_main(colname=col):
        items = [(tree.set(k, colname), k) for k in tree.get_children('') if "bold" not in tree.item(k, "tags")]
        is_numeric = all(val.replace('.', '', 1).isdigit() for val, _ in items if val != '')
        reverse = not sort_directions_main[colname]
        sort_directions_main[colname] = reverse
        items.sort(key=lambda t: float(t[0]) if is_numeric and t[0] else t[0], reverse=reverse)
        for index, (_, k) in enumerate(items):
            tree.move(k, '', index)
    tree.heading(col, text=col, command=sortby_main)
    tree.column(col, anchor="center")

# ====== Spodná tabuľka / Košík ======
basket_columns = ("id", "nazov", "nakup_material", "koeficient", "pocet", "cena")
basket_frame = tk.Frame(content_frame)
basket_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tk.Label(basket_frame, text="Košík - vybraté položky:").pack()

basket_scroll_x = ttk.Scrollbar(basket_frame, orient="horizontal")
basket_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

basket_tree = ttk.Treeview(basket_frame, columns=basket_columns, show="headings", xscrollcommand=basket_scroll_x.set)
basket_scroll_x.config(command=basket_tree.xview)
basket_tree.pack(fill=tk.BOTH, expand=True)

for col in basket_columns:
    basket_tree.heading(col, text=col)
    basket_tree.column(col, anchor="center")

def add_to_basket(event):
    item_id = tree.focus()
    item = tree.item(item_id)["values"]
    if item and "bold" not in tree.item(item_id, "tags"):
        try:
            nakup = float(item[7])
            koef = float(item[6])
            pocet = float(item[3])
            cena = round(nakup * koef * pocet, 2)
            full_item = (item[0], item[1], nakup, koef, pocet, cena)
            basket_tree.insert("", tk.END, values=full_item)
        except Exception as e:
            messagebox.showerror("Chyba", f"Chyba pri pridaní do košíka:\n{e}")

def edit_cell(event):
    region = basket_tree.identify("region", event.x, event.y)
    if region != "cell": return
    row_id = basket_tree.identify_row(event.y)
    col_id = basket_tree.identify_column(event.x)
    col_index = int(col_id.replace("#", "")) - 1
    col_name = basket_columns[col_index]
    if col_name not in ("koeficient", "pocet"): return

    x, y, width, height = basket_tree.bbox(row_id, col_id)
    value = basket_tree.set(row_id, col_name)

    frame = tk.Frame(basket_tree)
    frame.place(x=x, y=y, width=width, height=height)

    entry = tk.Spinbox(frame, from_=0, to=999999, increment=1 if col_name == "pocet" else 0.1)
    entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    entry.delete(0, tk.END)
    entry.insert(0, value)
    entry.focus()

    def reset_to_default():
        entry.delete(0, tk.END)
        entry.insert(0, "1" if col_name == "pocet" else "1.0")
        save_edit()

    btn = tk.Button(frame, text="D", width=2, command=reset_to_default)
    btn.pack(side=tk.RIGHT)

    def save_edit(event=None):
        try:
            new_val = float(entry.get())
            basket_tree.set(row_id, col_name, new_val)
            update_price(row_id)
        except:
            pass
        finally:
            frame.destroy()

    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", lambda e: save_edit())

def update_price(row_id):
    try:
        nakup = float(basket_tree.set(row_id, "nakup_material"))
        koef = float(basket_tree.set(row_id, "koeficient"))
        pocet = float(basket_tree.set(row_id, "pocet"))
        cena = round(nakup * koef * pocet, 2)
        basket_tree.set(row_id, "cena", cena)
    except:
        pass

# ====== Load funkcia ======
def load_table(*args):
    tree.delete(*tree.get_children())
    filter_text = search_var_main.get().lower()
    tabs_to_load = [tab for tab in all_tabs if table_filter_vars[tab].get()]
    for tab in tabs_to_load:
        try:
            cursor.execute(f'SELECT * FROM "{tab}"')
            rows = cursor.fetchall()
            visible_rows = [row for row in rows if filter_text in str(row).lower()]
            if not visible_rows:
                continue
            heading_values = ["" for _ in tree_columns]
            heading_values[0] = tab
            tree.insert("", tk.END, values=heading_values, tags=("bold",))
            for row in visible_rows:
                reordered = (
                    row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]
                )
                tree.insert("", tk.END, values=reordered)
        except psycopg2.Error as err:
            conn.rollback()
            if 'does not exist' in str(err):
                continue
            messagebox.showerror("Chyba pri čítaní", f"{tab}: {str(err)}")

# ====== Bindy & štart ======
search_var_main.trace_add("write", load_table)
tree.bind("<Double-1>", add_to_basket)
basket_tree.bind("<Double-1>", edit_cell)

update_table_combo()
load_table()
root.mainloop()
conn.close()
