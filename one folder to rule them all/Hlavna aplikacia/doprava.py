import tkinter as tk
from tkinter import StringVar

from helpers import parse_float, secure_load_json, secure_save_json

# In-memory doprava values for the current session
current_doprava = {}

DEFAULT_DOPRAVA = {
    "cena_vyjazd": "30.00",
    "pocet_vyjazdov": "0",
    "cena_km": "0.55",
    "vzdialenost": "0.0",
    "pocet_ciest": "0",
}


def _normalize_value(key: str, value) -> str:
    """Return doprava values stored as strings in a consistent format."""
    if key in ("pocet_vyjazdov", "pocet_ciest"):
        try:
            # Allow floats like "2.0" or "2,0" but store as integers
            num = int(parse_float(str(value)))
            return str(max(0, num))
        except Exception:
            return DEFAULT_DOPRAVA[key]
    if key in ("cena_vyjazd", "cena_km"):
        try:
            num = parse_float(str(value))
            return f"{num:.2f}"
        except Exception:
            return DEFAULT_DOPRAVA[key]
    if key == "vzdialenost":
        try:
            num = parse_float(str(value))
            text = f"{num:.2f}".rstrip("0").rstrip(".")
            return text or "0"
        except Exception:
            return DEFAULT_DOPRAVA[key]
    return str(value or "")


def normalize_doprava_data(data: dict | None) -> dict:
    """Ensure all doprava fields are present and sanitized as strings."""
    normalized = DEFAULT_DOPRAVA.copy()
    if not isinstance(data, dict):
        return normalized

    for key in DEFAULT_DOPRAVA:
        if key in data:
            normalized[key] = _normalize_value(key, data.get(key))
    return normalized


def save_doprava_data(d: dict):
    global current_doprava
    normalized = normalize_doprava_data(d)
    current_doprava.clear()
    current_doprava.update(normalized)
    print("DEBUG save_doprava_data loaded:", current_doprava)

def load_doprava_from_project(commit_file: str):
    """Load doprava dict from the project JSON (with defaults)."""
    data = secure_load_json(commit_file, default={})
    return normalize_doprava_data(data.get("doprava"))


def save_doprava_to_project(commit_file: str, doprava_dict: dict):
    """Save doprava dict into the project JSON."""
    data = secure_load_json(commit_file, default={})
    normalized = normalize_doprava_data(doprava_dict)
    data["doprava"] = normalized
    secure_save_json(commit_file, data)
    print(f"✅ Doprava uložená do {commit_file}")
    print("DEBUG doprava content:", normalized)


def load_doprava_tuple(commit_file: str):
    """Return doprava as a tuple for Excel export."""
    data = load_doprava_from_project(commit_file)
    try:
        cena_vyjazd = float(data.get("cena_vyjazd", 0))
        pocet_vyjazdov = int(data.get("pocet_vyjazdov", 0))
        cena_km = float(data.get("cena_km", 0))
        vzdialenost = float(data.get("vzdialenost", 0))
        pocet_ciest = int(data.get("pocet_ciest", 0))

        cena_ba = cena_vyjazd * pocet_vyjazdov
        cena_mimo = cena_km * vzdialenost * pocet_ciest
        return (cena_vyjazd, pocet_vyjazdov, cena_ba, cena_km, cena_mimo)
    except Exception:
        return None


def show_doprava_window(commit_file: str):
    """Open the Doprava window bound to a specific project JSON."""
    from ttkbootstrap import Button
    global current_doprava

    # Start with in-memory values if present, else load from file
    base_settings = current_doprava if current_doprava else load_doprava_from_project(commit_file)
    settings = normalize_doprava_data(base_settings)

    # Ensure in-memory snapshot reflects what we display to the user
    current_doprava.clear()
    current_doprava.update(settings)

    def compute_and_update(event=None):
        try:
            ba_total = float(cena_vyjazd_var.get()) * float(pocet_vyjazdov_var.get())
        except Exception:
            ba_total = 0.0
        try:
            mimo_total = (
                float(cena_km_var.get())
                * float(vzdialenost_var.get())
                * float(pocet_ciest_var.get())
            )
        except Exception:
            mimo_total = 0.0

        vysledok_ba_var.set(f"{ba_total:.2f} €")
        vysledok_mimo_var.set(f"{mimo_total:.2f} €")
        vysledok_spolu_var.set(f"{ba_total + mimo_total:.2f} €")

        update_session_data()  # keep memory in sync

    def collect_current_values():
        return {
            "cena_vyjazd": cena_vyjazd_var.get(),
            "pocet_vyjazdov": pocet_vyjazdov_var.get(),
            "cena_km": cena_km_var.get(),
            "vzdialenost": vzdialenost_var.get(),
            "pocet_ciest": pocet_ciest_var.get(),
        }

    def update_session_data():
        """Update the in-memory doprava values."""
        normalized = normalize_doprava_data(collect_current_values())
        current_doprava.clear()
        current_doprava.update(normalized)
        return normalized.copy()

    def bind_all(widget):
        widget.bind("<KeyRelease>", compute_and_update)
        widget.bind("<FocusOut>", compute_and_update)
        widget.bind("<ButtonRelease>", compute_and_update)

    def make_spin_row(parent, label_text, var, min_value=0, step=1):
        tk.Label(parent, text=label_text).pack(anchor="w")
        row = tk.Frame(parent)
        row.pack(fill="x", expand=True, pady=2)

        entry = tk.Entry(row, textvariable=var, justify="center")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        bind_all(entry)

        btn_frame = tk.Frame(row)
        btn_frame.pack(side="right")

        Button(btn_frame, text="−", bootstyle="warning",
               command=lambda: var.set(str(max(min_value, int(var.get() or "0") - step)))).pack(side="left", padx=1, ipadx=6, ipady=2)
        Button(btn_frame, text="+", bootstyle="warning",
               command=lambda: var.set(str(int(var.get() or "0") + step))).pack(side="left", padx=1, ipadx=6, ipady=2)

    win = tk.Toplevel()
    win.title("Výpočet dopravy")

    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    width = int(screen_width * 0.2)
    height = int(screen_height * 0.5)
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")
    win.minsize(300, 450)

    # Variables
    cena_vyjazd_var = StringVar(value=settings.get("cena_vyjazd", "30.00"))
    pocet_vyjazdov_var = StringVar(value=settings.get("pocet_vyjazdov", "0"))
    vysledok_ba_var = StringVar(value="0.00 €")

    cena_km_var = StringVar(value=settings.get("cena_km", "0.55"))
    vzdialenost_var = StringVar(value=settings.get("vzdialenost", "0.0"))
    pocet_ciest_var = StringVar(value=settings.get("pocet_ciest", "0"))
    vysledok_mimo_var = StringVar(value="0.00 €")

    vysledok_spolu_var = StringVar(value="0.00 €")

    for var in (cena_vyjazd_var, pocet_vyjazdov_var, cena_km_var, vzdialenost_var, pocet_ciest_var):
        var.trace_add("write", lambda *a: compute_and_update())

    # 🚗 BA section
    frame_ba = tk.LabelFrame(win, text="🚗 V Bratislave", padx=10, pady=10)
    frame_ba.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_ba, text="Cena za 1 výjazd (€):").pack(anchor="w")
    entry_cena = tk.Entry(frame_ba, textvariable=cena_vyjazd_var)
    entry_cena.pack(fill="x", expand=True)
    bind_all(entry_cena)

    make_spin_row(frame_ba, "Počet výjazdov:", pocet_vyjazdov_var, min_value=0, step=1)

    tk.Label(frame_ba, text="Celková cena (BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_ba, textvariable=vysledok_ba_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # 🚐 Mimo BA section
    frame_mimo = tk.LabelFrame(win, text="🚐 Mimo Bratislavu", padx=10, pady=10)
    frame_mimo.pack(fill="x", padx=10, pady=(5, 5))

    tk.Label(frame_mimo, text="Cena za 1 km (€):").pack(anchor="w")
    entry_km = tk.Entry(frame_mimo, textvariable=cena_km_var)
    entry_km.pack(fill="x", expand=True)
    bind_all(entry_km)

    make_spin_row(frame_mimo, "Vzdialenosť (km):", vzdialenost_var, min_value=0, step=1)
    make_spin_row(frame_mimo, "Počet ciest (tam a späť):", pocet_ciest_var, min_value=0, step=1)

    tk.Label(frame_mimo, text="Celková cena (mimo BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_mimo, textvariable=vysledok_mimo_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # 💰 Together
    frame_spolu = tk.LabelFrame(win, text="💰 Spolu doprava", padx=10, pady=10)
    frame_spolu.pack(fill="x", padx=10, pady=(5, 10))

    tk.Label(frame_spolu, text="Celková suma:").pack(anchor="w")
    tk.Label(frame_spolu, textvariable=vysledok_spolu_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")

    # 💾 Save button → now only closes the window
    def persist_and_close():
        values = update_session_data()
        save_doprava_to_project(commit_file, values)
        win.destroy()

    Button(win, text="💾 Uložiť dopravu", bootstyle="success",
           command=persist_and_close).pack(pady=10, ipadx=10, ipady=5)

    compute_and_update()

    def on_close():
        update_session_data()  # keep memory updated
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)
