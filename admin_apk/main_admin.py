import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2
from insert_admin import insert_product_form
from update_admin import update_product_form
from pouzivatelia_admin import UserManagementWindow

class AdminApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Panel")
        self.root.geometry("1400x700")
        self.center_window(self.root)

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, pady=5)

        tk.Button(button_frame, text="Správa používateľov", command=self.manage_users).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Pridať produkt", command=self.insert_product).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Update produktu", command=self.update_product).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Refresh", command=self.load_products).pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self.root, columns=(
            "delete", "produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace", "class_id"
        ), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<ButtonRelease-1>", self.handle_delete_click)
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
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.nazov_tabulky, p.id, p.produkt, p.jednotky, p.dodavatel, p.odkaz,
                   p.koeficient, p.nakup_materialu, p.cena_prace
            FROM produkty p
            JOIN class c ON p.class_id = c.id
            ORDER BY c.nazov_tabulky, p.id
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        current_class = None
        for row in rows:
            class_name = row[0]
            if class_name != current_class:
                current_class = class_name
                self.tree.insert("", "end", values=("", f"-- {class_name} --", "", "", "", "", "", "", ""), tags=("header",))
            self.tree.insert("", "end", values=("X", *row[1:], class_name))

        self.tree.tag_configure("header", font=("Arial", 10, "bold"))

    def handle_delete_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        column = self.tree.identify_column(event.x)
        if region == "cell" and column == "#1":
            item = self.tree.identify_row(event.y)
            if item:
                values = self.tree.item(item)['values']
                prod_name = values[1]
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

def main():
    root = tk.Tk()
    AdminApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
