import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap import Style
from helpers import enable_high_dpi_awareness, calibrate_tk_scaling, apply_ttk_base_font
import psycopg2
import subprocess
import os
import json
import sys



class login_app:
    def __init__(self, root):
        self.root = root
        self.root.title("Prihlásenie")
        self.root.geometry("420x200")
        self.center_window(self.root)

        self.credentials_file = "saved_credentials.json"
        self.password_visible = False

        frame = tb.LabelFrame(root, text="Prihlásenie používateľa", padding=10)
        frame.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # Username
        tb.Label(frame, text="Username:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.username_entry = tb.Entry(frame, width=25)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        # Password
        tb.Label(frame, text="Heslo:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.password_entry = tb.Entry(frame, show="*", width=25)
        self.password_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.toggle_button = tb.Button(
            frame, text="●", width=2, relief="flat", command=self.toggle_password_visibility
        )
        self.toggle_button.grid(row=1, column=2, padx=0, sticky="w")

        # Zapamätať prihlásenie
        self.remember_var = tk.BooleanVar()
        self.remember_check = tb.Checkbutton(frame, text="Zapamätať prihlásenie", variable=self.remember_var)
        self.remember_check.grid(row=2, column=1, sticky="w", padx=5, pady=(0, 5))

        # Login button
        login_btn = tb.Button(frame, text="Prihlásiť sa", width=20, bootstyle="success", command=self.login)
        login_btn.grid(row=3, column=0, columnspan=3, pady=10)

        self.root.bind("<Return>", lambda event: self.login())

        self.load_credentials()

    def toggle_password_visibility(self):
        self.password_visible = not self.password_visible
        self.password_entry.config(show="" if self.password_visible else "*")
        self.toggle_button.config(text="◉" if self.password_visible else "●")

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

        if result and result[0] != "admin":
            if self.remember_var.get():
                self.save_credentials(username, password)
            else:
                self.clear_credentials()

            import project_selector
            self.root.quit()      # stop login mainloop
            self.root.destroy()   # close login window fully
            project_selector.main(parent=None)  # start project selector fresh

        else:
            messagebox.showerror("Odmietnutý prístup", "Admin nemá povolený prístup.")

    def save_credentials(self, username, password):
        data = {"username": username, "password": password}
        with open(self.credentials_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_credentials(self):
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.username_entry.insert(0, data.get("username", ""))
                    self.password_entry.insert(0, data.get("password", ""))
                    self.remember_var.set(True)
            except:
                pass

    def clear_credentials(self):
        if os.path.exists(self.credentials_file):
            os.remove(self.credentials_file)

if __name__ == "__main__":
    try:
        enable_high_dpi_awareness()
    except Exception:
        pass
    style = Style(theme="flatly")
    root = style.master
    try:
        calibrate_tk_scaling(root)
    except Exception:
        pass
    try:
        apply_ttk_base_font(style, family="Segoe UI", size=11)
    except Exception:
        pass
    login_app(root)
    root.mainloop()
