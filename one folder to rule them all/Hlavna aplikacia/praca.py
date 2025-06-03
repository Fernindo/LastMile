import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import Button


def show_praca_window(cursor):
    cursor.execute("SELECT id, rola, plat_za_hodinu FROM pracovnik_roly")
    roles = cursor.fetchall()

    if not roles:
        messagebox.showwarning("Upozornenie", "Žiadne roly v databáze.")
        return

    praca_window = tk.Toplevel()
    praca_window.title("Odhad pracovnej činnosti")
    praca_window.geometry("1150x600")

    entries = []

    def recalculate():
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
            except:
                continue

    def change_int(var, delta, minimum=0):
        try:
            val = int(var.get()) + delta
            if val < minimum:
                val = minimum
            var.set(str(val))
        except:
            var.set(str(minimum))

    def change_float(var, delta, minimum=0.1):
        try:
            val = float(var.get()) + delta
            if val < minimum:
                val = minimum
            var.set(f"{val:.1f}")
        except:
            var.set(f"{minimum:.1f}")

    def add_row(role_id=None, rola="", plat=0.0):
        row = {}
        idx = len(entries) + 1  # header is row 0

        row["rola_var"] = tk.StringVar(value=rola)
        tk.Entry(table_frame, textvariable=row["rola_var"], width=20, justify="center").grid(row=idx, column=0, padx=2, pady=1)

        row["osoby_var"] = tk.StringVar(value="1")
        tk.Button(table_frame, text="-", width=2, command=lambda: change_int(row["osoby_var"], -1, 1)).grid(row=idx, column=1)
        tk.Entry(table_frame, textvariable=row["osoby_var"], width=5, justify="center").grid(row=idx, column=2)
        tk.Button(table_frame, text="+", width=2, command=lambda: change_int(row["osoby_var"], 1)).grid(row=idx, column=3)

        row["hodiny_var"] = tk.StringVar(value="8")
        tk.Button(table_frame, text="-", width=2, command=lambda: change_int(row["hodiny_var"], -2, 0)).grid(row=idx, column=4)
        tk.Entry(table_frame, textvariable=row["hodiny_var"], width=5, justify="center").grid(row=idx, column=5)
        tk.Button(table_frame, text="+", width=2, command=lambda: change_int(row["hodiny_var"], 2)).grid(row=idx, column=6)

        row["plat_label"] = tk.Label(table_frame, text=f"{plat:.2f}", width=8, relief="groove", anchor="center")
        row["plat_label"].grid(row=idx, column=7, padx=2)

        row["spolu_label"] = tk.Label(table_frame, text="0.00", width=8, relief="sunken", anchor="center")
        row["spolu_label"].grid(row=idx, column=8, padx=2)

        row["koef_var"] = tk.StringVar(value="1.0")
        tk.Button(table_frame, text="-", width=2, command=lambda: change_float(row["koef_var"], -0.1, 0.1)).grid(row=idx, column=9)
        tk.Entry(table_frame, textvariable=row["koef_var"], width=5, justify="center").grid(row=idx, column=10)
        tk.Button(table_frame, text="+", width=2, command=lambda: change_float(row["koef_var"], 0.1)).grid(row=idx, column=11)

        row["predaj_var"] = tk.StringVar(value="0.00")
        tk.Entry(table_frame, textvariable=row["predaj_var"], width=8, justify="center").grid(row=idx, column=12, padx=2)

        entries.append(row)
        recalculate()

        row["osoby_var"].trace_add("write", lambda *args: recalculate())
        row["hodiny_var"].trace_add("write", lambda *args: recalculate())
        row["koef_var"].trace_add("write", lambda *args: recalculate())

    def remove_row():
        if len(entries) <= 1:
            messagebox.showwarning("Upozornenie", "Musí zostať aspoň jedna rola.")
            return
        row = entries.pop()
        for widget in table_frame.grid_slaves():
            if int(widget.grid_info()["row"]) == len(entries) + 1:
                widget.destroy()
        recalculate()

    # Horné tlačidlá
    top_frame = tk.Frame(praca_window)
    top_frame.pack(fill="x", padx=10, pady=10)
    Button(top_frame, text="➕ Pridať", bootstyle="success", command=lambda: add_row(rola="Nová rola", plat=0)).pack(side="left", padx=5)
    Button(top_frame, text="❌ Odstrániť", bootstyle="danger", command=remove_row).pack(side="left", padx=5)

    # Tabuľka
    table_frame = tk.Frame(praca_window)
    table_frame.pack(fill="both", expand=True, padx=10, pady=5)

    headers = [
        ("Rola", 20),
        ("", 2), ("Osoby", 5), ("", 2),
        ("", 2), ("Hodiny", 5), ("", 2),
        ("Plat €/h", 8),
        ("Spolu", 8),
        ("", 2), ("Koef.", 5), ("", 2),
        ("Predaj", 8)
    ]

    for i, (text, width) in enumerate(headers):
        tk.Label(table_frame, text=text, font=("Segoe UI", 10, "bold"), width=width, anchor="center").grid(
            row=0, column=i, padx=2, pady=2
        )

    for role in roles:
        _, rola, plat = role
        add_row(role_id=role[0], rola=rola, plat=plat)

    praca_window.grab_set()
