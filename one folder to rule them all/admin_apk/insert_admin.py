import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

def insert_product_form(parent):
    window = tk.Toplevel(parent)
    window.title("Pridať produkt")
    window.geometry("500x500")

    labels = ["Produkt", "Jednotky", "Nákup materiálu", "Koeficient", "Cena práce", "Dodávateľ", "Odkaz"]
    entries = {}

    for i, label in enumerate(labels):
        tk.Label(window, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=5)
        entry = tk.Entry(window, width=40)
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries[label] = entry

    tk.Label(window, text="Trieda").grid(row=len(labels), column=0, sticky="e", padx=10, pady=5)
    class_combo = ttk.Combobox(window, width=37, state="readonly")
    class_combo.grid(row=len(labels), column=1, padx=10, pady=5)

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
        class_combo["values"] = [f"{row[0]} - {row[1]}" for row in cur.fetchall()]
        cur.close()
        conn.close()

    def save():
        data = [entries[label].get() for label in labels]
        class_id = class_combo.get().split(" - ")[0] if class_combo.get() else ""
        if not all(data) or not class_id:
            messagebox.showerror("Chyba", "Vyplň všetky polia")
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO produkty (produkt, jednotky, nakup_materialu, koeficient, cena_prace, dodavatel, odkaz)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, data)
        produkt_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO produkt_class (produkt_id, class_id)
            VALUES (%s, %s)
        """, (produkt_id, class_id))
        conn.commit()
        cur.close()
        conn.close()
        messagebox.showinfo("OK", "Produkt bol pridaný")
        window.destroy()

    tk.Button(window, text="Pridať produkt", command=save).grid(row=len(labels)+1, columnspan=2, pady=20)
    load_classes()
    window.mainloop()
