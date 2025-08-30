# Consolidated helper functions and widgets
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ttkbootstrap import Button


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
# Filter panel UI (from filter_panel.py)
# ---------------------------------------------------------------------------
def create_filter_panel(parent, on_mousewheel_callback, width_fraction=0.2, min_width=250, max_width=450):
    """Create a horizontally scrollable filter panel."""
    filter_container = tk.Frame(parent, bg="white")
    filter_container.pack_propagate(False)

    resize_job = [None]

    def _set_width(total_w):
        target = int(total_w * width_fraction)
        target = max(min(target, max_width), min_width)
        if abs(filter_container.winfo_width() - target) > 1:
            filter_container.config(width=target)

    def _adjust_width(event):
        if resize_job[0] is not None:
            filter_container.after_cancel(resize_job[0])
        resize_job[0] = filter_container.after(100, lambda w=event.width: _set_width(w))

    parent.bind("<Configure>", _adjust_width)
    parent.update_idletasks()
    _set_width(parent.winfo_width())

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
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
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

        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(data, jf, ensure_ascii=False, indent=2)
        print(f"📝 Notes saved to {json_path}")

    def on_text_change(event):
        text_widget.edit_modified(False)

    text_widget.bind("<<Modified>>", on_text_change)

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                text_widget.insert("1.0", data.get("notes_text", ""))
            text_widget.edit_modified(False)
        except Exception:
            pass

    return frame


# ---------------------------------------------------------------------------
# Work estimation window (from praca.py)
# ---------------------------------------------------------------------------
def show_praca_window(cursor):
    from tkinter import messagebox
    from ttkbootstrap import Button

    cursor.execute("SELECT id, rola, plat_za_hodinu FROM pracovnik_roly")
    roles = cursor.fetchall()
    if not roles:
        messagebox.showwarning("Upozornenie", "Žiadne roly v databáze.")
        return

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

    entries = []
    praca_nakup_var = tk.StringVar(value="0.00")
    praca_predaj_var = tk.StringVar(value="0.00")
    praca_marza_var = tk.StringVar(value="0.00")

    def recalculate():
        nakup_sum = 0.0
        predaj_sum = 0.0

        for row in entries:
            try:
                osoby = int(row["osoby_var"].get())
                hodiny = int(row["hodiny_var"].get())
                if "plat_entry" in row:
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

    def add_row(role_id=None, rola="", plat=0.0):
        row = {}
        idx = len(entries) + 1

        row["rola_var"] = tk.StringVar(value=rola)
        tk.Entry(table_frame, textvariable=row["rola_var"], justify="center").grid(row=idx, column=0, padx=6, pady=4, sticky="nsew")

        row["osoby_var"] = tk.StringVar(value="1")
        Button(table_frame, text="−", bootstyle="warning", command=lambda: change_int(row["osoby_var"], -1, 1)).grid(row=idx, column=1, sticky="nsew", padx=2, pady=(6, 2))
        tk.Entry(table_frame, textvariable=row["osoby_var"], justify="center").grid(row=idx, column=2, sticky="nsew", padx=2)
        Button(table_frame, text="+", bootstyle="warning", command=lambda: change_int(row["osoby_var"], 1)).grid(row=idx, column=3, sticky="nsew", padx=2, pady=(6, 2))

        row["hodiny_var"] = tk.StringVar(value="8")
        Button(table_frame, text="−", bootstyle="warning", command=lambda: change_int(row["hodiny_var"], -2, 0)).grid(row=idx, column=4, sticky="nsew", padx=2, pady=(6, 2))
        tk.Entry(table_frame, textvariable=row["hodiny_var"], justify="center").grid(row=idx, column=5, sticky="nsew", padx=2)
        Button(table_frame, text="+", bootstyle="warning", command=lambda: change_int(row["hodiny_var"], 2)).grid(row=idx, column=6, sticky="nsew", padx=2, pady=(6, 2))

        if role_id is None:
            row["plat_var"] = tk.StringVar(value=f"{plat:.2f}")
            entry = tk.Entry(table_frame, textvariable=row["plat_var"], justify="center", width=10)
            entry.grid(row=idx, column=7, sticky="nsew", padx=2)
            row["plat_entry"] = entry
        else:
            row["plat_label"] = tk.Label(table_frame, text=f"{plat:.2f}", relief="groove", anchor="center", bg="#ffffff")
            row["plat_label"].grid(row=idx, column=7, sticky="nsew", padx=2)

        row["spolu_label"] = tk.Label(table_frame, text="0.00", relief="sunken", anchor="center", bg="#f0f0f0")
        row["spolu_label"].grid(row=idx, column=8, sticky="nsew", padx=2)

        row["koef_var"] = tk.StringVar(value="1.0")
        Button(table_frame, text="−", bootstyle="warning", command=lambda: change_float(row["koef_var"], -0.1, 0.1)).grid(row=idx, column=9, sticky="nsew", padx=2, pady=(6, 2))
        tk.Entry(table_frame, textvariable=row["koef_var"], justify="center").grid(row=idx, column=10, sticky="nsew", padx=2)
        Button(table_frame, text="+", bootstyle="warning", command=lambda: change_float(row["koef_var"], 0.1)).grid(row=idx, column=11, sticky="nsew", padx=2, pady=(6, 2))

        row["predaj_var"] = tk.StringVar(value="0.00")
        tk.Entry(table_frame, textvariable=row["predaj_var"], justify="center").grid(row=idx, column=12, sticky="nsew", padx=2)

        row["del_btn"] = Button(table_frame, text="✖", bootstyle="danger", command=lambda r=row: remove_specific_row(r))
        row["del_btn"].grid(row=idx, column=13, sticky="nsew", padx=2, pady=(6, 2))

        entries.append(row)
        recalculate()

        row["osoby_var"].trace_add("write", lambda *args: recalculate())
        row["hodiny_var"].trace_add("write", lambda *args: recalculate())
        row["koef_var"].trace_add("write", lambda *args: recalculate())
        if "plat_var" in row:
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
    Button(top_frame, text="➕ Pridať", bootstyle="success", width=12, command=lambda: add_row(rola="Nová rola", plat=0)).pack(side="left", padx=10)
    Button(top_frame, text="❌ Odstrániť", bootstyle="danger", width=12, command=remove_row).pack(side="left", padx=10)

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
            pady=5
        )
        label.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
        table_frame.grid_columnconfigure(i, weight=1)

        if text == "−" and i in (1, 4, 9):
            field = "osoby_var" if i == 1 else "hodiny_var" if i == 4 else "koef_var"
            is_float = i == 9
            label.bind("<Button-1>", lambda e, f=field, fl=is_float: adjust_column(f, -1 if not fl else -0.1, fl))
        elif text == "+" and i in (3, 6, 11):
            field = "osoby_var" if i == 3 else "hodiny_var" if i == 6 else "koef_var"
            is_float = i == 11
            label.bind("<Button-1>", lambda e, f=field, fl=is_float: adjust_column(f, 1 if not fl else 0.1, fl))

    for role in roles:
        role_id, rola, plat = role
        add_row(role_id=role_id, rola=rola, plat=plat)

    summary_frame = tk.Frame(praca_window, bg="#e9f0fb")
    summary_frame.pack(fill="x", padx=15, pady=(0, 15))

    tk.Label(summary_frame, text="Práca nákup:", font=("Segoe UI", 10), bg="#e9f0fb").pack(side="left", padx=(0, 5))
    tk.Label(summary_frame, textvariable=praca_nakup_var, font=("Segoe UI", 10, "bold"), bg="#e9f0fb").pack(side="left", padx=(0, 20))

    tk.Label(summary_frame, text="Práca marža:", font=("Segoe UI", 10), bg="#e9f0fb").pack(side="left", padx=(0, 5))
    tk.Label(summary_frame, textvariable=praca_marza_var, font=("Segoe UI", 10, "bold"), bg="#e9f0fb").pack(side="left", padx=(0, 20))

    tk.Label(summary_frame, text="Práca predaj:", font=("Segoe UI", 10), bg="#e9f0fb").pack(side="left", padx=(0, 5))
    tk.Label(summary_frame, textvariable=praca_predaj_var, font=("Segoe UI", 10, "bold"), bg="#e9f0fb").pack(side="left", padx=(0, 20))
