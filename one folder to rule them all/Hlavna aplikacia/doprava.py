import tkinter as tk
from tkinter import StringVar, DoubleVar, IntVar


def show_doprava_window():
    def compute_and_update(event=None):
        try:
            ba_total = float(cena_vyjazd_var.get()) * pocet_vyjazdov_var.get()
        except:
            ba_total = 0.0
        try:
            mimo_total = cena_km_var.get() * vzdialenost_var.get() * pocet_ciest_var.get()
        except:
            mimo_total = 0.0

        vysledok_ba_var.set(f"{ba_total:.2f} €")
        vysledok_mimo_var.set(f"{mimo_total:.2f} €")
        vysledok_spolu_var.set(f"{ba_total + mimo_total:.2f} €")

    def bind_all(widget):
        widget.bind("<KeyRelease>", compute_and_update)
        widget.bind("<FocusOut>", compute_and_update)
        widget.bind("<ButtonRelease>", compute_and_update)  # šípky v Spinboxe

    win = tk.Toplevel()
    win.title("Výpočet dopravy")
    win.geometry("340x440")
    win.resizable(False, False)

    # --- Premenné
    cena_vyjazd_var = StringVar(value="30.00")
    pocet_vyjazdov_var = IntVar(value=0)
    vysledok_ba_var = StringVar(value="0.00 €")

    cena_km_var = DoubleVar(value=0.55)
    vzdialenost_var = DoubleVar(value=0.0)
    pocet_ciest_var = IntVar(value=0)
    vysledok_mimo_var = StringVar(value="0.00 €")

    vysledok_spolu_var = StringVar(value="0.00 €")

    # --- Bratislava sekcia
    frame_ba = tk.LabelFrame(win, text="🚗 V Bratislave", padx=10, pady=10)
    frame_ba.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_ba, text="Cena za 1 výjazd (€):").pack(anchor="w")
    entry_cena = tk.Entry(frame_ba, textvariable=cena_vyjazd_var)
    entry_cena.pack(fill="x")
    bind_all(entry_cena)

    tk.Label(frame_ba, text="Počet výjazdov:").pack(anchor="w")
    spin_vyjazdy = tk.Spinbox(frame_ba, from_=0, to=100, increment=1, textvariable=pocet_vyjazdov_var)
    spin_vyjazdy.pack(fill="x")
    bind_all(spin_vyjazdy)

    tk.Label(frame_ba, text="Celková cena (BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_ba, textvariable=vysledok_ba_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- mimo BA sekcia
    frame_mimo = tk.LabelFrame(win, text="🚐 Mimo Bratislavu", padx=10, pady=10)
    frame_mimo.pack(fill="x", padx=10, pady=(5, 5))

    tk.Label(frame_mimo, text="Cena za 1 km (€):").pack(anchor="w")
    entry_km = tk.Entry(frame_mimo, textvariable=cena_km_var)
    entry_km.pack(fill="x")
    bind_all(entry_km)

    tk.Label(frame_mimo, text="Vzdialenosť (km):").pack(anchor="w")
    spin_km = tk.Spinbox(frame_mimo, from_=0, to=1000, increment=1, textvariable=vzdialenost_var)
    spin_km.pack(fill="x")
    bind_all(spin_km)

    tk.Label(frame_mimo, text="Počet ciest (tam a späť):").pack(anchor="w")
    spin_cesty = tk.Spinbox(frame_mimo, from_=0, to=100, increment=1, textvariable=pocet_ciest_var)
    spin_cesty.pack(fill="x")
    bind_all(spin_cesty)

    tk.Label(frame_mimo, text="Celková cena (mimo BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_mimo, textvariable=vysledok_mimo_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- Spolu sekcia
    frame_spolu = tk.LabelFrame(win, text="💰 Spolu doprava", padx=10, pady=10)
    frame_spolu.pack(fill="x", padx=10, pady=(5, 10))

    tk.Label(frame_spolu, text="Celková suma:").pack(anchor="w")
    tk.Label(frame_spolu, textvariable=vysledok_spolu_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")

    compute_and_update()
