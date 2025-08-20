# login.py
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from gui_functions import get_database_connection  # tvoje napojenie na online DB

APP_TITLE = "Prihlásenie"
CONFIG_FILE = "login_config.json"  # ukladá "zapamätaj si" lokálne
LAUNCHER_FILE = "launcher.py"      # spúšťaný launcher

# ───────────────────────── Helpery ─────────────────────────

def resource_path(rel_path: str) -> str:
    """Absolútna cesta fungujúca v skripte aj po pyinstaller-e."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, rel_path)

def load_config():
    try:
        with open(resource_path(CONFIG_FILE), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg: dict):
    try:
        with open(resource_path(CONFIG_FILE), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def verify_user_online(username: str, password: str):
    """
    Overí používateľa cez tvoju DB vrstvu (get_database_connection).
    Očakáva tabuľku `users` so stĺpcami:
    id, username, password, role_id, meno, priezvisko, popis
    Vráti dict alebo None.
    """
    try:
        conn, db_type = get_database_connection()
    except Exception as e:
        messagebox.showerror("Chyba DB", f"Nepodarilo sa pripojiť k databáze:\n{e}")
        return None

    try:
        cur = conn.cursor()
        # Vyber placeholdery podľa typu DB
        if db_type == "postgres":
            sql = """
                SELECT id, username, password, role_id,
                       COALESCE(meno,''), COALESCE(priezvisko,''), COALESCE(popis,'')
                FROM users
                WHERE username = %s
                LIMIT 1
            """
            params = (username,)
        else:
            # fallback (napr. sqlite) – rovnaké stĺpce
            sql = """
                SELECT id, username, password, role_id,
                       COALESCE(meno,''), COALESCE(priezvisko,''), COALESCE(popis,'')
                FROM users
                WHERE username = ?
                LIMIT 1
            """
            params = (username,)

        cur.execute(sql, params)
        row = cur.fetchone()
    except Exception as e:
        messagebox.showerror("Chyba DB", f"Dotaz zlyhal:\n{e}")
        try:
            conn.close()
        except Exception:
            pass
        return None

    try:
        conn.close()
    except Exception:
        pass

    if not row:
        return None

    user = {
        "id": row[0],
        "username": row[1],
        "password": row[2],
        "role_id": row[3],
        "meno": row[4] or "",
        "priezvisko": row[5] or "",
        "popis": row[6] or "",
    }

    # Plaintext kontrola podľa tvojich dát
    if str(password) == str(user["password"]):
        return user
    return None

def run_launcher(meno: str = "", priezvisko: str = "", open_latest: bool = False):
    """
    Spustí launcher.py s voliteľnými parametrami --meno, --priezvisko, --open-latest.
    """
    launcher_path = resource_path(LAUNCHER_FILE)
    if not os.path.isfile(launcher_path):
        messagebox.showerror("Chyba", f"Nenašiel som '{LAUNCHER_FILE}'.")
        return

    args = [sys.executable, launcher_path]
    if meno:
        args += ["--meno", meno]
    if priezvisko:
        args += ["--priezvisko", priezvisko]
    if open_latest:
        args += ["--open-latest"]

    try:
        subprocess.Popen(args, cwd=os.path.dirname(launcher_path) or None)
    except Exception as e:
        messagebox.showerror("Chyba", f"Nepodarilo sa spustiť launcher:\n{e}")
        return
    finally:
        # Bezpečne ukončí login proces (aby nezostal visieť)
        os._exit(0)

# ───────────────────────── UI ─────────────────────────

class LoginApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("420x300")
        root.resizable(False, False)

        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_show_password = tk.BooleanVar(value=False)
        self.var_remember = tk.BooleanVar(value=True)

        cfg = load_config()
        if cfg.get("remember"):
            self.var_username.set(cfg.get("username", ""))
            self.var_password.set(cfg.get("password", ""))
            self.var_remember.set(True)

        pad = 12
        frm = tb.Frame(root, padding=pad)
        frm.pack(fill="both", expand=True)

        title = tb.Label(frm, text="Prihlásenie", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")

        # Username
        tb.Label(frm, text="Používateľ:").grid(row=1, column=0, sticky="w")
        self.ent_user = tb.Entry(frm, textvariable=self.var_username, width=28, bootstyle=INFO)
        self.ent_user.grid(row=1, column=1, columnspan=2, sticky="we", pady=(0, 6))

        # Password
        tb.Label(frm, text="Heslo:").grid(row=2, column=0, sticky="w")
        self.ent_pass = tb.Entry(frm, textvariable=self.var_password, show="•", width=28, bootstyle=INFO)
        self.ent_pass.grid(row=2, column=1, sticky="we", pady=(0, 6))
        chk_show = tb.Checkbutton(frm, text="Zobraziť heslo", variable=self.var_show_password, command=self.toggle_password, bootstyle=SECONDARY)
        chk_show.grid(row=2, column=2, sticky="w")

        # Remember me
        chk_rem = tb.Checkbutton(frm, text="Uložiť prihlásenie", variable=self.var_remember, bootstyle=SECONDARY)
        chk_rem.grid(row=3, column=1, columnspan=2, sticky="w")

        # Buttons
        btn_login = tb.Button(frm, text="Prihlásiť sa", command=self.on_login, bootstyle=SUCCESS)
        btn_login.grid(row=4, column=1, sticky="we", pady=(12, 4))

        btn_skip = tb.Button(frm, text="Skip (vývoj)", command=lambda: run_launcher(open_latest=False), bootstyle=WARNING)
        btn_skip.grid(row=4, column=2, sticky="we", pady=(12, 4))

        btn_open_latest = tb.Button(frm, text="Otvoriť najnovšiu verziu", command=self.on_open_latest, bootstyle=PRIMARY)
        btn_open_latest.grid(row=5, column=1, columnspan=2, sticky="we", pady=(4, 0))

        # Shortcuts
        root.bind("<Return>", lambda e: self.on_login())

        for c in range(3):
            frm.columnconfigure(c, weight=1)

    def toggle_password(self):
        self.ent_pass.config(show="" if self.var_show_password.get() else "•")

    def on_login(self):
        username = self.var_username.get().strip()
        password = self.var_password.get()

        if not username or not password:
            messagebox.showwarning("Chýbajú údaje", "Zadaj používateľské meno aj heslo.")
            return

        user = verify_user_online(username, password)
        if not user:
            messagebox.showerror("Neplatné údaje", "Prihlásenie zlyhalo. Skontroluj meno/heslo.")
            return

        # Save remember
        if self.var_remember.get():
            save_config({"remember": True, "username": username, "password": password})
        else:
            save_config({"remember": False})

        run_launcher(meno=user.get("meno", ""), priezvisko=user.get("priezvisko", ""), open_latest=False)

    def on_open_latest(self):
        """
        Ak sú práve zadané a platné prihlasovacie údaje, prenesieme meno/priezvisko.
        Inak otvoríme len najnovší bez mena/priezviska.
        """
        username = self.var_username.get().strip()
        password = self.var_password.get()

        meno = ""
        priezvisko = ""
        if username and password:
            user = verify_user_online(username, password)
            if user:
                meno = user.get("meno", "")
                priezvisko = user.get("priezvisko", "")

        run_launcher(meno=meno, priezvisko=priezvisko, open_latest=True)

def main():
    # jednotný vzhľad s tvojím GUI
    style = tb.Style(theme="litera")
    root = style.master
    try:
        root.tk.call("tk", "scaling", 1.15)
    except Exception:
        pass
    app = LoginApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
