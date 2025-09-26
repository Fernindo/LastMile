# login.py
import os
import sys
import json
import subprocess
import argparse
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from gui_functions import get_database_connection  # tvoje napojenie na online DB
from helpers import (
    ensure_user_config,
    encrypt_string_for_user,
    decrypt_string_if_encrypted,
    secure_load_config,
    secure_save_config,
    enable_high_dpi_awareness,
    calibrate_tk_scaling,
    apply_ttk_base_font,
)

import project_selector 
import gui_functions
import excel_processing
import doprava
import gui
from updater import check_for_updates

# Run on startup or add a button
root = tb.Window(themename="litera")
#check_for_updates(root)





# Ensure DPI awareness early (before any Tk roots are created)
try:
    enable_high_dpi_awareness()
except Exception:
    pass


APP_TITLE = "Prihlásenie"
CONFIG_FILE = "login_config.json"              # lokálne ukladanie "zapamätaj si" a logged_in
PROJECT_SELECTOR_FILE = "project_selector.py"  # po prihlásení spúšťame selector (ak nie je --no-launch)

# ───────────────────────── Helpery ─────────────────────────

def resource_path(rel_path: str) -> str:
    """Get absolute path for bundled, read-only resources (dev + PyInstaller)."""
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, rel_path)

def app_dir() -> str:
    """Directory of the app/executable (writable location)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def config_path(filename: str) -> str:
    """Path for app settings persisted next to the EXE (writable)."""
    return os.path.join(app_dir(), filename)

def load_config() -> dict:
    """Load encrypted login config from the user config directory.
    Decrypt stored password for use in the UI (if present).
    """
    data = secure_load_config(
        CONFIG_FILE,
        default_content={
            "logged_in": False,
            "remember": False,
            "username": "",
            "password": "",
            "user": {},
        },
    )
    if isinstance(data, dict) and "password" in data:
        data["password"] = decrypt_string_if_encrypted(data.get("password", ""))
    return data or {}


def save_config(cfg_updates: dict):
    """Safely merge and persist encrypted login config."""
    current = secure_load_config(CONFIG_FILE, default_content={})
    upd = dict(cfg_updates or {})
    if isinstance(upd.get("password"), str) and upd["password"]:
        upd["password"] = encrypt_string_for_user(upd["password"])
    current.update(upd)
    secure_save_config(CONFIG_FILE, current)

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
            # fallback (napr. sqlite)
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
    finally:
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

    # Plaintext kontrola podľa tvojich dát (nahradíš hash porovnaním, keď budeš mať hashované heslá)
    if str(password) == str(user["password"]):
        return user
    return None


def run_project_selector_and_exit(root=None):
    """
    Closes the login window and launches the Project Selector
    in a fresh root (single EXE).
    """
    try:
        import project_selector

        # Hide the login window (keep Tk app alive)
        if root is not None:
            try:
                root.withdraw()
            except Exception:
                pass

        # Now start the selector as a child of the existing root
        project_selector.main(parent=root)

    except Exception as e:
        messagebox.showerror("Chyba", f"Nepodarilo sa spustiť Project Selector:\n{e}")
    finally:
        # Don’t kill the process here! (otherwise selector dies too)
        pass


# ───────────────────────── UI ─────────────────────────

class LoginApp:
    def __init__(self, root, no_launch: bool = False):
        self.root = root
        self.no_launch = no_launch

        root.title(APP_TITLE)
        # Sizing and scaling handled centrally in main(); keep just resizable here
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

        title = tb.Label(frm, text="Prihlásenie", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")

        # Username
        tb.Label(frm, text="Používateľ:").grid(row=1, column=0, sticky="w")
        self.ent_user = tb.Entry(frm, textvariable=self.var_username, width=22, bootstyle=INFO)
        self.ent_user.grid(row=1, column=1, columnspan=2, sticky="we", pady=(0, 6))

        # Password
        tb.Label(frm, text="Heslo:").grid(row=2, column=0, sticky="w")
        self.ent_pass = tb.Entry(frm, textvariable=self.var_password, show="•", width=22, bootstyle=INFO)
        self.ent_pass.grid(row=2, column=1, sticky="we", pady=(0, 6))
        chk_show = tb.Checkbutton(
            frm, text="Zobraziť heslo",
            variable=self.var_show_password,
            command=self.toggle_password,
            bootstyle=SECONDARY
        )
        chk_show.grid(row=2, column=2, sticky="w")

        # Remember me
        chk_rem = tb.Checkbutton(frm, text="Uložiť prihlásenie", variable=self.var_remember, bootstyle=SECONDARY)
        chk_rem.grid(row=3, column=1, columnspan=2, sticky="w")

        # Buttons
        btn_login = tb.Button(frm, text="Prihlásiť sa", command=self.on_login, bootstyle=SUCCESS)
        btn_login.grid(row=4, column=1, columnspan=2, sticky="we", pady=(12, 4))

        # Shortcuts
        root.bind("<Return>", lambda e: self.on_login())

        for c in range(3):
            frm.columnconfigure(c, weight=1)

    def toggle_password(self):
        self.ent_pass.config(show="" if self.var_show_password.get() else "•")

    def _persist_login_config(self, username: str, password: str, user: dict):
        """
        Uloží remember a stav prihlásenia tak, aby Project Selector vedel
        prepnúť farbu tlačidla (pollingom) a aby sme mali meno/priezvisko.
        """
        payload = {
            "logged_in": True,
            "user": {
                "id": user.get("id"),
                "username": user.get("username", username),
                "meno": user.get("meno", ""),
                "priezvisko": user.get("priezvisko", ""),
            }
        }
        if self.var_remember.get():
            payload.update({
                "remember": True,
                "username": username,
                "password": password,
            })
        else:
            payload.update({
                "remember": False,
                "username": "",
                "password": "",
            })
        save_config(payload)

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

        # Save config (remember + logged_in + user info)
        self._persist_login_config(username, password, user)

        # Ak bol login spustený zo Selectora s --no-launch, iba zavri okno
        if self.no_launch:
            self.root.destroy()
            return

        # Inak spusti Project Selector a ukonči tento proces
        run_project_selector_and_exit(self.root)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-launch",
        action="store_true",
        help="Po úspešnom prihlásení nespúšťať Project Selector, iba zavrieť login."
    )
    args = parser.parse_args()

    # jednotný vzhľad s tvojím GUI
    style = tb.Style(theme="litera")
    root = style.master

    # Unified DPI scaling and sizing
    try:
        enable_high_dpi_awareness()
    except Exception:
        pass
    try:
        scale = float(calibrate_tk_scaling(root))
    except Exception:
        scale = 1.25
    # Window size for login window (keep existing base dimensions)
    base_w, base_h = 520, 200
    try:
        root.geometry(f"{int(base_w * scale)}x{int(base_h * scale)}")
    except Exception:
        pass
    # Base fonts and button paddings
    try:
        apply_ttk_base_font(style, family="Segoe UI", size=int(10 * scale))
    except Exception:
        pass
    try:
        root.option_add("*Font", ("Segoe UI", int(10 * scale)))
    except Exception:
        pass
    try:
        pad = (int(8 * scale), int(4 * scale))
        for _btn_style in (
            "TButton",
            "secondary.TButton",
            "success.TButton",
            "danger.TButton",
            "info.TButton",
        ):
            try:
                style.configure(_btn_style, padding=pad)
            except Exception:
                pass
    except Exception:
        pass

    app = LoginApp(root, no_launch=args.no_launch)
    root.mainloop()

if __name__ == "__main__":
    main()


