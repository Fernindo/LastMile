import tkinter as tk
from tkinter import StringVar
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "doprava_settings.json")


def _load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Chyba pri ukladaní nastavení dopravy: {e}")


def show_doprava_window():
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

    def bind_all(widget):
        widget.bind("<KeyRelease>", compute_and_update)
        widget.bind("<FocusOut>", compute_and_update)
        widget.bind("<ButtonRelease>", compute_and_update)

    win = tk.Toplevel()
    win.title("Výpočet dopravy")

    # Dynamická veľkosť okna podľa rozlíšenia obrazovky
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    width = int(screen_width * 0.2)
    height = int(screen_height * 0.55)
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")
    win.minsize(300, 400)  # minimálna veľkosť, ak by sa zmenšovalo

    # --- Load saved values or use defaults
    settings = _load_settings()

    cena_vyjazd_var = StringVar(value=settings.get("cena_vyjazd", "30.00"))
    pocet_vyjazdov_var = StringVar(value=settings.get("pocet_vyjazdov", "0"))
    vysledok_ba_var = StringVar(value="0.00 €")

    cena_km_var = StringVar(value=settings.get("cena_km", "0.55"))
    vzdialenost_var = StringVar(value=settings.get("vzdialenost", "0.0"))
    pocet_ciest_var = StringVar(value=settings.get("pocet_ciest", "0"))
    vysledok_mimo_var = StringVar(value="0.00 €")

    vysledok_spolu_var = StringVar(value="0.00 €")

    for var in (
        cena_vyjazd_var,
        pocet_vyjazdov_var,
        cena_km_var,
        vzdialenost_var,
        pocet_ciest_var,
    ):
        var.trace_add("write", lambda *a: compute_and_update())

    # --- Bratislava sekcia
    frame_ba = tk.LabelFrame(win, text="🚗 V Bratislave", padx=10, pady=10)
    frame_ba.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_ba, text="Cena za 1 výjazd (€):").pack(anchor="w")
    entry_cena = tk.Entry(frame_ba, textvariable=cena_vyjazd_var)
    entry_cena.pack(fill="x", expand=True)
    bind_all(entry_cena)

    tk.Label(frame_ba, text="Počet výjazdov:").pack(anchor="w")
    spin_vyjazdy = tk.Spinbox(
        frame_ba,
        from_=0,
        to=100,
        increment=1,
        textvariable=pocet_vyjazdov_var,
        command=compute_and_update,
    )
    spin_vyjazdy.pack(fill="x", expand=True)
    bind_all(spin_vyjazdy)

    tk.Label(frame_ba, text="Celková cena (BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_ba, textvariable=vysledok_ba_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- mimo BA sekcia
    frame_mimo = tk.LabelFrame(win, text="🚐 Mimo Bratislavu", padx=10, pady=10)
    frame_mimo.pack(fill="x", padx=10, pady=(5, 5))

    tk.Label(frame_mimo, text="Cena za 1 km (€):").pack(anchor="w")
    entry_km = tk.Entry(frame_mimo, textvariable=cena_km_var)
    entry_km.pack(fill="x", expand=True)
    bind_all(entry_km)

    tk.Label(frame_mimo, text="Vzdialenosť (km):").pack(anchor="w")
    spin_km = tk.Spinbox(
        frame_mimo,
        from_=0,
        to=1000,
        increment=1,
        textvariable=vzdialenost_var,
        command=compute_and_update,
    )
    spin_km.pack(fill="x", expand=True)
    bind_all(spin_km)

    tk.Label(frame_mimo, text="Počet ciest (tam a späť):").pack(anchor="w")
    spin_cesty = tk.Spinbox(
        frame_mimo,
        from_=0,
        to=100,
        increment=1,
        textvariable=pocet_ciest_var,
        command=compute_and_update,
    )
    spin_cesty.pack(fill="x", expand=True)
    bind_all(spin_cesty)

    tk.Label(frame_mimo, text="Celková cena (mimo BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_mimo, textvariable=vysledok_mimo_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- Spolu sekcia
    frame_spolu = tk.LabelFrame(win, text="💰 Spolu doprava", padx=10, pady=10)
    frame_spolu.pack(fill="x", padx=10, pady=(5, 10))

    tk.Label(frame_spolu, text="Celková suma:").pack(anchor="w")
    tk.Label(frame_spolu, textvariable=vysledok_spolu_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")

    compute_and_update()

    def on_close():
        data = {
            "cena_vyjazd": cena_vyjazd_var.get(),
            "pocet_vyjazdov": pocet_vyjazdov_var.get(),
            "cena_km": cena_km_var.get(),
            "vzdialenost": vzdialenost_var.get(),
            "pocet_ciest": pocet_ciest_var.get(),
        }
        _save_settings(data)
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)
