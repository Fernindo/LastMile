import sys
import os
import tkinter as tk
from tkinter import messagebox, Listbox, Scrollbar, Frame, Label, Button

def main():
    # Determine base directory (where launcher.py or launcher.exe lives)
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Look for the "projects" folder
    projects_dir = os.path.join(base_dir, "projects")
    if not os.path.isdir(projects_dir):
        messagebox.showerror("Chyba", "Chýba priečinok 'projects' pri launcheri.")
        sys.exit(1)

    # Build main window
    root = tk.Tk()
    root.title("📁 Archív projektov")
    root.geometry("420x500")
    root.configure(bg="#f0f4f8")

    # Title and description
    Label(root, text="Vyber projekt pre otvorenie", font=("Segoe UI", 14, "bold"), bg="#f0f4f8").pack(pady=(20, 10))
    
    # Frame for listbox + scrollbar
    list_frame = Frame(root, bg="#f0f4f8")
    list_frame.pack(fill="both", expand=True, padx=20, pady=10)

    lb = Listbox(
        list_frame,
        width=40,
        height=20,
        font=("Segoe UI", 10),
        bg="white",
        fg="black",
        highlightthickness=1,
        highlightcolor="#0078D7",
        selectbackground="#0078D7",     # Výrazné pozadie pri výbere
        selectforeground="white",       # Biele písmo na výbere
        activestyle="none"
    )
    lb.pack(side="left", fill="both", expand=True)

    sb = Scrollbar(list_frame, orient="vertical", command=lb.yview)
    sb.pack(side="right", fill="y")
    lb.config(yscrollcommand=sb.set)

    # Close button
    Button(root, text="Zavrieť", command=root.destroy, font=("Segoe UI", 10), bg="#e0e0e0", relief="flat").pack(pady=(5, 15))

    # On double click
    def on_open(evt):
        sel = lb.curselection()
        if not sel:
            return
        display = lb.get(sel[0]).strip()

        if " | " in display:
            date_part, base = [s.strip() for s in display.split("|", 1)]
            json_file = f"{base}_{date_part}.json"
        else:
            base = display
            json_file = f"{base}.json"

        json_path = os.path.join(projects_dir, json_file)
        root.destroy()
        import gui
        gui.start(base_dir, json_path)

    lb.bind("<Double-1>", on_open)

    # Load JSON files
    files = [f for f in os.listdir(projects_dir) if f.lower().endswith(".json")]
    files.sort(key=lambda f: os.path.getmtime(os.path.join(projects_dir, f)), reverse=True)

    for f in files:
        name, _ = os.path.splitext(f)
        if "_" in name:
            base, date_part = name.split("_", 1)
            display = f"{date_part} | {base}"
        else:
            display = name
        lb.insert(tk.END, display)

    root.mainloop()

if __name__ == "__main__":
    main()
