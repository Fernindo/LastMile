"""
gui_demo.py - Demo of a Hierarchical Filter Panel

This demo creates an in-memory SQLite database with sample data in the
"class" table (categories/subcategories) and the "produkty" table.
The filter panel on the left always shows category labels and subcategory
checkboxes. For example, the category "SK" will display its subcategories
directly beneath it.

The product list on the right is filtered based solely on which subcategory
checkboxes are checked, along with a text search in the "Vyhľadávanie" box.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import sys
import shutil
import sqlite3
import decimal
from datetime import datetime
from collections import OrderedDict
import json
import unicodedata

########################################################################
# 1) CREATE AN IN-MEMORY DATABASE WITH SAMPLE DATA
########################################################################

def create_in_memory_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create "class" table (categories and subcategories)
    cursor.execute("DROP TABLE IF EXISTS class")
    cursor.execute("""
        CREATE TABLE class (
            id INTEGER PRIMARY KEY,
            hlavna_kategoria TEXT,
            nazov_tabulky TEXT
        )
    """)
    # Sample data – note: "SK" category has two subcategories
    sample_class_data = [
        (1, 'CCTV', 'IP Kamery'),
        (2, 'CCTV', 'Analógové kamery'),
        (3, 'EZS', 'Environmentálne detektory'),
        (4, 'EZS', 'Magnetické kontakty'),
        (5, 'SK', 'Moja subkategória 1'),
        (6, 'SK', 'Moja subkategória 2')
    ]
    cursor.executemany("INSERT INTO class VALUES (?, ?, ?)", sample_class_data)
    
    # Create "produkty" table
    cursor.execute("DROP TABLE IF EXISTS produkty")
    cursor.execute("""
        CREATE TABLE produkty (
            id INTEGER PRIMARY KEY,
            produkt TEXT,
            jednotky TEXT,
            dodavatel TEXT,
            odkaz TEXT,
            koeficient REAL,
            nakup_materialu REAL,
            cena_prace REAL,
            class_id INTEGER,
            class_name TEXT
        )
    """)
    sample_produkty_data = [
        (1, "Hikvision IP Cam", "ks", "Hikvision", "https://example.com/hik-ip", 1.0, 20.0, 100.0, 1, 'IP Kamery'),
        (2, "Generic Analog Cam", "ks", "Generic", "https://example.com/analog", 1.0, 15.0, 50.0, 2, 'Analógové kamery'),
        (3, "Detektor dymu", "ks", "Generic", "https://example.com/detector", 1.0, 12.0, 60.0, 3, 'Environmentálne detektory'),
        (4, "Magnet kontakt", "ks", "Generic", "https://example.com/magnet", 1.0, 5.0, 20.0, 4, 'Magnetické kontakty'),
        (5, "Vec SK 1", "ks", "Local", "https://example.com/sk1", 1.2, 10.0, 30.0, 5, 'Moja subkategória 1'),
        (6, "Vec SK 2", "ks", "Local", "https://example.com/sk2", 1.2, 15.0, 40.0, 6, 'Moja subkategória 2')
    ]
    cursor.executemany("INSERT INTO produkty VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_produkty_data)
    
    conn.commit()
    return conn

########################################################################
# 2) Helper Functions for Filtering and Removing Accents
########################################################################

def remove_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def apply_filters(cursor, table_vars, name_entry, tree):
    """
    Filters products based on which subcategory checkboxes are checked and the name search.
    """
    selected_table_ids = [str(cid) for cid, var in table_vars.items() if var.get()]
    name_filter = remove_accents(name_entry.get().strip().lower())
    
    base_query = """
        SELECT p.produkt, p.jednotky, p.dodavatel, p.odkaz,
               p.koeficient, p.nakup_materialu, p.cena_prace,
               c.id, c.hlavna_kategoria, c.nazov_tabulky
        FROM produkty p
        JOIN class c ON p.class_id = c.id
        WHERE 1=1
    """
    params = []
    if selected_table_ids:
        placeholders = ','.join(['?']*len(selected_table_ids))
        base_query += f" AND c.id IN ({placeholders})"
        params.extend(selected_table_ids)
    
    print("\n=== apply_filters ===")
    print("Selected subcategory IDs:", selected_table_ids)
    print("Name filter:", name_filter)
    print("SQL Query:", base_query)
    print("Params:", params)
    
    cursor.execute(base_query, tuple(params))
    all_rows = cursor.fetchall()
    print(f"Rows from DB: {len(all_rows)}")
    
    # Apply name filter
    filtered = []
    for row in all_rows:
        prod = row[0] or ""
        if name_filter and name_filter not in remove_accents(prod.lower()):
            continue
        filtered.append(row)
    print(f"Rows after name filter: {len(filtered)}")
    
    tree.delete(*tree.get_children())
    filtered.sort(key=lambda r: (r[8], r[9], r[0]))
    grouped = {}
    for row in filtered:
        cat = row[8]
        subcat = row[9]
        grouped.setdefault(cat, {}).setdefault(subcat, []).append(row[:8])
    for cat in sorted(grouped):
        tree.insert("", "end", values=("", f"-- {cat} --"), tags=("header",))
        for subcat in sorted(grouped[cat]):
            tree.insert("", "end", values=("", f"   > {subcat}"), tags=("subheader",))
            for row_data in grouped[cat][subcat]:
                tree.insert("", "end", values=row_data)
    tree.tag_configure("header", font=("Arial", 10, "bold"))
    tree.tag_configure("subheader", font=("Arial", 9, "italic"))

########################################################################
# 3) Create the Filter Panel - Always Display Subcategories
########################################################################

def create_filter_panel(parent, on_filter_callback):
    """
    Creates a scrollable filter panel.
    Categories are always shown as labels, with their subcategories (with checkboxes)
    always visible (i.e. under each category, the subcategory checkboxes are listed).
    """
    frame = tk.Frame(parent, bg="white", width=250)
    frame.pack_propagate(False)
    
    canvas = tk.Canvas(frame, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    main_inner = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=main_inner, anchor="nw")
    
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    main_inner.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    main_inner.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    main_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # Dictionaries for the state of the checkboxes.
    # In this demo, we do not have a top-level checkbox; categories are just labels.
    # Only subcategory checkboxes (table_vars) are interactive.
    category_vars = {}  # we won't use these in this simplified demo
    table_vars = {}
    
    def setup_filter(category_structure):
        for widget in main_inner.winfo_children():
            widget.destroy()
        
        tk.Label(main_inner, text="Filtre:", font=("Arial", 12, "bold"), bg="white").pack(anchor="w", padx=5, pady=5)
        
        def on_subcat_toggle():
            on_filter_callback()
        
        # For each category, create a label and then its subcategory checkboxes
        for cat, subcats in sorted(category_structure.items()):
            # Category label
            tk.Label(main_inner, text=cat, font=("Arial", 10, "bold", "underline"), bg="white")\
                .pack(anchor="w", padx=5, pady=(5, 2))
            
            # Subcategories frame (always visible)
            subcat_frame = tk.Frame(main_inner, bg="white")
            subcat_frame.pack(anchor="w", fill="x", padx=20, pady=2)
            
            for class_id, table_name in sorted(subcats, key=lambda x: x[1]):
                # Create a BooleanVar for each subcategory checkbox, default is unchecked.
                table_vars[class_id] = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(
                    subcat_frame,
                    text=table_name,
                    variable=table_vars[class_id],
                    bg="white",
                    command=on_subcat_toggle
                )
                chk.pack(anchor="w", pady=2)
        
        # Reset button to clear all selections
        tk.Button(
            main_inner,
            text="Resetovať filtre",
            command=lambda: (
                [v.set(False) for v in table_vars.values()],
                on_filter_callback()
            )
        ).pack(anchor="w", padx=5, pady=10)
    
    return frame, setup_filter, category_vars, table_vars

########################################################################
# 4) MAIN GUI DEMO
########################################################################

def run_gui_demo():
    # Create the in-memory demo database
    conn = create_in_memory_db()
    cursor = conn.cursor()
    
    root = tk.Tk()
    root.title("Demo - Hierarchical Filter Panel")
    root.geometry("1200x700")
    
    container = tk.Frame(root)
    container.pack(fill=tk.BOTH, expand=True)
    
    # Filter panel callback
    def on_filter_changed():
        apply_filters(cursor, table_vars, name_entry, tree)
    
    # Create filter panel on the left
    filter_frame, setup_filter, category_vars, table_vars = create_filter_panel(container, on_filter_changed)
    filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    
    # Build category structure from the in-memory DB
    category_structure = {}
    cursor.execute("SELECT id, hlavna_kategoria, nazov_tabulky FROM class")
    for class_id, cat, subcat in cursor.fetchall():
        category_structure.setdefault(cat, []).append((class_id, subcat))
    
    # Debug prints for categories
    print("=== Debug: category_structure ===")
    for c, subs in category_structure.items():
        print(f"Category '{c}': {subs}")
    
    setup_filter(category_structure)
    
    # Main content on the right
    main_frame = tk.Frame(container)
    main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Top frame for the search box
    top_frame = tk.Frame(main_frame)
    top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
    
    tk.Label(top_frame, text="Vyhľadávanie:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    name_entry = tk.Entry(top_frame, width=30)
    name_entry.pack(side=tk.LEFT, padx=5)
    name_entry.bind("<KeyRelease>", lambda e: on_filter_changed())
    
    # Treeview for products
    tree_frame = tk.Frame(main_frame)
    tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    columns = ("produkt", "jednotky", "dodavatel", "odkaz", "koeficient", "nakup_materialu", "cena_prace")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, anchor="center")
    tree.pack(fill=tk.BOTH, expand=True)
    
    # Initially apply filter (which shows all products because no subcategory is checked)
    on_filter_changed()
    
    root.mainloop()
    conn.close()

if __name__ == "__main__":
    run_gui_demo()
