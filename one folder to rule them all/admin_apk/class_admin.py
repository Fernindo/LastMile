import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

def create_table_form(parent, refresh_callback=None):
    window = tk.Toplevel(parent)
    window.title("Editor tabuliek a kategórií")
    window.geometry("900x600")
    window.grab_set()

    sort_column = "nazov_tabulky"
    sort_reverse = False

    def get_connection():
        return psycopg2.connect(
            host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
            port=5432,
            user="neondb_owner",
            password="npg_aYC4yHnQIjV1",
            dbname="neondb",
            sslmode="require"
        )

    left_frame = tk.Frame(window)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    right_frame = tk.Frame(window)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    form_frame = tk.LabelFrame(left_frame, text="Pridať novú tabuľku", padx=10, pady=10)
    form_frame.pack(fill="x", pady=10)

    tk.Label(form_frame, text="Hlavná kategória").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    kat_combo = ttk.Combobox(form_frame, width=20, state="readonly")
    kat_combo.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(form_frame, text="Názov tabuľky").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    nazov_entry = tk.Entry(form_frame, width=22)
    nazov_entry.grid(row=1, column=1, padx=5, pady=5)

    def save_table():
        kategoria = kat_combo.get().strip()
        nazov = nazov_entry.get().strip()

        if not kategoria or not nazov:
            return messagebox.showwarning("Chyba", "Vyplň všetky polia.")
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO class (hlavna_kategoria, nazov_tabulky) VALUES (%s, %s) RETURNING id",
                (kategoria, nazov)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Hotovo", f"Tabuľka vytvorená s ID: {new_id}")
            nazov_entry.delete(0, tk.END)
            load_tables()
            if refresh_callback:
                refresh_callback()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    tk.Button(form_frame, text="Vytvoriť tabuľku", command=save_table).grid(row=2, column=0, columnspan=2, pady=10)

    cat_frame = tk.LabelFrame(left_frame, text="Hlavné kategórie", padx=10, pady=10)
    cat_frame.pack(fill="x", pady=10)

    tk.Label(cat_frame, text="Nová kategória").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    new_cat_entry = tk.Entry(cat_frame, width=22)
    new_cat_entry.grid(row=0, column=1, padx=5, pady=5)

    def pridaj_kategoriu():
        nazov = new_cat_entry.get().strip()
        if not nazov:
            return messagebox.showwarning("Chyba", "Zadaj názov kategórie.")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO class (hlavna_kategoria, nazov_tabulky) VALUES (%s, '')", (nazov,))
        conn.commit()
        cur.close()
        conn.close()
        new_cat_entry.delete(0, tk.END)
        load_categories()
        load_tables()

    tk.Button(cat_frame, text="Pridať kategóriu", command=pridaj_kategoriu).grid(row=1, column=0, columnspan=2, pady=10)

    cat_listbox = tk.Listbox(cat_frame, height=6, exportselection=False)
    cat_listbox.grid(row=2, column=0, columnspan=2, sticky="we", pady=5)

    def delete_category():
        selected = cat_listbox.curselection()
        if not selected:
            return
        item = cat_listbox.get(selected[0])
        kat = item.strip()
        confirm = messagebox.askyesno("Potvrdenie", f"Naozaj chceš zmazať kategóriu: {kat}?")
        if not confirm:
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM class WHERE hlavna_kategoria = %s", (kat,))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("Hotovo", f"Kategória '{kat}' bola vymazaná.")
        load_categories()
        load_tables()

    tk.Button(cat_frame, text="Vymazať kategóriu", fg="red", command=delete_category).grid(row=3, column=0, columnspan=2, pady=5)

    table_tree = ttk.Treeview(right_frame, columns=("id", "hlavna_kategoria", "nazov"), show="headings")
    table_tree.heading("id", text="ID", command=lambda: sort_tables("id"))
    table_tree.heading("hlavna_kategoria", text="Hlavná kategória", command=lambda: sort_tables("hlavna_kategoria"))
    table_tree.heading("nazov", text="Názov tabuľky", command=lambda: sort_tables("nazov_tabulky"))
    table_tree.column("id", width=50, anchor="center")
    table_tree.column("hlavna_kategoria", width=150, anchor="center")
    table_tree.column("nazov", width=250)
    table_tree.pack(fill=tk.BOTH, expand=True)

    tk.Button(right_frame, text="🗑️ Vymazať vybranú tabuľku", fg="red", command=lambda: delete_table_by_id()).pack(pady=10)

    def delete_table_by_id():
        selected = table_tree.selection()
        if not selected:
            return
        item = table_tree.item(selected[0])
        table_id = item["values"][0]
        nazov = item["values"][2]

        confirm = messagebox.askyesno("Potvrdenie", f"Naozaj chceš zmazať tabuľku: {nazov}?")
        if not confirm:
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM produkt_class WHERE class_id = %s", (table_id,))
        cur.execute("DELETE FROM class WHERE id = %s", (table_id,))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("Hotovo", f"Tabuľka '{nazov}' bola vymazaná.")
        load_tables()
        if refresh_callback:
            refresh_callback()

    def sort_tables(column):
        nonlocal sort_column, sort_reverse
        if sort_column == column:
            sort_reverse = not sort_reverse
        else:
            sort_column = column
            sort_reverse = False
        load_tables()

    def load_categories():
        cat_listbox.delete(0, tk.END)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT hlavna_kategoria FROM class ORDER BY hlavna_kategoria")
        categories = cur.fetchall()
        cat_listbox.insert(tk.END, *[cat[0] for cat in categories])
        kat_combo["values"] = [cat[0] for cat in categories]
        if categories:
            kat_combo.set(categories[0][0])
        cur.close()
        conn.close()

    def load_tables():
        for i in table_tree.get_children():
            table_tree.delete(i)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, hlavna_kategoria, nazov_tabulky
            FROM class
            WHERE nazov_tabulky != ''
            ORDER BY {sort_column} {'DESC' if sort_reverse else 'ASC'}
        """)
        for row in cur.fetchall():
            table_tree.insert("", "end", values=row)
        cur.close()
        conn.close()

    load_categories()
    load_tables()
    window.mainloop()
