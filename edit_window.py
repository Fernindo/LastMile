# edit_window.py
import tkinter as tk
from tkinter import ttk, messagebox

def open_edit_window(root, conn, cursor, tab_names, tree_columns):
    edit_win = tk.Toplevel(root)
    edit_win.title("Editor tabuliek")
    edit_win.state("zoomed")

    container = tk.Frame(edit_win)
    container.grid(row=0, column=0, sticky="nsew", padx=40, pady=20)

    tk.Label(container, text="Vyber tabuľku:").grid(row=0, column=0, sticky="e", pady=5)
    edit_table_var = tk.StringVar()
    edit_combo = ttk.Combobox(container, textvariable=edit_table_var, values=tab_names, state="readonly")
    edit_combo.grid(row=0, column=1, sticky="ew", pady=5)

    entry_fields = {}
    placeholders = {
        "nazov": "napr. Položka A",
        "jednotka": "napr. ks",
        "pocet": "0",
        "cena": "0.00",
        "koeficient": "1.0",
        "nakup_material": "0.00",
        "dodavatel": "napr. Feri s.r.o.",
        "odkaz": "http://..."
    }

    for idx, col in enumerate(tree_columns[1:], start=1):
        tk.Label(container, text=col).grid(row=idx, column=0, sticky="e", padx=5, pady=5)
        entry = tk.Entry(container, foreground='gray')
        placeholder = placeholders.get(col, '')

        def on_focus_in(e, entry=entry, ph=placeholder):
            if entry.get() == ph:
                entry.delete(0, tk.END)
                entry.config(foreground='black')

        def on_focus_out(e, entry=entry, ph=placeholder):
            if entry.get() == '':
                entry.insert(0, ph)
                entry.config(foreground='gray')

        entry.insert(0, placeholder)
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        entry.grid(row=idx, column=1, sticky="ew", pady=5)
        entry_fields[col] = entry

    def insert_into_db():
        table = edit_table_var.get()
        if not table:
            messagebox.showwarning("Upozornenie", "Vyber tabuľku")
            return
        cols = []
        vals = []
        numeric_cols = {"pocet", "cena", "koeficient", "nakup_material"}
        for col, entry in entry_fields.items():
            val = entry.get()
            if val and val != placeholders.get(col, ''):
                cols.append(col)
                if col in numeric_cols:
                    vals.append(val)
                else:
                    vals.append(f"'{val}'")
        if not cols:
            messagebox.showwarning("Upozornenie", "Vyplň aspoň jeden stĺpec")
            return
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)})"
        try:
            cursor.execute(sql)
            conn.commit()
            show_insert_success_screen(table)
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    def show_insert_success_screen(table):
        for widget in container.winfo_children():
            widget.destroy()

        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()

        tree_success = ttk.Treeview(container, columns=tree_columns, show="headings")
        for col in tree_columns:
            tree_success.heading(col, text=col)
        tree_success.grid(row=0, column=0, columnspan=2, sticky="nsew")
        for row in rows:
            tree_success.insert("", tk.END, values=row)

        button_frame = tk.Frame(container)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="Späť na domovskú stránku", command=edit_win.destroy).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Vložiť ďalšie položky", command=lambda: [edit_win.destroy(), open_edit_window(root, conn, cursor, tab_names, tree_columns)]).pack(side=tk.LEFT, padx=10)

    btn_frame = tk.Frame(container)
    btn_frame.grid(row=len(tree_columns)+1, column=0, columnspan=2, pady=10)
    tk.Button(btn_frame, text="Insert", command=insert_into_db, width=20).pack(side=tk.LEFT, padx=10)
