import os
import json
import shutil
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, filedialog, simpledialog
from datetime import datetime
import subprocess
import sys
import re
from gui_functions import get_database_connection
from helpers import (
    ensure_user_config,
    secure_load_json,
    secure_save_json,
    enable_high_dpi_awareness,
    calibrate_tk_scaling,
    apply_ttk_base_font,
)

# Legacy compatibility: some builds still call show_presets_window from the top bar.
# We keep a no-op stub so the UI can hide the old button without NameError.
def show_presets_window():
    pass


# Single-app Projects Home embedded in project_selector.py
# No new code files. Only creates project JSONs when you make a new project.

UI_SETTINGS_FILE = ensure_user_config("ui_settings.json")

# Global scale multiplier for Project Selector UI.
# Increase (>1.0) to make items larger; e.g. 1.15 = +15%.
project_scale = 1.4

# --- UI profile helpers (auto-detected only) --------------------------------
def _get_ui_profile(root: tk.Misc) -> str:
    # Always auto-detect based on screen width; manual options removed
    try:
        sw = int(root.winfo_screenwidth())
    except Exception:
        sw = 1920
    return "27" if sw >= 2300 else "13"

def _profile_scale(profile: str, root: tk.Misc) -> float:
    if profile == "27":
        return 1.35
    if profile == "13":
        return 1.00
    try:
        sw = int(root.winfo_screenwidth())
    except Exception:
        sw = 1920
    return 1.35 if sw >= 2300 else 1.00

# ───────────────────────── Helpers: settings ─────────────────────────

def load_settings():
    return secure_load_json(UI_SETTINGS_FILE, default={})
    return {}
LOGIN_CONFIG_FILE = ensure_user_config("login_config.json")
def load_login_user():
    data = secure_load_json(LOGIN_CONFIG_FILE, default={})
    return (data or {}).get("user") or {}

def load_skip_login() -> bool:
    data = secure_load_json(LOGIN_CONFIG_FILE, default={})
    return bool((data or {}).get("skip_login", False))

def set_skip_login(value: bool):
    data = secure_load_json(LOGIN_CONFIG_FILE, default={})
    data["skip_login"] = bool(value)
    secure_save_json(LOGIN_CONFIG_FILE, data)

def load_login_state() -> bool:
    data = secure_load_json(LOGIN_CONFIG_FILE, default={})
    return bool((data or {}).get("logged_in", False))
def set_logged_out():
    data = secure_load_json(LOGIN_CONFIG_FILE, default={})
    data["logged_in"] = False
    secure_save_json(LOGIN_CONFIG_FILE, data)

def save_settings(data):
    try:
        secure_save_json(UI_SETTINGS_FILE, data)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot save settings:\n{e}")

def get_projects_root():
    st = load_settings()
    # fallback to a local "workspace" folder next to the EXE
    return st.get("projects_root", os.path.abspath(os.path.join(os.path.dirname(UI_SETTINGS_FILE), "workspace")))

def set_projects_root(path):
    st = load_settings()
    st["projects_root"] = path
    save_settings(st)

# ─────────────────────── Helpers: projects & archive ───────────────────────
def resolve_author_from_json(json_path: str) -> str:
    """
    Vráti 'Priezvisko M.' podľa posledného ukladateľa.
    1) Skúsi priamo JSON kľúč 'author'
    2) Fallback: 'user_id' alebo 'username' -> dotiahne meno/priezvisko z tabuľky users
    """
    username = ""
    user_id = None

    try:
        data = secure_load_json(json_path, default={})
        if isinstance(data, dict):
            # Ak už nové GUI zapisuje 'author', stačí ho použiť
            if data.get("author"):
                return str(data["author"])
            username = (data.get("username") or "").strip()
            user_id = data.get("user_id")
    except Exception:
        pass

    # Ak nemáme identifikátor, nevieme určiť
    if user_id is None and not username:
        return ""

    try:
        conn, db_type = get_database_connection()
        cur = conn.cursor()
        if user_id is not None:
            sql = "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE id = %s" \
                  if db_type == "postgres" else \
                  "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE id = ?"
            cur.execute(sql, (user_id,))
        else:
            sql = "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE username = %s LIMIT 1" \
                  if db_type == "postgres" else \
                  "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE username = ? LIMIT 1"
            cur.execute(sql, (username,))
        row = cur.fetchone()
        conn.close()
        if row:
            meno, priezvisko = row[0] or "", row[1] or ""
            return f"{priezvisko} {meno[:1]}.".strip()
    except Exception:
        pass

    return ""

# override with full-name resolution preferred over abbreviated author
def resolve_author_from_json(json_path: str) -> str:
    username = ""
    user_id = None
    author_str = ""
    created_by = ""
    cb_username = ""
    cb_user_id = None

    try:
        data = secure_load_json(json_path, default={})
        if isinstance(data, dict):
            author_str = str(data.get("author") or "").strip()
            username = (data.get("username") or "").strip()
            user_id = data.get("user_id")
            created_by = str(data.get("created_by") or "").strip()
            cb_username = (data.get("created_by_username") or "").strip()
            cb_user_id = data.get("created_by_id")
    except Exception:
        pass

    # Prefer resolving full name from DB if we have any identifier
    cand_user_id = user_id if (user_id is not None) else cb_user_id
    cand_username = username or cb_username
    if cand_user_id is not None or cand_username:
        try:
            conn, db_type = get_database_connection()
            cur = conn.cursor()
            if cand_user_id is not None:
                sql = (
                    "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE id = %s"
                    if db_type == "postgres"
                    else "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE id = ?"
                )
                cur.execute(sql, (cand_user_id,))
            else:
                sql = (
                    "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE username = %s LIMIT 1"
                    if db_type == "postgres"
                    else "SELECT COALESCE(meno,''), COALESCE(priezvisko,'') FROM users WHERE username = ? LIMIT 1"
                )
                cur.execute(sql, (cand_username,))
            row = cur.fetchone()
            conn.close()
            if row:
                meno, priezvisko = row[0] or "", row[1] or ""
                full = f"{meno} {priezvisko}".strip()
                if full:
                    return full
        except Exception:
            pass

    if cand_username:
        return cand_username
    if created_by:
        return created_by
    if author_str:
        return author_str
    return ""

def discover_projects(root):
    """Rýchlejšie prehľadanie priečinka pomocou os.scandir."""
    items = []
    if not os.path.isdir(root):
        return items
    try:
        with os.scandir(root) as it:
            for entry in it:
                if not entry.is_dir():
                    continue
                json_dir = os.path.join(entry.path, "projects")
                if os.path.isdir(json_dir):
                    items.append({"name": entry.name, "path": entry.path})
        items.sort(key=lambda x: x["name"].lower())
    except Exception:
        pass
    return items

def project_archive(project_path):
    json_dir = os.path.join(project_path, "projects")
    if not os.path.isdir(json_dir):
        return []
    files = []
    try:
        with os.scandir(json_dir) as it:
            for entry in it:
                if entry.is_file() and entry.name.lower().endswith('.json'):
                    try:
                        mtime = entry.stat().st_mtime
                    except Exception:
                        mtime = 0
                    files.append((mtime, entry.path))
        files.sort(key=lambda t: t[0], reverse=True)  # newest first
        return [p for _, p in files]
    except Exception:
        return []

def create_project(root, name, street=None, area=None):
    if not name:
        raise ValueError("Project name is required.")
    safe = name.strip()
    if not safe:
        raise ValueError("Project name is required.")
    proj_dir = os.path.join(root, safe)
    json_dir = os.path.join(proj_dir, "projects")
    os.makedirs(json_dir, exist_ok=True)
    # Seed one main JSON if missing
    main_json = os.path.join(json_dir, f"{safe}.json")
    if not os.path.exists(main_json):
        # Capture current logged-in user to mark the creator
        try:
            u = load_login_user() if load_login_state() else {}
        except Exception:
            u = {}

        meno = (u.get("meno") or "").strip()
        priezvisko = (u.get("priezvisko") or "").strip()
        username = (u.get("username") or "").strip()
        user_id = u.get("id")
        creator = f"{meno} {priezvisko}".strip() if (meno or priezvisko) else (username or "")

        payload = {
            "project": safe,
            "street": (street or "").strip() if isinstance(street, str) else street,
            "area": area,
            "created": datetime.now().isoformat(),
        }
        # Add creator/author metadata if available
        if creator:
            payload.update({
                "author": creator,
                "username": username,
                "user_id": user_id,
                # Persist original creator explicitly so it can survive later saves
                "created_by": creator,
                "created_by_username": username,
                "created_by_id": user_id,
            })
        secure_save_json(main_json, payload)
    return {"name": safe, "path": proj_dir, "json": main_json}

# ─────────────────────────── Launch GUI safely ───────────────────────────

def launch_gui_in_same_root(root, project_dir, json_path, *, preset_mode: bool=False):
    set_projects_root(root.projects_home_state["projects_root"].get())
    master_obj = root
    try:
        # If selector was opened from login (Toplevel with a parent),
        # destroy only the selector Toplevel and keep the master alive.
        # Otherwise (standalone root), just withdraw it so GUI can run
        # within the same Tcl interpreter safely.
        if root.winfo_parent():
            try:
                root.destroy()
            except Exception:
                try:
                    root.withdraw()
                except Exception:
                    pass
            # Keep the parent (e.g., login root) withdrawn
            try:
                root.master.withdraw()
                master_obj = root.master
            except Exception:
                pass
        else:
            try:
                root.withdraw()
            except Exception:
                pass
    except Exception:
        pass

    # načítaj prihláseného používateľa (ak skip, nech je prázdny)
    u = load_login_user() if load_login_state() else {}

    import gui
    try:
        master_obj.after(0, lambda: gui.start(
            project_dir,
            json_path,
            meno=u.get("meno", ""),
            priezvisko=u.get("priezvisko", ""),
            username=u.get("username", ""),
            preset_mode=preset_mode
        ))
    except Exception:
        gui.start(
            project_dir,
            json_path,
            meno=u.get("meno", ""),
            priezvisko=u.get("priezvisko", ""),
            username=u.get("username", ""),
            preset_mode=preset_mode
        )

# ──────────────────────────────── Main UI ────────────────────────────────



def main(parent=None):
    # If launched from login.py, we pass parent
    # If run directly, create its own root window
    if parent is None:
        try:
            enable_high_dpi_awareness()
        except Exception:
            pass
        style = Style(theme="litera")
        root = style.master
        # Calibrate for DPI, then apply 13"/27" profile scaling
        try:
            calibrate_tk_scaling(root)
        except Exception:
            pass
        ui_profile = _get_ui_profile(root)
        scale = _profile_scale(ui_profile, root)
        try:
            scale = float(scale) * float(project_scale)
        except Exception:
            pass
        try:
            root.tk.call("tk", "scaling", float(scale))
        except Exception:
            pass
        try:
            # Base font for ttk widgets in Project Selector (smaller baseline)
            apply_ttk_base_font(style, family="Segoe UI", size=int(8 * scale))
        except Exception:
            pass
        # Make ttk buttons scale with the global scale; keep 13" compact baseline
        try:
            if ui_profile == "13":
                for _btn_style in ("TButton", "secondary.TButton", "success.TButton", "danger.TButton", "info.TButton"):
                    try:
                        style.configure(_btn_style, padding=(6, 3))
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            pad_x = max(10, int(12 * float(scale)))
            pad_y = max(6, int(6 * float(scale)))
            btn_font_size = max(11, int(2 * float(scale)))
            _btn_styles = (
                "TButton",
                "primary.TButton",
                "secondary.TButton",
                "success.TButton",
                "danger.TButton",
                "info.TButton",
                "warning.TButton",
                "light.TButton",
                "primary.Outline.TButton",
                "secondary.Outline.TButton",
                "success.Outline.TButton",
                "danger.Outline.TButton",
                "info.Outline.TButton",
                "warning.Outline.TButton",
                "light.Outline.TButton",
                # Menubutton styles for user menu
                "TMenubutton",
                "primary.TMenubutton",
                "secondary.TMenubutton",
            )
            for _s in _btn_styles:
                try:
                    style.configure(_s, padding=(pad_x, pad_y), font=("Segoe UI", btn_font_size))
                except Exception:
                    pass
        except Exception:
            pass
        # Ensure classic Tk widgets (e.g., Listbox) also use scaled base size (smaller)
        try:
            root.option_add("*Font", ("Segoe UI", int(8 * scale)))
        except Exception:
            pass
        root.title("Projects Home")
        # Dynamic geometry based on screen size (centers window)
        try:
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            margin = 80
            # Scale window relative to screen with sane bounds
            target_w = int(min(max(int(sw * 0.75), 900), sw - margin))
            target_h = int(min(max(int(sh * 0.75), 600), sh - margin))
            x = max(0, (sw - target_w) // 2)
            y = max(0, (sh - target_h) // 2)
            root.geometry(f"{target_w}x{target_h}+{x}+{y}")
            # Allow resizing, but ensure minimum fits smaller displays
            root.minsize(min(900, sw - margin), min(600, sh - margin))
            root.resizable(True, True)
        except Exception:
            # Fallback geometry if anything goes wrong
            root.geometry("1000x700")
            try:
                root.minsize(900, 600)
                root.resizable(True, True)
            except Exception:
                pass
        owns_root = True
    else:
        # Create a child window on the existing Tk root
        root = tb.Toplevel(parent)
        # Ensure we get a Style object to tweak paddings for this window too
        try:
            style = Style()
            # Calibrate for DPI, then apply 13"/27" profile scaling
            try:
                calibrate_tk_scaling(root)
            except Exception:
                pass
            ui_profile = _get_ui_profile(root)
            scale = _profile_scale(ui_profile, root)
            try:
                scale = float(scale) * float(project_scale)
            except Exception:
                pass
            try:
                root.tk.call("tk", "scaling", float(scale))
            except Exception:
                pass
            try:
                apply_ttk_base_font(style, family="Segoe UI", size=int(8 * scale))
            except Exception:
                pass
            for _btn_style in ("TButton", "secondary.TButton", "success.TButton", "danger.TButton", "info.TButton"):
                try:
                    if ui_profile == "13":
                        style.configure(_btn_style, padding=(6, 3))
                except Exception:
                    pass
            try:
                pad_x = max(10, int(12 * float(scale)))
                pad_y = max(6, int(6 * float(scale)))
                btn_font_size = max(11, int(12 * float(scale)))
                _btn_styles = (
                    "TButton",
                    "primary.TButton",
                    "secondary.TButton",
                    "success.TButton",
                    "danger.TButton",
                    "info.TButton",
                    "warning.TButton",
                    "light.TButton",
                    "primary.Outline.TButton",
                    "secondary.Outline.TButton",
                    "success.Outline.TButton",
                    "danger.Outline.TButton",
                    "info.Outline.TButton",
                    "warning.Outline.TButton",
                    "light.Outline.TButton",
                    "TMenubutton",
                    "primary.TMenubutton",
                    "secondary.TMenubutton",
                )
                for _s in _btn_styles:
                    try:
                        style.configure(_s, padding=(pad_x, pad_y), font=("Segoe UI", btn_font_size))
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass
        root.title("Projects Home")
        # Dynamic geometry for child window as well
        try:
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            margin = 80
            target_w = int(min(max(int(sw * 0.75), 900), sw - margin))
            target_h = int(min(max(int(sh * 0.75), 600), sh - margin))
            x = max(0, (sw - target_w) // 2)
            y = max(0, (sh - target_h) // 2)
            root.geometry(f"{target_w}x{target_h}+{x}+{y}")
            root.minsize(min(900, sw - margin), min(600, sh - margin))
            root.resizable(True, True)
        except Exception:
            root.geometry("1024x700")
            try:
                root.minsize(900, 600)
                root.resizable(True, True)
            except Exception:
                pass
        owns_root = False
        # Closing the selector should close the whole app
        try:
            root.protocol("WM_DELETE_WINDOW", parent.destroy)
        except Exception:
            pass

    # Keep a small state dict on the root so helper functions can access it
    root.projects_home_state = {
        "projects_root": tk.StringVar(value=get_projects_root()),
        "projects": [],
        "selected_project": None,
        "filter_text": tk.StringVar(),
    }

    # Top bar
    top = tb.Frame(root, padding=10)
    top.pack(side="top", fill="x")

    # Label showing logged-in user's name (auto-updated)
    login_name_var = tk.StringVar()

    def _compute_login_name() -> str:
        try:
            if not load_login_state():
                return ""
            u = load_login_user() or {}
            meno = (u.get("meno") or "").strip()
            priezvisko = (u.get("priezvisko") or "").strip()
            if meno or priezvisko:
                return f"Prihlásený: {meno} {priezvisko}".strip()
            username = (u.get("username") or "").strip()
            if username:
                return f"Prihlásený: {username}"
            return ""
        except Exception:
            return ""

    login_name_var.set(_compute_login_name())
    # Replace static label with a bordered, clickable user menu
    user_menu_btn = tb.Menubutton(
        top,
        textvariable=login_name_var,
        bootstyle="secondary-outline"
    )
    user_menu = tk.Menu(user_menu_btn, tearoff=False)
    def do_logout():
        set_logged_out()
        login_btn.configure(bootstyle="danger")
        login_name_var.set("")
        # re-show login button and hide user menu on logout
        try:
            if not login_btn.winfo_ismapped():
                login_btn.pack(side="right", padx=(6, 0))
        except Exception:
            pass
        try:
            if user_menu_btn.winfo_ismapped():
                user_menu_btn.pack_forget()
        except Exception:
            pass
    user_menu.add_command(label="Odhlásiť sa", command=do_logout)
    try:
        user_menu_btn["menu"] = user_menu
    except Exception:
        pass
    # show only when logged in
    if load_login_state() and login_name_var.get():
        user_menu_btn.pack(side="right", padx=(6, 0))

    tb.Label(top, text="Projects Root:").pack(side="left")
    # Wider entry so long paths don't feel cramped
    root_entry = tb.Entry(top, textvariable=root.projects_home_state["projects_root"], width=72)
    root_entry.pack(side="left", padx=6)

    def browse_root():
        cur = root.projects_home_state["projects_root"].get()
        path = filedialog.askdirectory(initialdir=cur or os.getcwd(), title="Choose Projects Root")
        if path:
            root.projects_home_state["projects_root"].set(path)
            set_projects_root(path)
            # Rescan filesystem only when root changes
            rescan_projects()
            refresh_projects()
            # no extra mainloop() calls here

    def open_preset_builder():
        pr_root = root.projects_home_state["projects_root"].get() or os.getcwd()
        name = "PresetBuilder"
        proj_dir = os.path.join(pr_root, name)
        json_dir = os.path.join(proj_dir, "projects")
        os.makedirs(json_dir, exist_ok=True)
        json_path = os.path.join(json_dir, f"{name}.json")
        if not os.path.exists(json_path):
            try:
                # Capture current logged-in user to mark the creator
                try:
                    u = load_login_user() if load_login_state() else {}
                except Exception:
                    u = {}
                meno = (u.get("meno") or "").strip()
                priezvisko = (u.get("priezvisko") or "").strip()
                username = (u.get("username") or "").strip()
                user_id = u.get("id")
                creator = f"{meno} {priezvisko}".strip() if (meno or priezvisko) else (username or "")

                payload = {
                    "project": name,
                    "created": datetime.now().isoformat(),
                    "notes": []
                }
                if creator:
                    payload.update({
                        "author": creator,
                        "username": username,
                        "user_id": user_id,
                        "created_by": creator,
                        "created_by_username": username,
                        "created_by_id": user_id,
                    })
                secure_save_json(json_path, payload)
            except Exception:
                pass
            
        launch_gui_in_same_root(root, proj_dir, json_path, preset_mode=True)

    tb.Button(top, text="Browse…", bootstyle="secondary", command=browse_root).pack(side="left")
    tb.Button(top, text="📦 Presets", bootstyle="secondary", command=show_presets_window).pack(side="left", padx=(6, 0))
    def open_login():
        login_path = os.path.join(os.path.dirname(__file__), "login.py")
        if not os.path.isfile(login_path):
            messagebox.showerror("Chyba", "login.py sa nenašiel.")
            return
        try:
            subprocess.Popen([sys.executable, login_path, "--no-launch"],
                             cwd=os.path.dirname(login_path) or None)
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodarilo sa spustiť login.py:\n{e}")
    

    # inicializačný štýl podľa aktuálneho stavu
    login_btn = tb.Button(
        top,
        text="Prihlásenie",
        bootstyle=("success" if load_login_state() else "danger"),
        command=open_login
    )
    # show login button only when not logged in
    if not load_login_state():
        login_btn.pack(side="right", padx=(6, 0))

    # Hide legacy 'Presets' popup button; keep only 'Presets DB'
    try:
        for _w in top.winfo_children():
            try:
                txt = _w.cget("text")
            except Exception:
                continue
            if isinstance(txt, str) and ("Presets" in txt) and ("DB" not in txt):
                try:
                    _w.pack_forget()
                except Exception:
                    pass
    except Exception:
        pass

    # Preset Builder (database) — opens the full app in preset mode
    tb.Button(top, text="Presets DB", bootstyle="secondary", command=open_preset_builder).pack(side="left", padx=(6, 0))

    # periodická kontrola súboru login_config.json a aktualizácia farby
    def refresh_login_btn():
        try:
            is_in = load_login_state()
            login_btn.configure(bootstyle=("success" if is_in else "danger"))
            login_name_var.set(_compute_login_name())
            # toggle login button visibility depending on state
            try:
                if is_in and login_btn.winfo_ismapped():
                    login_btn.pack_forget()
                elif (not is_in) and (not login_btn.winfo_ismapped()):
                    login_btn.pack(side="right", padx=(6, 0))
            except Exception:
                pass
            # voliteľne zmeň text (napr. „Prihlásený“ / „Prihlásenie“):
            # login_btn.configure(text=("Prihlásený" if is_in else "Prihlásenie"))
        except Exception:
            # ak by bol súbor počas zápisu, ignoruj chybu a skús znova
            pass
        finally:
            root.after(2000, refresh_login_btn)  # každé 2 sekundy

    def refresh_user_menu_btn():
        try:
            is_in = load_login_state()
            login_name_var.set(_compute_login_name())
            try:
                if is_in and (not user_menu_btn.winfo_ismapped()) and login_name_var.get():
                    user_menu_btn.pack(side="right", padx=(6, 0))
                elif (not is_in) and user_menu_btn.winfo_ismapped():
                    user_menu_btn.pack_forget()
            except Exception:
                pass
        except Exception:
            pass
        finally:
            root.after(2000, refresh_user_menu_btn)

    refresh_user_menu_btn()
    refresh_login_btn()
    
    # tlačidlo Odhlásiť (X)
    def _do_logout_legacy_unused():
        set_logged_out()
        login_btn.configure(bootstyle="danger")
        login_name_var.set("")
        # ensure login button visible after logout
        try:
            if not login_btn.winfo_ismapped():
                login_btn.pack(side="right", padx=(6, 0))
        except Exception:
            pass
        # voliteľne môžeš zmeniť aj text
        # login_btn.configure(text="Prihlásenie")

    # removed old logout (X) button; handled via user name menu


    def create_project_dialog():
        """Otvorí malé okno pre zadanie názvu, ulice a plochy."""
        dlg = tb.Toplevel(root)
        dlg.title("Nový projekt")
        dlg.resizable(False, False)
        dlg.transient(root)
        dlg.grab_set()

        frm = tb.Frame(dlg, padding=12)
        frm.pack(fill="both", expand=True)

        name_var = tk.StringVar()
        street_var = tk.StringVar()
        area_var = tk.StringVar()

        # Názov
        tb.Label(frm, text="Názov projektu:").grid(row=0, column=0, sticky="w", padx=(0,8), pady=(0,6))
        name_entry = tb.Entry(frm, textvariable=name_var, width=36)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0,6))

        # Ulica
        tb.Label(frm, text="Ulica:").grid(row=1, column=0, sticky="w", padx=(0,8), pady=(0,6))
        street_entry = tb.Entry(frm, textvariable=street_var, width=36)
        street_entry.grid(row=1, column=1, sticky="ew", pady=(0,6))

        # Plocha
        tb.Label(frm, text="Plocha (m²):").grid(row=2, column=0, sticky="w", padx=(0,8), pady=(0,10))
        area_entry = tb.Entry(frm, textvariable=area_var, width=18)
        area_entry.grid(row=2, column=1, sticky="w", pady=(0,10))

        frm.columnconfigure(1, weight=1)

        result = {"ok": False}

        def on_ok():
            name = (name_var.get() or "").strip()
            if not name:
                messagebox.showwarning("Chýba názov", "Zadajte názov projektu.", parent=dlg)
                return
            # Parse area as float if provided
            area_txt = (area_var.get() or "").strip()
            area_val = None
            if area_txt:
                try:
                    # allow comma decimal
                    area_val = float(area_txt.replace(",", "."))
                except ValueError:
                    messagebox.showwarning("Neplatná plocha", "Plocha musí byť číslo.", parent=dlg)
                    return
            result.update({
                "ok": True,
                "name": name,
                "street": (street_var.get() or "").strip(),
                "area": area_val,
            })
            dlg.destroy()

        def on_cancel():
            dlg.destroy()

        btns = tb.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e")
        tb.Button(btns, text="Zrušiť", bootstyle="secondary", command=on_cancel).pack(side="right", padx=(0,6))
        tb.Button(btns, text="Vytvoriť", bootstyle="success", command=on_ok).pack(side="right")

        name_entry.focus_set()
        dlg.bind("<Return>", lambda e: on_ok())
        dlg.bind("<Escape>", lambda e: on_cancel())

        root.wait_window(dlg)

        if not result.get("ok"):
            return

        try:
            info = create_project(
                root.projects_home_state["projects_root"].get(),
                result["name"],
                street=result.get("street"),
                area=result.get("area"),
            )
        except Exception as e:
            messagebox.showerror("Vytvorenie projektu zlyhalo", str(e))
            return
        rescan_projects()
        refresh_projects()
        select_project_by_name(info["name"])

    # Moved Create Project button into the left panel above Delete

    # Body: left projects list (with Delete), right archive list
    body = tb.Frame(root, padding=10)
    body.pack(fill="both", expand=True)

    left = tb.Labelframe(body, text="Projects", padding=8)
    # Make the left projects column slightly thinner
    try:
        _left_w = max(260, int(300 * float(scale)))
    except Exception:
        _left_w = 300
    left.config(width=_left_w)
    left.pack_propagate(False)
    left.pack(side="left", fill="y", padx=(0, 12))
    tb.Label(left, text="Filter:").pack(anchor="w")
    filter_entry = tb.Entry(left, textvariable=root.projects_home_state["filter_text"])
    filter_entry.pack(fill="x", pady=(0, 6))
    right = tb.Labelframe(body, text="Archive", padding=8)
    right.pack(side="left", fill="both", expand=True)

    # Let the list expand to fill the left panel
    proj_list = tk.Listbox(left, height=24)
    proj_list.pack(fill="both", expand=True)

    # Project action buttons
    proj_btns = tb.Frame(left)
    proj_btns.pack(fill="x", pady=(8, 0))
    create_btn = tb.Button(proj_btns, text="Vytvoriť projekt", bootstyle="success", command=create_project_dialog)
    create_btn.pack(fill="x")
    delete_btn = tb.Button(proj_btns, text="Delete Project", bootstyle="danger")
    delete_btn.pack(fill="x", pady=(6, 0))
    # Slightly enlarge the create/delete buttons (padding scale-aware)
    try:
        _bx = max(8, int(10 * float(scale)))
        _by = max(4, int(6 * float(scale)))
        create_btn.configure(padding=(_bx, _by))
        delete_btn.configure(padding=(_bx, _by))
    except Exception:
        pass

    archive_list = tk.Listbox(right)
    archive_list.pack(fill="both", expand=True)

    buttons = tb.Frame(right)
    buttons.pack(fill="x", pady=6)
    open_btn = tb.Button(buttons, text="Open Selected", bootstyle="info")
    open_btn.pack(side="left")

    # ─────────────────────────── Behaviors ───────────────────────────

    def refresh_projects(*_):
        """Refresh only the UI list from in-memory projects and current filter."""
        projects = root.projects_home_state["projects"]
        proj_list.delete(0, "end")
        flt = root.projects_home_state["filter_text"].get().lower()
        for item in projects:
            name = item["name"]
            if flt and flt not in name.lower():
                continue
            proj_list.insert("end", name)
        archive_list.delete(0, "end")
        archive_list._files = []
        root.projects_home_state["selected_project"] = None
        delete_btn.configure(state="disabled")

    # Debounced filter to avoid rescanning/redrawing on each keystroke
    _filter_after = [None]
    def _on_filter_change(*_args):
        if _filter_after[0] is not None:
            try:
                root.after_cancel(_filter_after[0])
            except Exception:
                pass
        _filter_after[0] = root.after(120, refresh_projects)
    root.projects_home_state["filter_text"].trace_add("write", _on_filter_change)

    def rescan_projects():
        projects = discover_projects(root.projects_home_state["projects_root"].get())
        root.projects_home_state["projects"] = projects

    def select_project_by_name(name):
        for idx, item in enumerate(root.projects_home_state["projects"]):
            if item["name"] == name:
                proj_list.selection_clear(0, "end")
                proj_list.selection_set(idx)
                on_project_select(None)
                break

    def on_project_select(event):
        sel = proj_list.curselection()
        if not sel:
            delete_btn.configure(state="disabled")
            return
        idx = sel[0]
        proj = root.projects_home_state["projects"][idx]
        root.projects_home_state["selected_project"] = proj
        delete_btn.configure(state="normal")

        archive_list.delete(0, "end")
        files = project_archive(proj["path"])
        for fp in files:
            base = os.path.basename(fp)
            ts = datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M")
            who = resolve_author_from_json(fp)
            # Strip extension and trailing timestamp suffix from filename, keep only save name
            stem = base[:-5] if base.lower().endswith('.json') else base
            m = re.match(r"^(?P<name>.+?)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$", stem)
            nice_name = m.group('name') if m else stem
            line = f"{ts}  |  {nice_name}"
            if who:
                line += f"  |  {who}"
            archive_list.insert("end", line)

        archive_list._files = files  


    def open_selected():
        if not load_login_state() and not load_skip_login():
            messagebox.showwarning(
            "Prihlásenie",
            "Aby si mohol otvoriť projekt, prihlás sa (alebo dočasne povol 'Skip prihlásenia')."
        )
            return
        proj = root.projects_home_state["selected_project"]
        if not proj:
            messagebox.showwarning("No project selected", "Please select a project.")
            return
        files = getattr(archive_list, "_files", [])
        sel = archive_list.curselection()
        if not sel or not files:
            messagebox.showwarning("No archive selected", "Please select a JSON entry from the archive.")
            return
        json_path = files[sel[0]]
        launch_gui_in_same_root(root, proj["path"], json_path)

    def delete_selected_project():
        """Delete the selected project folder safely (ONLY from Projects list)."""
        sel = proj_list.curselection()
        if not sel:
            messagebox.showwarning("No project selected", "Please select a project to delete.")
            return

        proj = root.projects_home_state["projects"][sel[0]]
        proj_name = proj["name"]
        proj_path = os.path.abspath(proj["path"])
        projects_root = os.path.abspath(root.projects_home_state["projects_root"].get())

       
        try:
            if os.path.commonpath([proj_path, projects_root]) != projects_root:
                messagebox.showerror("Safety check failed", "Project path is outside the Projects Root. Aborting.")
                return
        except ValueError:
            messagebox.showerror("Safety check failed", "Invalid paths detected. Aborting.")
            return

        
        ok = messagebox.askyesno(
            "Delete Project",
            f"Delete the entire project '{proj_name}'?\n\n"
            f"This will remove the project folder and its archive permanently.",
            icon="warning",
            default="no",
        )
        if not ok:
            return

        
        try:
            shutil.rmtree(proj_path)
        except Exception as e:
            messagebox.showerror("Delete failed", f"Could not delete project:\n{e}")
            return

       
        rescan_projects()
        refresh_projects()
        messagebox.showinfo("Project deleted", f"'{proj_name}' was deleted.")

    
    proj_list.bind("<<ListboxSelect>>", on_project_select)                 
    archive_list.bind("<Double-Button-1>", lambda e: open_selected())     
    archive_list.bind("<Return>", lambda e: open_selected())               

    open_btn.configure(command=open_selected)
    delete_btn.configure(command=delete_selected_project, state="disabled")

    rescan_projects()
    refresh_projects()
    if owns_root:
        root.mainloop()

if __name__ == "__main__":
    main()

