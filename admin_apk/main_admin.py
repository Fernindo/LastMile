import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2
import json
import os

from insert_admin import insert_product_form
from update_admin import update_product_form
from pouzivatelia_admin import UserManagementWindow
from class_admin import create_table_form
from filter_panel import FilterPanel

USER_ID = "admin"
SETTINGS_FILE = "user_column_settings.json"

ALL_COLUMNS = [
    "produkt", "jednotky", "dodavatel", "odkaz",
    "koeficient", "nakup_materialu", "cena_prace", "class_id"
]

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Panel")
        self.root.geometry("1400x700")
        self.center_window(self.root)

        self.selected_columns = self.load_user_settings()
        self.sort_column = None
        self.sort_reverse = False

        # Horný panel s tlačidlami
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, pady=5)

        tk.Button(button_frame, text="Správa používateľov", command=self.manage_users).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Pridať produkt", command=self.insert_product).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Update produktu", command=self.update_product).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Editovať tabuľku", command=self.create_table).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Refresh", command=self.load_products).pack(side=tk.LEFT, padx=5)

        # Filter panel
        self.filter_panel = FilterPanel(
            self.root,
            get_connection_func=self.get_connection,
            on_filter_apply=self.on_filter_applied,
            on_columns_change=self.on_column_change,
            selected_columns=self.selected_columns
        )

        # Tabuľka produktov
        self.tree = ttk.Treeview(self.root, columns=["delete"] + self.selected_columns, show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col))
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<ButtonRelease-1>", self.handle_delete_click)
        self.load_products()

    def load_user_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                return settings.get(USER_ID, ALL_COLUMNS)
        return ALL_COLUMNS

    def save_user_settings(self):
        settings = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        settings[USER_ID] = self.selected_columns
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)

    def on_column_change(self, selected_columns=None):
        self.selected_columns = selected_columns or self.filter_panel.get_selected_columns()
        self.save_user_settings()
        self.refresh_tree()

    def on_filter_applied(self, kategoria, tabulka):
        self.active_filter_kat = kategoria
        self.active_filter_tab = tabulka
        self.load_products()

    def refresh_tree(self):
        if hasattr(self, "tree") and self.tree.winfo_exists():
            self.tree.destroy()
        self.tree = ttk.Treeview(self.root, columns=["delete"] + self.selected_columns, show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col))
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.handle_delete_click)
        self.load_products()

    def sort_by_column(self, col):
        if col not in self.selected_columns:
            return
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False
        self.load_products()

    def center_window(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def get_connection(self):
        return psycopg2.connect(
            host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
            port=5432,
            user="neondb_owner",
            password="npg_aYC4yHnQIjV1",
            dbname="neondb",
            sslmode="require"
        )

    def load_products(self):
        try:
            if not hasattr(self, "tree") or not self.tree.winfo_exists():
                return
        except tk.TclError:
            return  # Aplikácia bola zavretá

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = self.get_connection()
        cur = conn.cursor()

        query = """
            SELECT c.nazov_tabulky, p.id, p.produkt, p.jednotky, p.dodavatel, p.odkaz,
                   p.koeficient, p.nakup_materialu, p.cena_prace, p.class_id
            FROM class c
            LEFT JOIN produkty p ON p.class_id = c.id
        """
        filters = []
        params = []

        if hasattr(self, "active_filter_kat") and self.active_filter_kat:
            filters.append("c.hlavna_kategoria = %s")
            params.append(self.active_filter_kat)
        if hasattr(self, "active_filter_tab") and self.active_filter_tab:
            filters.append("c.nazov_tabulky = %s")
            params.append(self.active_filter_tab)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY c.nazov_tabulky, p.id"

        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if self.sort_column:
            try:
                index = ALL_COLUMNS.index(self.sort_column) + 2
                rows.sort(key=lambda x: (x[index] is None, x[index]), reverse=self.sort_reverse)
            except Exception as e:
                print(f"Sort error: {e}")

        current_class = None
        for row in rows:
            class_name = row[0]
            produkt_data = row[2:]
            if class_name != current_class:
                current_class = class_name
                self.tree.insert("", "end", values=("", f"-- {class_name} --", *[""] * len(self.selected_columns)), tags=("header",))
            if row[1] is not None:
                values = [produkt_data[ALL_COLUMNS.index(col)] if col in ALL_COLUMNS else "" for col in self.selected_columns]
                self.tree.insert("", "end", values=("X", *values))

        self.tree.tag_configure("header", font=("Arial", 10, "bold"))

    def handle_delete_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        if region == "cell" and column == "#1":
            item = self.tree.identify_row(event.y)
            if item:
                values = self.tree.item(item)['values']
                prod_name = values[1]
                if prod_name.startswith("--"):
                    return
                if messagebox.askyesno("Vymazať", f"Naozaj chceš vymazať produkt '{prod_name}'?"):
                    conn = self.get_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM produkty WHERE produkt = %s", (prod_name,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    self.load_products()

    def insert_product(self):
        insert_product_form(self.root)
        self.load_products()

    def update_product(self):
        update_product_form(self.root)
        self.load_products()

    def manage_users(self):
        UserManagementWindow(self.root)

    def create_table(self):
        create_table_form(self.root, refresh_callback=self.safe_reload)

    def safe_reload(self):
        try:
            self.load_products()
        except tk.TclError:
            print("Aplikácia bola zavretá – nemožno načítať produkty.")


def main():
    root = tk.Tk()
    AdminApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
