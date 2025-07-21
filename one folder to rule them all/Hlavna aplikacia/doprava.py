import tkinter as tk
from tkinter import StringVar


def show_doprava_window():
    def safe_float(var):
        try:
            return float(var.get().replace(",", "."))
        except:
            return 0.0

    def safe_int(var):
        try:
            return int(var.get())
        except:
            return 0

    def compute_and_update(event=None):
        ba_total = safe_float(cena_vyjazd_var) * safe_int(pocet_vyjazdov_var)
        mimo_total = (
            safe_float(cena_km_var)
            * safe_float(vzdialenost_var)
            * safe_int(pocet_ciest_var)
        )
        vysledok_ba_var.set(f"{ba_total:.2f} €")
        vysledok_mimo_var.set(f"{mimo_total:.2f} €")
        vysledok_spolu_var.set(f"{ba_total + mimo_total:.2f} €")

    def bind_entry(entry, placeholder):
        def on_focus_in(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg="black")

        def on_focus_out(e):
            if entry.get() == "":
                entry.insert(0, placeholder)
                entry.config(fg="gray")

        entry.insert(0, placeholder)
        entry.config(fg="gray")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        entry.bind("<KeyRelease>", compute_and_update)

    win = tk.Toplevel()
    win.title("Výpočet dopravy")
    win.geometry("340x420")
    win.resizable(False, False)

    # --- Premenné
    cena_vyjazd_var = StringVar()
    pocet_vyjazdov_var = StringVar()
    vysledok_ba_var = StringVar(value="0.00 €")

    cena_km_var = StringVar()
    vzdialenost_var = StringVar()
    pocet_ciest_var = StringVar()
    vysledok_mimo_var = StringVar(value="0.00 €")

    vysledok_spolu_var = StringVar(value="0.00 €")

    # --- Bratislava sekcia
    frame_ba = tk.LabelFrame(win, text="🚗 V Bratislave", padx=10, pady=10)
    frame_ba.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_ba, text="Cena za 1 výjazd (€):").pack(anchor="w")
    e1 = tk.Entry(frame_ba, textvariable=cena_vyjazd_var)
    e1.pack(fill="x")
    bind_entry(e1, "30")

    tk.Label(frame_ba, text="Počet výjazdov:").pack(anchor="w")
    e2 = tk.Entry(frame_ba, textvariable=pocet_vyjazdov_var)
    e2.pack(fill="x")
    bind_entry(e2, "0")

    tk.Label(frame_ba, text="Celková cena (BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_ba, textvariable=vysledok_ba_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- mimo BA sekcia
    frame_mimo = tk.LabelFrame(win, text="🚐 Mimo Bratislavu", padx=10, pady=10)
    frame_mimo.pack(fill="x", padx=10, pady=(5, 5))

    tk.Label(frame_mimo, text="Cena za 1 km (€):").pack(anchor="w")
    e3 = tk.Entry(frame_mimo, textvariable=cena_km_var)
    e3.pack(fill="x")
    bind_entry(e3, "0.55")

    tk.Label(frame_mimo, text="Vzdialenosť (km):").pack(anchor="w")
    e4 = tk.Entry(frame_mimo, textvariable=vzdialenost_var)
    e4.pack(fill="x")
    bind_entry(e4, "0")

    tk.Label(frame_mimo, text="Počet ciest (tam a späť):").pack(anchor="w")
    e5 = tk.Entry(frame_mimo, textvariable=pocet_ciest_var)
    e5.pack(fill="x")
    bind_entry(e5, "0")

    tk.Label(frame_mimo, text="Celková cena (mimo BA):").pack(anchor="w", pady=(5, 0))
    tk.Label(frame_mimo, textvariable=vysledok_mimo_var, font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # --- Spolu sekcia
    frame_spolu = tk.LabelFrame(win, text="💰 Spolu doprava", padx=10, pady=10)
    frame_spolu.pack(fill="x", padx=10, pady=(5, 10))

    tk.Label(frame_spolu, text="Celková suma:").pack(anchor="w")
    tk.Label(frame_spolu, textvariable=vysledok_spolu_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")

    compute_and_update()
