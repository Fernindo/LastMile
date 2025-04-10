import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

class UserManagementWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Správa používateľov")
        self.top.geometry("900x500")
        self.center_window(self.top)

        self.tree = ttk.Treeview(
            self.top,
            columns=("ID", "Username", "Password", "Rola", "Meno", "Priezvisko"),
            show="headings"
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Password", text="Heslo")
        self.tree.heading("Rola", text="Rola")
        self.tree.heading("Meno", text="Meno")
        self.tree.heading("Priezvisko", text="Priezvisko")

        for col in ("ID", "Username", "Password", "Rola", "Meno", "Priezvisko"):
            self.tree.column(col, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        tk.Button(self.top, text="Odstrániť vybraného", command=self.delete_selected).pack(pady=5)

        form = tk.LabelFrame(self.top, text="Pridať používateľa")
        form.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(form, text="Username").grid(row=0, column=0, padx=5, pady=5)
        self.entry_username = tk.Entry(form)
        self.entry_username.grid(row=0, column=1, padx=5)

        tk.Label(form, text="Heslo").grid(row=0, column=2, padx=5)
        self.entry_password = tk.Entry(form)
        self.entry_password.grid(row=0, column=3, padx=5)

        tk.Label(form, text="Rola").grid(row=0, column=4, padx=5)
        self.role_var = tk.StringVar(value="user")
        ttk.Combobox(form, textvariable=self.role_var, values=["admin", "user"], state="readonly").grid(row=0, column=5, padx=5)

        tk.Label(form, text="Meno").grid(row=1, column=0, padx=5, pady=5)
        self.entry_meno = tk.Entry(form)
        self.entry_meno.grid(row=1, column=1, padx=5)

        tk.Label(form, text="Priezvisko").grid(row=1, column=2, padx=5, pady=5)
        self.entry_priezvisko = tk.Entry(form)
        self.entry_priezvisko.grid(row=1, column=3, padx=5)

        tk.Button(self.top, text="Pridať", command=self.add_user).pack(pady=5)

        self.load_users()

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

    def load_users(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.username, u.password, r.name, u.meno, u.priezvisko
            FROM users u
            JOIN roles r ON u.role_id = r.id
        """)
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)
        cur.close()
        conn.close()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        user_id = item["values"][0]
        if messagebox.askyesno("Odstrániť", "Chceš zmazať tohto používateľa?"):
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            cur.close()
            conn.close()
            self.load_users()

    def add_user(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        meno = self.entry_meno.get()
        priezvisko = self.entry_priezvisko.get()
        role_name = self.role_var.get()

        if not username or not password or not meno or not priezvisko:
            messagebox.showwarning("Chyba", "Zadaj všetky údaje")
            return

        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
        role_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO users (username, password, role_id, meno, priezvisko)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password, role_id, meno, priezvisko))

        conn.commit()
        cur.close()
        conn.close()
        self.load_users()
