
import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

def update_product_form(parent):
    window = tk.Toplevel(parent)
    window.title("Upraviť produkt")
    window.geometry("600x600")

    labels = ["Produkt", "Jednotky", "Nákup materiálu", "Koeficient", "Cena práce", "Dodávateľ", "Odkaz"]
    entries = {}

    for i, label in enumerate(labels):
        tk.Label(window, text=label).grid(row=i+2, column=0, sticky="e", padx=10, pady=5)
        entry = tk.Entry(window, width=40)
        entry.grid(row=i+2, column=1, padx=10, pady=5)
        entries[label] = entry

    tk.Label(window, text="Trieda").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    class_combo = ttk.Combobox(window, width=40, state="readonly")
    class_combo.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(window, text="Produkt").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    product_combo = ttk.Combobox(window, width=40, state="readonly")
    product_combo.grid(row=1, column=1, padx=10, pady=5)

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
        cur.execute("SELECT id, nazov_tabulky FROM class")
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
        cur.execute("SELECT produkt FROM produkty WHERE class_id = %s", (class_id,))
        products = [r[0] for r in cur.fetchall()]
        product_combo['values'] = products
        cur.close()
        conn.close()

    def fill_data(event=None):
        if not product_combo.get():
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT produkt, jednotky, nakup_materialu, koeficient, cena_prace, dodavatel, odkaz FROM produkty WHERE produkt = %s", (product_combo.get(),))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result:
            for i, label in enumerate(labels):
                entries[label].delete(0, tk.END)
                entries[label].insert(0, result[i])

    def save_update():
        data = [entries[label].get() for label in labels]
        product_name = product_combo.get()
        if not product_name or not all(data):
            messagebox.showerror("Chyba", "Vyplň všetky údaje")
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE produkty
            SET produkt=%s, jednotky=%s, nakup_materialu=%s, koeficient=%s,
                cena_prace=%s, dodavatel=%s, odkaz=%s
            WHERE produkt=%s
        """, (*data, product_name))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("OK", "Produkt bol aktualizovaný")
        window.destroy()

    class_combo.bind("<<ComboboxSelected>>", load_products)
    product_combo.bind("<<ComboboxSelected>>", fill_data)

    tk.Button(window, text="Uložiť zmeny", command=save_update).grid(row=len(labels)+2, columnspan=2, pady=20)
    load_classes()
    window.mainloop()
