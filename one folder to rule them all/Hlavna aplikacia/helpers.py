# Consolidated helper functions and widgets
import os
import sys
import json
import shutil
import base64
import ctypes
from ctypes import wintypes
from typing import Any
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
from datetime import datetime
import ctypes
from ttkbootstrap import Button


# ---------------------------------------------------------------------------
# App/resource paths and config bootstrap (PyInstaller-friendly)
# ---------------------------------------------------------------------------
get_praca_data_func = None
def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> str:
    """Writable directory for app data (next to EXE when frozen)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resources_dir() -> str:
    """Bundled resources dir (resources/ inside _MEIPASS when frozen)."""
    base = sys._MEIPASS if is_frozen() else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources")

def resource_path(rel_path: str) -> str:
    """Full path to a resource in the bundled resources directory."""
    return os.path.join(resources_dir(), rel_path)


def ensure_writable_config(filename: str, default_content: dict | None = None) -> str:
    """Ensure a writable copy of a config JSON exists next to the EXE.

    - If `<app_dir>/<filename>` doesn't exist, copy default from resources
      (`resources/<filename>`) when available, otherwise write `default_content`
      (or `{}` if not provided).
    - Returns the full writable path.
    """
    dest = os.path.join(app_dir(), filename)
    if not os.path.exists(dest):
        os.makedirs(app_dir(), exist_ok=True)
        src = resource_path(filename)
        if os.path.exists(src):
            try:
                shutil.copyfile(src, dest)
            except Exception:
                pass
        if not os.path.exists(dest):
            try:
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(default_content or {}, f, ensure_ascii=False, indent=2)
            except Exception:
                # last resort: create empty file
                try:
                    open(dest, "a").close()
                except Exception:
                    pass
    return dest


# ---------------------------------------------------------------------------
# AppData/Roaming config with defaults from resources
# ---------------------------------------------------------------------------
def user_config_dir(app_name: str = "LastMile") -> str:
    """Return a per-user config directory, preferring AppData/Roaming on Windows."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
        return os.path.join(base, app_name)
    # Cross-platform fallback: ~/.config/<app_name>
    return os.path.join(os.path.expanduser("~/.config"), app_name)


def ensure_user_config(filename: str, default_content: dict | None = None, app_name: str = "LastMile") -> str:
    """Ensure a writable JSON config exists under the user config dir.

    If missing, copy a bundled default from resources/<filename> when present,
    otherwise write default_content or empty JSON.
    Returns the absolute path to the config file.
    """
    cfg_dir = user_config_dir(app_name)
    os.makedirs(cfg_dir, exist_ok=True)
    dest = os.path.join(cfg_dir, filename)
    if not os.path.exists(dest):
        src = resource_path(filename)
        if os.path.exists(src):
            try:
                shutil.copyfile(src, dest)
            except Exception:
                pass
        if not os.path.exists(dest):
            try:
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(default_content or {}, f, ensure_ascii=False, indent=2)
            except Exception:
                try:
                    open(dest, "a").close()
                except Exception:
                    pass
    return dest


# ---------------------------------------------------------------------------
# Lightweight per-user protection for secrets (Windows DPAPI when available)
# ---------------------------------------------------------------------------

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _bytes_to_blob(b: bytes):
    if not isinstance(b, (bytes, bytearray)):
        b = (b or b"")
    buf = ctypes.create_string_buffer(b, len(b))
    blob = DATA_BLOB()
    blob.cbData = len(b)
    blob.pbData = ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))
    return blob, buf  # keep buf alive


def _blob_to_bytes(blob: DATA_BLOB) -> bytes:
    return ctypes.string_at(blob.pbData, blob.cbData)


def _local_free(ptr) -> None:
    try:
        ctypes.windll.kernel32.LocalFree(ptr)
    except Exception:
        pass


def dpapi_protect(data: bytes) -> bytes:
    """Protect bytes with Windows DPAPI for current user. Fallback: base64."""
    if os.name == "nt":
        try:
            crypt32 = ctypes.windll.crypt32
            in_blob, _buf = _bytes_to_blob(data)
            out_blob = DATA_BLOB()
            if crypt32.CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                try:
                    return _blob_to_bytes(out_blob)
                finally:
                    _local_free(out_blob.pbData)
        except Exception:
            pass
    # Fallback obfuscation
    return base64.b64encode(data)


def dpapi_unprotect(data: bytes) -> bytes:
    if os.name == "nt":
        try:
            crypt32 = ctypes.windll.crypt32
            in_blob, _buf = _bytes_to_blob(data)
            out_blob = DATA_BLOB()
            if crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                try:
                    return _blob_to_bytes(out_blob)
                finally:
                    _local_free(out_blob.pbData)
        except Exception:
            pass
    # Fallback obfuscation reverse
    try:
        return base64.b64decode(data)
    except Exception:
        return b""


def encrypt_string_for_user(text: str) -> str:
    raw = text.encode("utf-8") if isinstance(text, str) else b""
    enc = dpapi_protect(raw)
    return "enc:" + base64.b64encode(enc).decode("ascii")


def decrypt_string_if_encrypted(value: str) -> str:
    if isinstance(value, str) and value.startswith("enc:"):
        try:
            blob = base64.b64decode(value[4:].encode("ascii"))
            plain = dpapi_unprotect(blob)
            return plain.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return value if isinstance(value, str) else ""


# ---------------------------------------------------------------------------
# Encrypted JSON helpers (file-level encryption for all settings)
# ---------------------------------------------------------------------------

_SECURE_MAGIC = b"ENC1:"

# ---------------------------------------------------------------------------
# High-DPI helpers (consistent font/scaling when packaged)
# ---------------------------------------------------------------------------

def enable_high_dpi_awareness() -> None:
    """Enable per-monitor DPI awareness on Windows so Tk can scale correctly.

    Safe to call multiple times and on non-Windows platforms (no-op).
    """
    try:
        if os.name != "nt":
            return
        try:
            # Windows 8.1+ (per-monitor aware)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass
        try:
            # Windows Vista/7 fallback (system DPI aware)
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    except Exception:
        pass



def calibrate_tk_scaling(root: tk.Misc, min_scale: float = 1.0, max_scale: float = 2.5) -> float:
    """Return the scaling factor using Windows API if available.
    Special-case 200% DPI to reduce oversizing.
    """
    try:
        enable_high_dpi_awareness()
    except Exception:
        pass

    scale = 1.0
    try:
        if os.name == "nt":
            dpi = ctypes.windll.user32.GetDpiForSystem()
            scale = dpi / 96.0
        else:
            scale = float(root.winfo_fpixels("1i")) / 72.0
    except Exception:
        try:
            scale = float(root.winfo_fpixels("1i")) / 96.0
        except Exception:
            scale = 1.0

    # ✅ Option A: tweak the extremes
    if abs(scale - 2.0) < 0.05:       # 200% DPI → shrink a bit
        scale = 1.65
    elif abs(scale - 1.0) < 0.05:     # 100% DPI → give a small boost
        scale = 1.1
    elif abs(scale - 1.75) < 0.05:     # 100% DPI → give a small boost
        scale = 1.5
    elif abs(scale - 1.25) < 0.05:     # 100% DPI → give a small boost
        scale = 1.3

    # Clamp to safe range
    scale = max(min_scale, min(scale, max_scale))

    try:
        root.tk.call("tk", "scaling", float(scale))
    except Exception:
        pass

    return float(scale)



def apply_global_scaling(root, style, scale: float):
    base_font_size = int(11 * scale)

    # Apply to all ttk widgets
    apply_ttk_base_font(style, family="Segoe UI", size=base_font_size)
    root.option_add("*Font", ("Segoe UI", base_font_size))

    # Update button paddings
    pad = (int(10 * scale), int(6 * scale))
    for btn_style in (
        "TButton", "secondary.TButton", "success.TButton",
        "danger.TButton", "info.TButton"
    ):
        try:
            style.configure(btn_style, padding=pad)
        except Exception:
            pass

    # Scale Treeview row heights and fonts
    table_font_size = int(11 * scale)
    row_h = int(2.4 * table_font_size)
    style.configure("Main.Treeview", rowheight=row_h, font=("Segoe UI", table_font_size))
    basket_font_size = table_font_size
    basket_row_h = row_h
    if scale >= 1.6:  # only enlarge on 200% DPI laptops
        basket_font_size += 10
        basket_row_h += int(0.2 * table_font_size)
    style.configure("Basket.Treeview", rowheight=basket_row_h, font=("Segoe UI", basket_font_size))



class DebugMenu(tk.Toplevel):
    def __init__(self, master, settings):
        super().__init__(master)
        self.title("Debug Menu")
        self.settings = settings
        self.vars = {}

        row = 0
        for key, value in settings.items():
            tk.Label(self, text=key).grid(row=row, column=0, sticky="w")
            var = tk.DoubleVar(value=value)
            self.vars[key] = var
            tk.Scale(self, from_=0, to=5, resolution=0.1,
                     orient="horizontal", variable=var).grid(row=row, column=1, sticky="ew")
            row += 1

        self.columnconfigure(1, weight=1)

    def get_settings(self):
        return {k: v.get() for k, v in self.vars.items()}


def open_debug_menu(root, settings):
    """Open the debug menu (F12)."""
    DebugMenu(root, settings)




def apply_ttk_base_font(style: ttk.Style, *, family: str = "Segoe UI", size: int = 10) -> None:
    """Apply a base font to common ttk widgets, but do NOT change buttons.

    - Intentionally skips all `TButton` variants so top bars don't grow when
      changing table/font settings.
    - Applies to labels/entries/checkbuttons/radiobuttons/treeviews.
    - Updates Tk named default fonts to keep classic widgets in sync.
    """
    try:
        # Do NOT set the global '.' font, because many themes let buttons inherit
        # from it. Instead, set specific non-button classes.
        for cls in ("TLabel", "TEntry", "TCheckbutton", "TRadiobutton", "Treeview"):
            try:
                style.configure(cls, font=(family, size))
            except Exception:
                pass
        # Update Tk named fonts so non-ttk widgets also follow the size
        try:
            # Avoid changing TkDefaultFont because many ttk buttons inherit it.
            for name in ("TkTextFont", "TkHeadingFont", "TkMenuFont", "TkSmallCaptionFont"):
                try:
                    nf = tkfont.nametofont(name)
                    nf.configure(family=family, size=size)
                except Exception:
                    pass
        except Exception:
            pass
    except Exception:
        pass


def secure_save_json(path: str, data: dict) -> None:
    """Save dict as encrypted JSON using Windows DPAPI (base64-wrapped).

    File format: b'ENC1:' + base64(DPAPI(encrypted_bytes))
    """
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    except Exception:
        pass
    try:
        plain = json.dumps(data or {}, ensure_ascii=False, indent=2).encode("utf-8")
    except Exception:
        # Fallback to compact dump if non-serializable default shows up
        plain = json.dumps(data or {}, ensure_ascii=False).encode("utf-8")
    enc = dpapi_protect(plain)
    b64 = base64.b64encode(enc)
    try:
        with open(path, "wb") as f:
            f.write(_SECURE_MAGIC + b64)
    except Exception:
        # As last resort, write plain to reduce data loss (not preferred)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(data or {}, ensure_ascii=False, indent=2))
        except Exception:
            pass


def secure_load_json(path: str, default: dict | None = None) -> dict:
    """Load encrypted JSON; transparently migrate plain JSON to encrypted.

    - If file starts with ENC1:, decrypt and parse JSON.
    - If plain JSON, parse it and re-save in encrypted form.
    - If missing or error, return default or {}.
    """
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        return dict(default or {})
    except Exception:
        return dict(default or {})

    try:
        if raw.startswith(_SECURE_MAGIC):
            b64 = raw[len(_SECURE_MAGIC):]
            enc = base64.b64decode(b64)
            plain = dpapi_unprotect(enc)
            return json.loads(plain.decode("utf-8", errors="ignore"))
        else:
            # Plain JSON; migrate to encrypted
            text = raw.decode("utf-8", errors="ignore")
            data = json.loads(text)
            try:
                secure_save_json(path, data)
            except Exception:
                pass
            return data
    except Exception:
        return dict(default or {})


def secure_load_config(filename: str, default_content: dict | None = None, app_name: str = "LastMile") -> dict:
    """Ensure a user config file exists and load it (encrypted)."""
    path = ensure_user_config(filename, default_content=default_content, app_name=app_name)
    return secure_load_json(path, default=default_content or {})


def secure_save_config(filename: str, data: dict, app_name: str = "LastMile") -> None:
    """Save an encrypted user config file."""
    path = ensure_user_config(filename, app_name=app_name)
    secure_save_json(path, data or {})


def parse_float(text: str) -> float:
    """Parse a float allowing comma as decimal separator."""
    return float(text.replace(",", ".").strip())


def askfloat_locale(title, prompt, **kwargs):
    """Prompt user for a float, accepting comma decimal separator."""
    while True:
        # Pass only supported options to askstring to avoid Tkinter's numeric
        # validation which expects a float.  We perform our own validation
        # below, so remove options like ``minvalue`` or ``maxvalue`` that would
        # otherwise trigger ``_QueryDialog`` to compare a string with a float
        # and raise a ``TypeError``.
        dialog_kwargs = {
            k: v for k, v in kwargs.items()
            if k in ("parent", "initialvalue", "show")
        }
        value = tk.simpledialog.askstring(title, prompt, **dialog_kwargs)
        if value is None:
            return None
        try:
            num = parse_float(value)
        except ValueError:
            messagebox.showerror("Chyba", "Neplatné číslo.", parent=kwargs.get("parent"))
            continue
        minv = kwargs.get("minvalue")
        maxv = kwargs.get("maxvalue")
        if minv is not None and num < minv:
            messagebox.showerror("Chyba", f"Hodnota musí byť aspoň {minv}.", parent=kwargs.get("parent"))
            continue
        if maxv is not None and num > maxv:
            messagebox.showerror("Chyba", f"Hodnota musí byť najviac {maxv}.", parent=kwargs.get("parent"))
            continue
        return num


def format_currency(value: float) -> str:
    """Return the value formatted with space thousand separators and a trailing
    euro sign."""
    return f"{value:,.2f}".replace(",", " ") + " €"



# ---------------------------------------------------------------------------
# Filter panel UI (responsive width)
# ---------------------------------------------------------------------------
def create_filter_panel(parent, on_mousewheel_callback):
    """Create a horizontally scrollable filter panel with responsive width.

    The container no longer forces a fixed width; it expands/shrinks based on
    its grid column weight configured by the caller (gui.py).
    """
    filter_container = tk.Frame(parent, bg="white")


    canvas = tk.Canvas(filter_container, bg="white", highlightthickness=0)
    h_scrollbar = tk.Scrollbar(filter_container, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=h_scrollbar.set)

    filter_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=filter_frame, anchor="nw")

    canvas.pack(fill=tk.BOTH, expand=True)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_enter(event):
        # Only capture on the filter widgets themselves
        canvas.bind("<MouseWheel>", _on_mousewheel)
        filter_frame.bind("<MouseWheel>", _on_mousewheel)

    def _on_leave(event):
        # Release when the pointer leaves the filter
        canvas.unbind("<MouseWheel>")
        filter_frame.unbind("<MouseWheel>")
    def _on_mousewheel(event):
        # Scroll horizontally when Shift is held; otherwise swallow to avoid janky background scrolling
        if event.state & 0x0001:
            try:
                units = int(-1 * (event.delta / 120))
            except Exception:
                units = -1
            canvas.xview_scroll(units, "units")
        return "break"

    filter_frame.bind("<Enter>", _on_enter)
    filter_frame.bind("<Leave>", _on_leave)
    filter_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    category_vars = {}
    table_vars = {}

    def setup_category_tree(category_structure):
        tk.Label(filter_frame, text="Prehliadač databázových tabuliek", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", padx=5, pady=5)

        def toggle_category(category, children_frame, classes):
            def handler(*args):
                show = category_vars[category].get()
                children_frame.pack_forget()
                for class_id, _ in classes:
                    table_vars[class_id].set(False)
                if show:
                    children_frame.pack(anchor="w", fill="x", padx=20)
                on_mousewheel_callback()
            return handler

        for category, classes in category_structure.items():
            category_vars[category] = tk.BooleanVar(value=False)
            outer_frame = tk.Frame(filter_frame, bg="white")
            outer_frame.pack(anchor="w", fill="x", padx=5, pady=2)

            children_frame = tk.Frame(outer_frame, bg="white")
            cat_checkbox = ttk.Checkbutton(outer_frame, text=category, variable=category_vars[category])
            cat_checkbox.pack(anchor="w")
            category_vars[category].trace_add("write", toggle_category(category, children_frame, classes))

            for class_id, table_name in classes:
                table_vars[class_id] = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(children_frame, text=table_name, variable=table_vars[class_id], command=on_mousewheel_callback, bg="white")
                chk.pack(anchor="w", pady=1)

        tk.Button(filter_frame, text="Resetovať filtre", command=lambda: reset_filters()).pack(anchor="w", pady=10, padx=5)

    def reset_filters():
        for var in table_vars.values():
            var.set(False)
        for var in category_vars.values():
            var.set(False)
        on_mousewheel_callback()

    return filter_container, filter_frame, setup_category_tree, category_vars, table_vars


# ---------------------------------------------------------------------------
# Notes panel UI (from notes_panel.py)
# ---------------------------------------------------------------------------
def create_notes_panel(parent, project_name, json_path):
    """Create a simple note-taking panel bound to a JSON file."""
    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    tk.Label(frame, text="Poznámky:", font=("Arial", 10)).pack(anchor="w")
    text_widget = tk.Text(frame, height=6, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True)

    def save_notes():
        data = {}
        if os.path.exists(json_path):
            try:
                data = secure_load_json(json_path, default={})
            except Exception:
                data = {}

        text = text_widget.get("1.0", tk.END).strip()
        data["notes_text"] = text

        history = data.get("history", [])
        history.append({
            "timestamp": datetime.now().isoformat(),
            "notes_text": text,
        })
        data["history"] = history

        secure_save_json(json_path, data)
        print(f"📝 Notes saved to {json_path}")

    def on_text_change(event):
        text_widget.edit_modified(False)

    text_widget.bind("<<Modified>>", on_text_change)

    if os.path.exists(json_path):
        try:
            data = secure_load_json(json_path, default={})
            text_widget.insert("1.0", data.get("notes_text", ""))
            text_widget.edit_modified(False)
        except Exception:
            pass

    return frame


# ---------------------------------------------------------------------------
# Work estimation window (from praca.py)
# ---------------------------------------------------------------------------
def show_praca_window(cursor, commit_file):
    from tkinter import messagebox
    from ttkbootstrap import Button
    import praca

    cursor.execute("SELECT id, rola, plat_za_hodinu FROM pracovnik_roly LIMIT 4")
    roles = cursor.fetchall()

    praca_window = tk.Toplevel()
    praca_window.title("🛠️ Odhad pracovnej činnosti")

    screen_width = praca_window.winfo_screenwidth()
    screen_height = praca_window.winfo_screenheight()
    width = int(screen_width * 0.6)
    height = int(screen_height * 0.3)
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    praca_window.geometry(f"{width}x{height}+{x}+{y}")
    praca_window.configure(bg="#f9f9f9")
    praca_window.minsize(800, 400)

    base_rows = praca.current_praca or praca.load_praca_from_project(commit_file)
    base_rows = praca.normalize_praca_data(base_rows)

    entries: list[dict[str, Any]] = []

    def get_praca_data():
        data: list[dict[str, Any]] = []
        for row in entries:
            pay_editable = row.get("pay_editable", True)
            plat = (
                row["plat_var"].get()
                if pay_editable
                else row["plat_label"].cget("text")
            )
            data.append(
                {
                    "rola": row["rola_var"].get(),
                    "osoby": row["osoby_var"].get(),
                    "hodiny": row["hodiny_var"].get(),
                    "plat": plat,
                    "spolu": row["spolu_label"].cget("text"),
                    "koeficient": row["koef_var"].get(),
                    "predaj": row["predaj_var"].get(),
                    "pay_editable": pay_editable,
                    "role_id": row.get("role_id", ""),
                }
            )
        return data

    praca_nakup_var = tk.StringVar(value="0.00")
    praca_predaj_var = tk.StringVar(value="0.00")
    praca_marza_var = tk.StringVar(value="0.00")

    def update_session_snapshot():
        snapshot = praca.save_praca_data(get_praca_data())
        return snapshot

    def recalculate():
        nakup_sum = 0.0
        predaj_sum = 0.0
        for row in entries:
            try:
                osoby = int(row["osoby_var"].get())
                hodiny = int(row["hodiny_var"].get())
                if row.get("pay_editable", True):
                    plat = parse_float(row["plat_var"].get())
                else:
                    plat = parse_float(row["plat_label"].cget("text"))
                koef = parse_float(row["koef_var"].get())
                spolu = osoby * hodiny * plat
                predaj = spolu * koef
                row["spolu_label"].config(text=f"{spolu:.2f}")
                row["predaj_var"].set(f"{predaj:.2f}")
                nakup_sum += spolu
                predaj_sum += predaj
            except Exception:
                continue
        praca_nakup_var.set(f"{nakup_sum:.2f}")
        praca_predaj_var.set(f"{predaj_sum:.2f}")
        praca_marza_var.set(f"{predaj_sum - nakup_sum:.2f}")
        update_session_snapshot()

    def change_int(var, delta, minimum=0):
        try:
            val = int(var.get()) + delta
            if val < minimum:
                val = minimum
            var.set(str(val))
        except Exception:
            var.set(str(minimum))

    def change_float(var, delta, minimum=0.1):
        try:
            val = parse_float(var.get()) + delta
            if val < minimum:
                val = minimum
            var.set(f"{val:.1f}")
        except Exception:
            var.set(f"{minimum:.1f}")

    def adjust_column(field, delta, is_float=False, minimum=0.1):
        for row in entries:
            var = row.get(field)
            if var:
                if is_float:
                    change_float(var, delta, minimum)
                else:
                    change_int(var, delta, minimum)

    def add_row(
        role_id=None,
        rola="",
        plat="0.00",
        osoby="1",
        hodiny="8",
        koef="1.0",
        predaj="0.00",
        pay_editable=None,
    ):
        row: dict[str, Any] = {}
        idx = len(entries) + 1

        row["role_id"] = "" if role_id is None else str(role_id)
        row["pay_editable"] = True if pay_editable is None else bool(pay_editable)

        row["rola_var"] = tk.StringVar(value=str(rola))
        tk.Entry(
            table_frame,
            textvariable=row["rola_var"],
            justify="center",
        ).grid(row=idx, column=0, padx=6, pady=4, sticky="nsew")

        row["osoby_var"] = tk.StringVar(value=str(osoby))
        Button(
            table_frame,
            text="−",
            bootstyle="warning",
            command=lambda: change_int(row["osoby_var"], -1, 1),
        ).grid(row=idx, column=1, sticky="nsew", padx=2, pady=(6, 2))
        tk.Entry(
            table_frame,
            textvariable=row["osoby_var"],
            justify="center",
        ).grid(row=idx, column=2, sticky="nsew", padx=2)
        Button(
            table_frame,
            text="+",
            bootstyle="warning",
            command=lambda: change_int(row["osoby_var"], 1),
        ).grid(row=idx, column=3, sticky="nsew", padx=2, pady=(6, 2))

        row["hodiny_var"] = tk.StringVar(value=str(hodiny))
        Button(
            table_frame,
            text="−",
            bootstyle="warning",
            command=lambda: change_int(row["hodiny_var"], -2, 0),
        ).grid(row=idx, column=4, sticky="nsew", padx=2, pady=(6, 2))
        tk.Entry(
            table_frame,
            textvariable=row["hodiny_var"],
            justify="center",
        ).grid(row=idx, column=5, sticky="nsew", padx=2)
        Button(
            table_frame,
            text="+",
            bootstyle="warning",
            command=lambda: change_int(row["hodiny_var"], 2),
        ).grid(row=idx, column=6, sticky="nsew", padx=2, pady=(6, 2))

        plat_value = str(plat)
        if not row["pay_editable"]:
            try:
                plat_value = f"{parse_float(plat_value):.2f}"
            except Exception:
                plat_value = "0.00"
            row["plat_label"] = tk.Label(
                table_frame,
                text=plat_value,
                relief="groove",
                anchor="center",
                bg="#ffffff",
            )
            row["plat_label"].grid(row=idx, column=7, sticky="nsew", padx=2)
        else:
            try:
                plat_value = f"{parse_float(plat_value):.2f}"
            except Exception:
                plat_value = "0.00"
            row["plat_var"] = tk.StringVar(value=plat_value)
            entry = tk.Entry(
                table_frame,
                textvariable=row["plat_var"],
                justify="center",
                width=10,
            )
            entry.grid(row=idx, column=7, sticky="nsew", padx=2)

        row["spolu_label"] = tk.Label(
            table_frame,
            text="0.00",
            relief="sunken",
            anchor="center",
            bg="#f0f0f0",
        )
        row["spolu_label"].grid(row=idx, column=8, sticky="nsew", padx=2)

        row["koef_var"] = tk.StringVar(value=str(koef))
        Button(
            table_frame,
            text="−",
            bootstyle="warning",
            command=lambda: change_float(row["koef_var"], -0.1, 0.1),
        ).grid(row=idx, column=9, sticky="nsew", padx=2, pady=(6, 2))
        tk.Entry(
            table_frame,
            textvariable=row["koef_var"],
            justify="center",
        ).grid(row=idx, column=10, sticky="nsew", padx=2)
        Button(
            table_frame,
            text="+",
            bootstyle="warning",
            command=lambda: change_float(row["koef_var"], 0.1),
        ).grid(row=idx, column=11, sticky="nsew", padx=2, pady=(6, 2))

        row["predaj_var"] = tk.StringVar(value=str(predaj))
        tk.Entry(
            table_frame,
            textvariable=row["predaj_var"],
            justify="center",
        ).grid(row=idx, column=12, sticky="nsew", padx=2)

        row["del_btn"] = Button(
            table_frame,
            text="✖",
            bootstyle="danger",
            command=lambda r=row: remove_specific_row(r),
        )
        row["del_btn"].grid(row=idx, column=13, sticky="nsew", padx=2, pady=(6, 2))

        entries.append(row)
        recalculate()

        row["osoby_var"].trace_add("write", lambda *args: recalculate())
        row["hodiny_var"].trace_add("write", lambda *args: recalculate())
        row["koef_var"].trace_add("write", lambda *args: recalculate())
        if row.get("pay_editable", True):
            row["plat_var"].trace_add("write", lambda *args: recalculate())

    def _remove_row_at(index: int):
        if len(entries) <= 1:
            messagebox.showwarning("Upozornenie", "Musí zostať aspoň jedna rola.")
            return
        entries.pop(index)
        for widget in table_frame.grid_slaves():
            row_num = int(widget.grid_info()["row"])
            if row_num == index + 1:
                widget.destroy()
            elif row_num > index + 1:
                widget.grid_configure(row=row_num - 1)
        recalculate()

    def remove_row():
        _remove_row_at(len(entries) - 1)

    def remove_specific_row(row_dict):
        if row_dict in entries:
            idx = entries.index(row_dict)
            _remove_row_at(idx)

    top_frame = tk.Frame(praca_window, bg="#e9f0fb")
    top_frame.pack(fill="x", padx=15, pady=10)

    Button(
        top_frame,
        text="➕ Pridať",
        bootstyle="success",
        width=12,
        command=lambda: add_row(rola="Nová rola", plat="0.00"),
    ).pack(side="left", padx=10)
    Button(
        top_frame,
        text="❌ Odstrániť",
        bootstyle="danger",
        width=12,
        command=remove_row,
    ).pack(side="left", padx=10)

    def persist_and_close():
        snapshot = update_session_snapshot()
        praca.save_praca_to_project(commit_file, snapshot)
        praca_window.destroy()

    Button(
        top_frame,
        text="💾 Uložiť",
        bootstyle="info",
        width=12,
        command=persist_and_close,
    ).pack(side="left", padx=10)

    global table_frame
    table_frame = tk.Frame(praca_window, bg="#f2f2f2", bd=2, relief="ridge")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    headers = [
        ("Rola", 20),
        ("−", 2), ("Osoby", 5), ("+", 2),
        ("−", 2), ("Hodiny", 5), ("+", 2),
        ("Plat €/h", 9),
        ("Spolu", 9),
        ("−", 2), ("Koef.", 5), ("+", 2),
        ("Predaj", 9),
    ]

    for i, (text, width) in enumerate(headers):
        label = tk.Label(
            table_frame,
            text=text,
            font=("Segoe UI", 9, "bold"),
            width=width,
            bg="#cfe2ff",
            relief="ridge",
            justify="center",
            pady=5,
        )
        label.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
        table_frame.grid_columnconfigure(i, weight=1)

        if text == "−" and i in (1, 4, 9):
            field = "osoby_var" if i == 1 else "hodiny_var" if i == 4 else "koef_var"
            is_float = i == 9
            label.bind(
                "<Button-1>",
                lambda e, f=field, fl=is_float: adjust_column(
                    f, -1 if not fl else -0.1, fl
                ),
            )
        elif text == "+" and i in (3, 6, 11):
            field = "osoby_var" if i == 3 else "hodiny_var" if i == 6 else "koef_var"
            is_float = i == 11
            label.bind(
                "<Button-1>",
                lambda e, f=field, fl=is_float: adjust_column(
                    f, 1 if not fl else 0.1, fl
                ),
            )

    if base_rows:
        for row in base_rows:
            add_row(
                role_id=row.get("role_id") or None,
                rola=row.get("rola", ""),
                plat=row.get("plat", "0.00"),
                osoby=row.get("osoby", "1"),
                hodiny=row.get("hodiny", "8"),
                koef=row.get("koeficient", "1.0"),
                predaj=row.get("predaj", "0.00"),
                pay_editable=row.get("pay_editable", True),
            )
    else:
        if roles:
            for role_id, rola, plat in roles:
                add_row(
                    role_id=role_id,
                    rola=rola,
                    plat=f"{plat:.2f}",
                    pay_editable=False,
                )
        else:
            add_row(rola="Nová rola", plat="0.00")

    summary_frame = tk.Frame(praca_window, bg="#e9f0fb")
    summary_frame.pack(fill="x", padx=15, pady=(0, 15))

    tk.Label(
        summary_frame,
        text="Práca nákup:",
        font=("Segoe UI", 10),
        bg="#e9f0fb",
    ).pack(side="left", padx=(0, 5))
    tk.Label(
        summary_frame,
        textvariable=praca_nakup_var,
        font=("Segoe UI", 10, "bold"),
        bg="#e9f0fb",
    ).pack(side="left", padx=(0, 20))

    tk.Label(
        summary_frame,
        text="Práca marža:",
        font=("Segoe UI", 10),
        bg="#e9f0fb",
    ).pack(side="left", padx=(0, 5))
    tk.Label(
        summary_frame,
        textvariable=praca_marza_var,
        font=("Segoe UI", 10, "bold"),
        bg="#e9f0fb",
    ).pack(side="left", padx=(0, 20))

    tk.Label(
        summary_frame,
        text="Práca predaj:",
        font=("Segoe UI", 10),
        bg="#e9f0fb",
    ).pack(side="left", padx=(0, 5))
    tk.Label(
        summary_frame,
        textvariable=praca_predaj_var,
        font=("Segoe UI", 10, "bold"),
        bg="#e9f0fb",
    ).pack(side="left", padx=(0, 20))

    def on_close():
        snapshot = update_session_snapshot()
        praca.save_praca_to_project(commit_file, snapshot)
        praca_window.destroy()

    praca_window.protocol("WM_DELETE_WINDOW", on_close)
