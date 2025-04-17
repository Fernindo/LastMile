# filter_panel.py

import tkinter as tk
from tkinter import ttk
import psycopg2

ALL_COLUMNS = [
    "produkt", "jednotky", "dodavatel", "odkaz",
    "koeficient", "nakup_materialu", "cena_prace", "class_id"
]

class FilterPanel:
    def __init__(self, parent, get_connection_func, on_filter_apply, on_columns_change, selected_columns):
        self.parent = parent
        self.get_connection = get_connection_func
        self.on_filter_apply = on_filter_apply
        self.on_columns_change = on_columns_change
        self.selected_columns = selected_columns
        self.visible = False

        self.container = tk.Frame(self.parent)
        self.container.pack(fill=tk.X, padx=5, pady=2)

        self.toggle_btn = tk.Button(self.container, text="🢃 Zobraziť filter", command=self.toggle)
        self.toggle_btn.grid(row=0, column=0, sticky="w", padx=2, pady=2)

        self.frame = tk.Frame(self.container)
        self.frame.grid(row=1, column=0, columnspan=10, sticky="ew")
        self.frame.grid_remove()

        # Výber kategórie + tabuľky
        tk.Label(self.frame, text="Hlavná kategória:").grid(row=0, column=0, padx=5, pady=5)
        self.kat_var = tk.StringVar()
        self.kat_combo = ttk.Combobox(self.frame, textvariable=self.kat_var, state="readonly")
        self.kat_combo["values"] = ["SK", "EZS", "CCTV"]
        self.kat_combo.grid(row=0, column=1, padx=5)
        self.kat_combo.bind("<<ComboboxSelected>>", self.update_table_options)

        tk.Label(self.frame, text="Tabuľka:").grid(row=0, column=2, padx=5)
        self.tab_var = tk.StringVar()
        self.tab_combo = ttk.Combobox(self.frame, textvariable=self.tab_var, state="readonly")
        self.tab_combo.grid(row=0, column=3, padx=5)

        tk.Button(self.frame, text="Použiť filter", command=self.apply_filter).grid(row=0, column=4, padx=5)

        # Checkboxy (stĺpce)
        self.check_vars = {}
        for i, col in enumerate(ALL_COLUMNS):
            var = tk.BooleanVar(value=col in self.selected_columns)
            cb = tk.Checkbutton(self.frame, text=col, variable=var, command=self.columns_changed)
            cb.grid(row=1, column=i, sticky="w", padx=5)
            self.check_vars[col] = var

        # Checkbox: zobraziť prázdne kategórie
        self.show_empty_var = tk.BooleanVar(value=False)
        self.empty_cb = tk.Checkbutton(self.frame, text="Zobraziť prázdne kategórie", variable=self.show_empty_var)
        self.empty_cb.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 10))

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self.frame.grid()
            self.toggle_btn.config(text="🡡 Skryť filter")
        else:
            self.frame.grid_remove()
            self.toggle_btn.config(text="🢃 Zobraziť filter")

    def update_table_options(self, event=None):
        kategoria = self.kat_var.get()
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT nazov_tabulky FROM class WHERE hlavna_kategoria = %s ORDER BY nazov_tabulky", (kategoria,))
        tables = [row[0] for row in cur.fetchall()]
        self.tab_combo["values"] = tables
        if tables:
            self.tab_combo.current(0)
        cur.close()
        conn.close()

    def apply_filter(self):
        if self.on_filter_apply:
            self.on_filter_apply(
                kategoria=self.kat_var.get(),
                tabulka=self.tab_var.get()
            )

    def columns_changed(self):
        self.selected_columns = [col for col, var in self.check_vars.items() if var.get()]
        if self.on_columns_change:
            self.on_columns_change(self.selected_columns)

    def get_selected_columns(self):
        return self.selected_columns

    def should_show_empty_categories(self):
        return self.show_empty_var.get()
