import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import Button


def show_praca_window(cursor):
    # Ziskame role z DB
    cursor.execute("SELECT id, rola, plat_za_hodinu FROM pracovnik_roly")
    roles = cursor.fetchall()

    if not roles:
        messagebox.showwarning("Upozornenie", "Žiadne roly v databáze.")
        return

    # Vytvorenie okna
    praca_window = tk.Toplevel()
    praca_window.title("🛠️ Odhad pracovnej činnosti")
    praca_window.geometry("1000x500")
    praca_window.configure(bg="#f9f9f9")

    entries = []
    celkovy_predaj_var = tk.StringVar(value="0.00")  # pre celkovy predaj

    def recalculate():
        # Pre kazdy riadok prepocteme hodnoty
        for row in entries:
            try:
                osoby = int(row["osoby_var"].get())
                hodiny = int(row["hodiny_var"].get())
                plat = float(row["plat_label"].cget("text"))
                koef = float(row["koef_var"].get())
                spolu = osoby * hodiny * plat
                predaj = spolu * koef
                row["spolu_label"].config(text=f"{spolu:.2f}")
                row["predaj_var"].set(f"{predaj:.2f}")
            except Exception:
                continue

        # Spocteme celkovy predaj
        try:
            suma = sum(float(r["predaj_var"].get()) for r in entries)
        except Exception:
            suma = 0.0
        celkovy_predaj_var.set(f"{suma:.2f}")

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
            val = float(var.get()) + delta
            if val < minimum:
                val = minimum
            var.set(f"{val:.1f}")
        except Exception:
            var.set(f"{minimum:.1f}")

    def add_row(role_id=None, rola="", plat=0.0):
        row = {}
        idx = len(entries) + 1

        # Nazov roly
        row["rola_var"] = tk.StringVar(value=rola)
        tk.Entry(table_frame, textvariable=row["rola_var"], width=25, justify="center")\
            .grid(row=idx, column=0, padx=4, pady=4)

        # Pocet osob
        row["osoby_var"] = tk.StringVar(value="1")
        tk.Button(table_frame, text="-", width=3,
                  command=lambda: change_int(row["osoby_var"], -1, 1))\
            .grid(row=idx, column=1, padx=1)
        tk.Entry(table_frame, textvariable=row["osoby_var"], width=6, justify="center")\
            .grid(row=idx, column=2, padx=1)
        tk.Button(table_frame, text="+", width=3,
                  command=lambda: change_int(row["osoby_var"], 1))\
            .grid(row=idx, column=3, padx=1)

        # Hodiny
        row["hodiny_var"] = tk.StringVar(value="8")
        tk.Button(table_frame, text="-", width=3,
                  command=lambda: change_int(row["hodiny_var"], -2, 0))\
            .grid(row=idx, column=4, padx=1)
        tk.Entry(table_frame, textvariable=row["hodiny_var"], width=6, justify="center")\
            .grid(row=idx, column=5, padx=1)
        tk.Button(table_frame, text="+", width=3,
                  command=lambda: change_int(row["hodiny_var"], 2))\
            .grid(row=idx, column=6, padx=1)

        # Plat
        row["plat_label"] = tk.Label(table_frame, text=f"{plat:.2f}", width=10,
                                      relief="groove", anchor="center", bg="#fff")
        row["plat_label"].grid(row=idx, column=7, padx=4)

        # Spolu
        row["spolu_label"] = tk.Label(table_frame, text="0.00", width=10,
                                        relief="sunken", anchor="center", bg="#f0f0f0")
        row["spolu_label"].grid(row=idx, column=8, padx=4)

        # Koeficient
        row["koef_var"] = tk.StringVar(value="1.0")
        tk.Button(table_frame, text="-", width=3,
                  command=lambda: change_float(row["koef_var"], -0.1, 0.1))\
            .grid(row=idx, column=9, padx=1)
        tk.Entry(table_frame, textvariable=row["koef_var"], width=6, justify="center")\
            .grid(row=idx, column=10, padx=1)
        tk.Button(table_frame, text="+", width=3,
                  command=lambda: change_float(row["koef_var"], 0.1))\
            .grid(row=idx, column=11, padx=1)

        # Predaj
        row["predaj_var"] = tk.StringVar(value="0.00")
        tk.Entry(table_frame, textvariable=row["predaj_var"], width=10, justify="center")\
            .grid(row=idx, column=12, padx=4)

        entries.append(row)
        recalculate()

        # Trace pre dynamicke prepocty
        row["osoby_var"].trace_add("write", lambda *args: recalculate())
        row["hodiny_var"].trace_add("write", lambda *args: recalculate())
        row["koef_var"].trace_add("write", lambda *args: recalculate())

    def remove_row():
        if len(entries) <= 1:
            messagebox.showwarning("Upozornenie", "Musí zostať aspoň jedna rola.")
            return
        # Odstranenie posledneho riadku
        row = entries.pop()
        for widget in table_frame.grid_slaves():
            if int(widget.grid_info()["row"]) == len(entries) + 1:
                widget.destroy()
        recalculate()

    # Horny panel s tlacitkami
    top_frame = tk.Frame(praca_window, bg="#f9f9f9")
    top_frame.pack(fill="x", padx=15, pady=15)
    Button(top_frame, text="➕ Pridať", bootstyle="success", width=12,
           command=lambda: add_row(rola="Nová rola", plat=0))\
        .pack(side="left", padx=10)
    Button(top_frame, text="❌ Odstrániť", bootstyle="danger", width=12,
           command=remove_row)\
        .pack(side="left", padx=10)

    # Tabulka
    table_frame = tk.Frame(praca_window, bg="#fdfdfd", bd=2, relief="groove")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    headers = [
        ("Rola", 25),
        ("", 3), ("Osoby", 6), ("", 3),
        ("", 3), ("Hodiny", 6), ("", 3),
        ("Plat €/h", 10),
        ("Spolu", 10),
        ("", 3), ("Koef.", 6), ("", 3),
        ("Predaj", 10)
    ]

    for i, (text, width) in enumerate(headers):
        tk.Label(table_frame, text=text, font=("Segoe UI", 10, "bold"), width=width,
                 bg="#e6e6fa", relief="ridge")\
            .grid(row=0, column=i, padx=2, pady=2)

    # Naplnenie riadkov z DB
    for role in roles:
        _, rola, plat = role
        add_row(role_id=role[0], rola=rola, plat=plat)

    # Spodny panel so suctom
    summary_frame = tk.Frame(praca_window, bg="#f9f9f9")
    summary_frame.pack(fill="x", padx=15, pady=(0,15))
    tk.Label(summary_frame, text="Celkový predaj:", font=("Segoe UI", 15, "bold"), bg="#f9f9f9")\
        .pack(side="left")
    tk.Label(summary_frame, textvariable=celkovy_predaj_var, font=("Segoe UI", 15), bg="#f9f9f9")\
        .pack(side="left", padx=(5,0))

    praca_window.grab_set()
