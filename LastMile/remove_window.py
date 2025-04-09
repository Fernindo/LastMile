import tkinter as tk
from tkinter import ttk, messagebox

def open_remove_window(conn, cursor, tab_names, tree_columns):
    remove_win = tk.Toplevel()
    remove_win.title("Odstrániť záznamy")
    remove_win.state("zoomed")

    top_frame = tk.Frame(remove_win)
    top_frame.pack(fill=tk.X, padx=20, pady=10)

    tk.Label(top_frame, text="Vyber tabuľku:").pack(side=tk.LEFT)
    remove_table_var = tk.StringVar()
    remove_combo = ttk.Combobox(top_frame, textvariable=remove_table_var, values=[""] + tab_names, state="readonly")
    remove_combo.pack(side=tk.LEFT, padx=10)

    tk.Label(top_frame, text="Vyhľadávanie:").pack(side=tk.LEFT, padx=(30, 5))
    search_var = tk.StringVar()
    search_entry = tk.Entry(top_frame, textvariable=search_var)
    search_entry.pack(side=tk.LEFT)

    table_frame = tk.Frame(remove_win)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    columns_with_action = ("action",) + tree_columns

    remove_scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")
    remove_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    tree_remove = ttk.Treeview(
        table_frame,
        columns=columns_with_action,
        show="headings",
        xscrollcommand=remove_scroll_x.set
    )
    remove_scroll_x.config(command=tree_remove.xview)
    tree_remove.pack(fill=tk.BOTH, expand=True)

    tree_remove.heading("action", text="X")
    tree_remove.column("action", width=30, anchor="center")

    # Bold štýl pre názvy tabuliek
    style = ttk.Style()
    style.configure("Treeview", rowheight=24)
    tree_remove.tag_configure("bold", font=('Segoe UI', 10, 'bold'))

    sort_directions = {col: True for col in tree_columns}

    for col in tree_columns:
        def sortby(colname=col):
            items = [(tree_remove.set(k, colname), k) for k in tree_remove.get_children('')]
            is_numeric = all(val.replace('.', '', 1).isdigit() for val, _ in items if val != '')
            reverse = not sort_directions[colname]
            sort_directions[colname] = reverse
            items.sort(key=lambda t: float(t[0]) if is_numeric and t[0] else t[0], reverse=reverse)
            for index, (_, k) in enumerate(items):
                tree_remove.move(k, '', index)
        tree_remove.heading(col, text=col, command=sortby)
        tree_remove.column(col, anchor="center")

    def load_remove_table(*args):
        tree_remove.delete(*tree_remove.get_children())
        selected_tab = remove_table_var.get()
        filter_text = search_var.get().lower()

        tabs_to_load = [selected_tab] if selected_tab else tab_names

        for tab in tabs_to_load:
            try:
                cursor.execute(f"SELECT * FROM {tab}")
                rows = cursor.fetchall()

                visible_rows = [row for row in rows if filter_text in str(row).lower()]
                if not visible_rows:
                    continue

                # Nadpis tabuľky – len v druhom stĺpci (id), ostatné prázdne
                if not selected_tab:
                    heading_values = [""] * len(columns_with_action)
                    heading_values[1] = tab
                    tree_remove.insert("", tk.END, values=heading_values, tags=("bold",))

                for row in visible_rows:
                    values = ("X",) + row
                    tree_remove.insert("", tk.END, values=values)

            except Exception as err:
                messagebox.showerror("Chyba pri čítaní", str(err))

    def handle_click(event):
        item_id = tree_remove.identify_row(event.y)
        col = tree_remove.identify_column(event.x)

        if not item_id:
            return

        row_values = tree_remove.item(item_id, "values")

        # Ak klikáme na bold hlavičku, ignorujeme
        if "bold" in tree_remove.item(item_id, "tags"):
            return

        if col == '#1':  # Kliknutie na "X"
            record_id = row_values[1]
            table = remove_table_var.get()

            # Ak nie je tabuľka vybraná, zisti ju z bold hlavičky nad záznamom
            if not table:
                table = find_table_name_above(tree_remove, item_id)
                if not table:
                    messagebox.showwarning("Chyba", "Nepodarilo sa určiť tabuľku pre záznam.")
                    return

            if messagebox.askyesno("Potvrdiť vymazanie", f"Naozaj chceš vymazať záznam ID {record_id} z tabuľky {table}?"):
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE id = %s", (record_id,))
                    conn.commit()
                    load_remove_table()
                    messagebox.showinfo("Vymazané", "Záznam bol úspešne vymazaný")
                except Exception as e:
                    messagebox.showerror("Chyba", str(e))

    def find_table_name_above(treeview, item_id):
        """Nájde názov tabuľky nad daným itemom (z bold riadku)."""
        index = treeview.index(item_id)
        children = treeview.get_children()
        for i in reversed(range(0, index)):
            tags = treeview.item(children[i], "tags")
            if "bold" in tags:
                name = treeview.item(children[i], "values")[1]
                return name
        return None

    tree_remove.bind("<Button-1>", handle_click)
    remove_combo.bind("<<ComboboxSelected>>", load_remove_table)
    search_var.trace_add("write", load_remove_table)

    # Prvotné načítanie všetkých tabuliek
    remove_combo.current(0)
    load_remove_table()
