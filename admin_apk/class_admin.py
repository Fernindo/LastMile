import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import psycopg2
import unicodedata
import re

def create_class_form(parent, refresh_callback=None):
    window = tk.Toplevel(parent)
    window.title("Vytvoriť / Odstrániť triedu")
    window.geometry("450x300")
    window.grab_set()

    allowed_categories = ["SK", "EZS", "CCTV"]

    tk.Label(window, text="Hlavná kategória").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    kat_combo = ttk.Combobox(window, values=allowed_categories, state="readonly", width=30)
    kat_combo.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(window, text="Názov tabuľky").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    nazov_entry = tk.Entry(window, width=30)
    nazov_entry.grid(row=1, column=1, padx=10, pady=10)

    tk.Label(window, text="Zoznam existujúcich tried").grid(row=3, column=0, columnspan=2)
    triedy_combo = ttk.Combobox(window, width=42, state="readonly")
    triedy_combo.grid(row=4, column=0, columnspan=2, padx=10)

    def generate_id(nazov):
        nfkd = unicodedata.normalize('NFKD', nazov)
        ascii_text = nfkd.encode('ASCII', 'ignore').decode('utf-8')
        return re.sub(r'\s+', '_', ascii_text.strip().lower())

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
        classes = cur.fetchall()
        triedy_combo["values"] = [f"{c[0]} - {c[1]}" for c in classes]
        cur.close()
        conn.close()


    def save_class():
        kategoria = kat_combo.get().strip()
        nazov = nazov_entry.get().strip()

        if not kategoria or not nazov:
            messagebox.showwarning("Chyba", "Vyplň všetky polia.")
            return

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

            messagebox.showinfo("Hotovo", f"Trieda bola vytvorená s ID: {new_id}")
            nazov_entry.delete(0, tk.END)
            load_classes()
            if refresh_callback:
                refresh_callback()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))


    def delete_class():
        selected = triedy_combo.get()
        if not selected:
            messagebox.showwarning("Chyba", "Vyber triedu na odstránenie.")
            return

        class_id = selected.split(" - ")[0]

        # Overenie admin hesla
        password = simpledialog.askstring("Overenie", "Zadaj heslo admina:", show="*")
        if not password:
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users u JOIN roles r ON u.role_id = r.id WHERE u.password = %s AND r.name = 'admin'", (password,))
            admin_check = cur.fetchone()

            if not admin_check:
                messagebox.showerror("Neúspech", "Nesprávne heslo alebo nie si admin.")
                cur.close()
                conn.close()
                return

            # Odstrániť najprv produkty
            cur.execute("DELETE FROM produkty WHERE class_id = %s", (class_id,))
            cur.execute("DELETE FROM class WHERE id = %s", (class_id,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Hotovo", f"Trieda '{selected}' bola odstránená.")
            load_classes()
            if refresh_callback:
                refresh_callback()
        except Exception as e:
            messagebox.showerror("Chyba", str(e))

    tk.Button(window, text="Vytvoriť triedu", command=save_class).grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(window, text="Odstrániť vybranú triedu", command=delete_class, fg="red").grid(row=5, column=0, columnspan=2, pady=10)

    load_classes()
    window.mainloop()
