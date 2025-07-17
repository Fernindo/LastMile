# Consolidated helper functions and widgets
import os
import shutil
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import xlwings as xw
from ttkbootstrap import Button
from excel_processing import update_excel


def parse_float(text: str) -> float:
    """Parse a float allowing comma as decimal separator."""
    return float(text.replace(",", ".").strip())


def askfloat_locale(title, prompt, **kwargs):
    """Prompt user for a float, accepting comma decimal separator."""
    while True:
        value = tk.simpledialog.askstring(title, prompt, **kwargs)
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



# ---------------------------------------------------------------------------
# Filter panel UI (from filter_panel.py)
# ---------------------------------------------------------------------------
def create_filter_panel(parent, on_mousewheel_callback, width_fraction=0.2, min_width=250, max_width=450):
    """Create a horizontally scrollable filter panel."""
    filter_container = tk.Frame(parent, bg="white")
    filter_container.pack_propagate(False)

    def _adjust_width(event):
        total_w = event.width
        target = int(total_w * width_fraction)
        target = max(min(target, max_width), min_width)
        filter_container.config(width=target)

    parent.bind("<Configure>", _adjust_width)

    canvas = tk.Canvas(filter_container, bg="white", highlightthickness=0)
    h_scrollbar = tk.Scrollbar(filter_container, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=h_scrollbar.set)

    filter_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=filter_frame, anchor="nw")

    canvas.pack(fill=tk.BOTH, expand=True)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_enter(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    def _on_leave(event):
        canvas.unbind_all("<MouseWheel>")
    def _on_mousewheel(event):
        if event.state & 0x0001:
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

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
def create_notes_panel(parent, project_name):
    """Create a simple note-taking panel bound to a text file."""
    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    tk.Label(frame, text="Poznámky:", font=("Arial", 10)).pack(anchor="w")
    text_widget = tk.Text(frame, height=6, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True)

    file_path = f"{project_name}_notes.txt"

    def save_notes():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_widget.get("1.0", tk.END).strip())
        print(f"📝 Notes saved to {file_path}")

    def on_text_change(event):
        if text_widget.edit_modified():
            save_notes()
            text_widget.edit_modified(False)

    text_widget.bind("<<Modified>>", on_text_change)
    text_widget.bind("<FocusOut>", lambda e: save_notes())

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            text_widget.insert("1.0", f.read())
        text_widget.edit_modified(False)

    return frame


# ---------------------------------------------------------------------------
# Work estimation window (from praca.py)
# ---------------------------------------------------------------------------
def show_praca_window(cursor):
    """Display a popup window for work/role estimation."""
    cursor.execute("SELECT id, rola, plat_za_hodinu FROM pracovnik_roly")
    roles = cursor.fetchall()
    if not roles:
        messagebox.showwarning("Upozornenie", "Žiadne roly v databáze.")
        return

    praca_window = tk.Toplevel()
    praca_window.title("🛠️ Odhad pracovnej činnosti")
    praca_window.geometry("1000x500")
    praca_window.configure(bg="#f9f9f9")

    entries = []
    celkovy_predaj_var = tk.StringVar(value="0.00")

    def recalculate():
        for row in entries:
            try:
                osoby = int(row["osoby_var"].get())
                hodiny = int(row["hodiny_var"].get())
                plat = parse_float(row["plat_label"].cget("text"))
                koef = parse_float(row["koef_var"].get())
                spolu = osoby * hodiny * plat
                predaj = spolu * koef
                row["spolu_label"].config(text=f"{spolu:.2f}")
                row["predaj_var"].set(f"{predaj:.2f}")
            except Exception:
                continue

        try:
            suma = sum(parse_float(r["predaj_var"].get()) for r in entries)
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
            val = parse_float(var.get()) + delta
            if val < minimum:
                val = minimum
            var.set(f"{val:.1f}")
        except Exception:
            var.set(f"{minimum:.1f}")

    def add_row(role_id=None, rola="", plat=0.0):
        row = {}
        idx = len(entries) + 1

        row["rola_var"] = tk.StringVar(value=rola)
        tk.Entry(table_frame, textvariable=row["rola_var"], width=25, justify="center").grid(row=idx, column=0, padx=4, pady=4)

        row["osoby_var"] = tk.StringVar(value="1")
        tk.Button(table_frame, text="-", width=3, command=lambda: change_int(row["osoby_var"], -1, 1)).grid(row=idx, column=1, padx=1)
        tk.Entry(table_frame, textvariable=row["osoby_var"], width=6, justify="center").grid(row=idx, column=2, padx=1)
        tk.Button(table_frame, text="+", width=3, command=lambda: change_int(row["osoby_var"], 1)).grid(row=idx, column=3, padx=1)

        row["hodiny_var"] = tk.StringVar(value="8")
        tk.Button(table_frame, text="-", width=3, command=lambda: change_int(row["hodiny_var"], -2, 0)).grid(row=idx, column=4, padx=1)
        tk.Entry(table_frame, textvariable=row["hodiny_var"], width=6, justify="center").grid(row=idx, column=5, padx=1)
        tk.Button(table_frame, text="+", width=3, command=lambda: change_int(row["hodiny_var"], 2)).grid(row=idx, column=6, padx=1)

        row["plat_label"] = tk.Label(table_frame, text=f"{plat:.2f}", width=10, relief="groove", anchor="center", bg="#fff")
        row["plat_label"].grid(row=idx, column=7, padx=4)

        row["spolu_label"] = tk.Label(table_frame, text="0.00", width=10, relief="sunken", anchor="center", bg="#f0f0f0")
        row["spolu_label"].grid(row=idx, column=8, padx=4)

        row["koef_var"] = tk.StringVar(value="1.0")
        tk.Button(table_frame, text="-", width=3, command=lambda: change_float(row["koef_var"], -0.1, 0.1)).grid(row=idx, column=9, padx=1)
        tk.Entry(table_frame, textvariable=row["koef_var"], width=6, justify="center").grid(row=idx, column=10, padx=1)
        tk.Button(table_frame, text="+", width=3, command=lambda: change_float(row["koef_var"], 0.1)).grid(row=idx, column=11, padx=1)

        row["predaj_var"] = tk.StringVar(value="0.00")
        tk.Entry(table_frame, textvariable=row["predaj_var"], width=10, justify="center").grid(row=idx, column=12, padx=4)

        entries.append(row)
        recalculate()

        row["osoby_var"].trace_add("write", lambda *args: recalculate())
        row["hodiny_var"].trace_add("write", lambda *args: recalculate())
        row["koef_var"].trace_add("write", lambda *args: recalculate())

    def remove_row():
        if len(entries) <= 1:
            messagebox.showwarning("Upozornenie", "Musí zostať aspoň jedna rola.")
            return
        entries.pop()
        for widget in table_frame.grid_slaves():
            if int(widget.grid_info()["row"]) == len(entries) + 1:
                widget.destroy()
        recalculate()

    top_frame = tk.Frame(praca_window, bg="#f9f9f9")
    top_frame.pack(fill="x", padx=15, pady=15)
    Button(top_frame, text="➕ Pridať", bootstyle="success", width=12, command=lambda: add_row(rola="Nová rola", plat=0)).pack(side="left", padx=10)
    Button(top_frame, text="❌ Odstrániť", bootstyle="danger", width=12, command=remove_row).pack(side="left", padx=10)

    global table_frame
    table_frame = tk.Frame(praca_window, bg="#fdfdfd", bd=2, relief="groove")
    table_frame.pack(fill="both", expand=True, padx=15, pady=10)

    headers = [
        ("Rola", 25),
        ("", 3), ("Osoby", 6), ("", 3),
        ("", 3), ("Hodiny", 6), ("", 3),
        ("Plat €/h", 10),
        ("Spolu", 10),
        ("", 3), ("Koef.", 6), ("", 3),
        ("Predaj", 10),
    ]

    for i, (text, width) in enumerate(headers):
        tk.Label(table_frame, text=text, font=("Segoe UI", 10, "bold"), width=width, bg="#e6e6fa", relief="ridge").grid(row=0, column=i, padx=2, pady=2)

    for role in roles:
        _, rola, plat = role
        add_row(role_id=role[0], rola=rola, plat=plat)

    summary_frame = tk.Frame(praca_window, bg="#f9f9f9")
    summary_frame.pack(fill="x", padx=15, pady=(0, 15))
    tk.Label(summary_frame, text="Celkový predaj:", font=("Segoe UI", 15, "bold"), bg="#f9f9f9").pack(side="left")
    tk.Label(summary_frame, textvariable=celkovy_predaj_var, font=("Segoe UI", 15), bg="#f9f9f9").pack(side="left", padx=(5, 0))

    praca_window.grab_set()
