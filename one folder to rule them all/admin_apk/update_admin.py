import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

def update_product_form(parent):
    window = tk.Toplevel(parent)
    window.title("Upraviť produkt")
    window.geometry("1200x600")

    left_frame = tk.Frame(window)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    right_frame = tk.Frame(window)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    labels = [
        "Produkt", "Jednotky", "Nákup materiálu",
        "Koeficient materiál", "Koeficient práca",
        "Cena práce", "Dodávateľ", "Odkaz"
    ]
    entries = {}

    tk.Label(left_frame, text="Trieda").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    class_combo = ttk.Combobox(left_frame, width=40, state="readonly")
    class_combo.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(left_frame, text="Produkt").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    product_combo = ttk.Combobox(left_frame, width=40, state="readonly")
    product_combo.grid(row=1, column=1, padx=5, pady=5)

    for i, label in enumerate(labels):
        tk.Label(left_frame, text=label).grid(row=i+2, column=0, sticky="e", padx=5, pady=5)
        entry = tk.Entry(left_frame, width=40)
        entry.grid(row=i+2, column=1, padx=5, pady=5)
        entries[label] = entry

    tree = ttk.Treeview(right_frame, columns=labels + ["class_id"], show="headings")
    for label in labels:
        tree.heading(label, text=label)
        tree.column(label, anchor="center")
    tree.heading("class_id", text="class_id")
    tree.column("class_id", width=0, stretch=False)  # Skryjeme stĺpec class_id
    tree.pack(fill=tk.BOTH, expand=True)

    def get_connection():
        return psycopg2.connect(
            host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
            port=5432,
            user="neondb_owner",
            password="npg_aYC4yHnQIjV1",
            dbname="neondb",
            sslmode="require"
        )

    def load_classes():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nazov_tabulky FROM class ORDER BY nazov_tabulky")
        values = [f"{r[0]} - {r[1]}" for r in cur.fetchall()]
        class_combo['values'] = values
        cur.close()
        conn.close()

    def load_products(event=None):
        product_combo.set('')
        product_combo['values'] = []
        if not class_combo.get():
            return
        class_id = class_combo.get().split(" - ")[0]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.produkt FROM produkty p
            JOIN produkt_class pc ON p.id = pc.produkt_id
            WHERE pc.class_id = %s
        """, (class_id,))
        products = [r[0] for r in cur.fetchall()]
        product_combo['values'] = products
        cur.close()
        conn.close()

    def fill_data(event=None):
        if not product_combo.get():
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT produkt, jednotky, nakup_materialu,
                   koeficient_material, koeficient_prace,
                   cena_prace, dodavatel, odkaz 
            FROM produkty WHERE produkt = %s
        """, (product_combo.get(),))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            for i, label in enumerate(labels):
                entries[label].delete(0, tk.END)
                entries[label].insert(0, result[i])

    def save_update():
        data = [entries[label].get().strip() for label in labels]
        product_name = product_combo.get()
        if not product_name or not all(data):
            messagebox.showerror("Chyba", "Vyplň všetky údaje")
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE produkty
            SET produkt=%s, jednotky=%s, nakup_materialu=%s,
                koeficient_material=%s, koeficient_prace=%s,
                cena_prace=%s, dodavatel=%s, odkaz=%s
            WHERE produkt=%s
        """, (*data, product_name))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("OK", "Produkt bol aktualizovaný")
        window.destroy()

    def load_table_data():
        tree.delete(*tree.get_children())
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.nazov_tabulky, p.produkt, p.jednotky, p.nakup_materialu, 
                   p.koeficient_material, p.koeficient_prace,
                   p.cena_prace, p.dodavatel, p.odkaz, c.id
            FROM produkty p
            JOIN produkt_class pc ON p.id = pc.produkt_id
            JOIN class c ON c.id = pc.class_id
            ORDER BY c.nazov_tabulky, p.id
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        current_class = None
        for row in rows:
            class_name = row[0]
            if class_name != current_class:
                current_class = class_name
                tree.insert("", "end", values=("", *[""]*len(labels), ""), tags=("header",))
                tree.insert("", "end", values=(f"-- {class_name} --", *[""]*(len(labels)-1), ""), tags=("header",))
            tree.insert("", "end", values=row[1:])

        tree.tag_configure("header", font=("Arial", 10, "bold"))

    def on_tree_select(event):
        item = tree.selection()
        if not item:
            return
        values = tree.item(item)["values"]
        if not values or str(values[0]).startswith("--"):
            return
        for i, label in enumerate(labels):
            entries[label].delete(0, tk.END)
            entries[label].insert(0, values[i])
        product_combo.set(values[0])
        class_id = values[-1]
        for val in class_combo['values']:
            if val.startswith(f"{class_id} -"):
                class_combo.set(val)
                break

    class_combo.bind("<<ComboboxSelected>>", load_products)
    product_combo.bind("<<ComboboxSelected>>", fill_data)
    tree.bind("<<TreeviewSelect>>", on_tree_select)

    tk.Button(left_frame, text="Uložiť zmeny", command=save_update).grid(row=len(labels)+2, columnspan=2, pady=20)

    load_classes()
    load_table_data()
    window.mainloop()
