import tkinter as tk
from tkinter import messagebox
import psycopg2
from main_admin import AdminApp

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Prihlásenie")
        self.root.geometry("400x200")
        self.center_window(self.root)

        frame = tk.Frame(root)
        frame.pack(expand=True)

        tk.Label(frame, text="Používateľské meno").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.username_entry = tk.Entry(frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="Heslo").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.password_entry = tk.Entry(frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        self.show_password_var = tk.BooleanVar()
        self.show_password_check = tk.Checkbutton(
            frame, text="Zobraziť heslo",
            variable=self.show_password_var,
            command=self.toggle_password
        )
        self.show_password_check.grid(row=2, column=1, sticky="w")

        login_btn = tk.Button(frame, text="Prihlásiť sa", width=15, command=self.login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=20)

        self.root.bind("<Return>", lambda event: self.login())  # Stlačenie Enter = login

    def toggle_password(self):
        self.password_entry.config(show="" if self.show_password_var.get() else "*")

    def center_window(self, win):
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (width // 2)
        y = (win.winfo_screenheight() // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def get_connection(self):
        try:
            return psycopg2.connect(
                host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
                port=5432,
                user="neondb_owner",
                password="npg_aYC4yHnQIjV1",
                dbname="neondb",
                sslmode="require"
            )
        except Exception as e:
            messagebox.showerror("Chyba pripojenia", str(e))
            return None

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Chýbajúce údaje", "Zadaj meno aj heslo.")
            return

        conn = self.get_connection()
        if not conn:
            return

        cur = conn.cursor()
        cur.execute("""
            SELECT r.name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE u.username = %s AND u.password = %s
        """, (username, password))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result[0] == "admin":
            self.root.destroy()
            root = tk.Tk()
            AdminApp(root)
            root.mainloop()
        else:
            messagebox.showerror("Odmietnutý prístup", "Iba admin má prístup.")

if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()
