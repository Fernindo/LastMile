import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2

def insert_product_form(parent):
    window = tk.Toplevel(parent)
    window.title("Pridať produkt")
    window.geometry("600x700")

    labels = [
        "Produkt", "Jednotky", "Nákup materiálu",
        "Koeficient materiál", "Koeficient práca",
        "Cena práce", "Dodávateľ", "Odkaz"
    ]
    entries = {}

    for i, label in enumerate(labels):
        tk.Label(window, text=label).grid(row=i, column=0, sticky="e", padx=10, pady=5)
        entry = tk.Entry(window, width=40)
        entry.grid(row=i, column=1, padx=10, pady=5)
        entries[label] = entry

    tk.Label(window, text="Kategórie (min. 1)").grid(row=len(labels), column=0, sticky="ne", padx=10, pady=5)

    category_frame = tk.Frame(window)
    category_frame.grid(row=len(labels), column=1, padx=10, pady=5, sticky="w")

    category_combos = []

    def get_connection():
        return psycopg2.connect(
            host="ep-holy-bar-a2bpx2sc-pooler.eu-central-1.aws.neon.tech",
            port=5432,
            user="neondb_owner",
            password="npg_aYC4yHnQIjV1",
            dbname="neondb",
            sslmode="require"
        )

    def load_all_classes():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nazov_tabulky FROM class ORDER BY nazov_tabulky")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [f"{row[0]} - {row[1]}" for row in rows]

    def remove_combobox(frame, combo):
        if len(category_combos) > 1:
            frame.destroy()
            category_combos.remove(combo)
        else:
            messagebox.showwarning("Upozornenie", "Musí byť aspoň jedna kategória.")

    def add_category_combobox(event=None):
        all_classes = load_all_classes()

        row_frame = tk.Frame(category_frame)
        row_frame.pack(anchor="w", pady=2)

        combo = ttk.Combobox(row_frame, width=35, state="readonly")
        combo["values"] = all_classes
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", add_category_combobox)
        category_combos.append(combo)

        # Pridať X len ak už existuje aspoň jeden combobox
        if len(category_combos) > 1:
            remove_button = tk.Button(row_frame, text="X", fg="red", width=2,
                                      command=lambda: remove_combobox(row_frame, combo))
            remove_button.pack(side="left", padx=5)

    def save():
        try:
            data = [entries[label].get().strip() for label in labels]
            if not all(data):
                messagebox.showerror("Chyba", "Vyplň všetky polia produktu")
                return

            class_ids = []
            for combo in category_combos:
                value = combo.get()
                if value:
                    class_id = value.split(" - ")[0]
                    if class_id not in class_ids:
                        class_ids.append(class_id)

            if not class_ids:
                messagebox.showerror("Chyba", "Vyber aspoň jednu kategóriu")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO produkty (
                    produkt, jednotky, nakup_materialu,
                    koeficient_material, koeficient_prace,
                    cena_prace, dodavatel, odkaz
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, data)
            produkt_id = cur.fetchone()[0]

            for class_id in class_ids:
                cur.execute("INSERT INTO produkt_class (produkt_id, class_id) VALUES (%s, %s)", (produkt_id, class_id))

            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("OK", "Produkt bol pridaný")
            window.destroy()

        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    add_category_combobox()

    tk.Button(window, text="Pridať produkt", command=save).grid(row=len(labels)+2, columnspan=2, pady=20)

    window.mainloop()
