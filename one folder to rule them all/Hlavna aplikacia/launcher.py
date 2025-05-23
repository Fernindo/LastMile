import sys
import os
import tkinter as tk
from tkinter import messagebox, Listbox

def main():
    # Determine base directory (where launcher.py or launcher.exe lives)
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Look for the "projects" folder next to us
    projects_dir = os.path.join(base_dir, "projects")
    if not os.path.isdir(projects_dir):
        messagebox.showerror(
            "Error",
            "Missing 'projects' folder next to the launcher."
        )
        sys.exit(1)

    # Build the archive window
    root = tk.Tk()
    root.title("Archive")
    lb = Listbox(root, width=40, height=20)
    lb.pack(fill=tk.BOTH, expand=True)

    def on_open(evt):
        sel = lb.curselection()
        if not sel:
            return
        display = lb.get(sel[0]).strip()

        if " | " in display:
            # format: "YYYY-MM-DD | basename"
            date_part, base = [s.strip() for s in display.split("|", 1)]
            json_file = f"{base}_{date_part}.json"
        else:
            # format: "basename" only
            base = display
            json_file = f"{base}.json"

        json_path = os.path.join(projects_dir, json_file)
        root.destroy()
        import gui
        gui.start(base_dir, json_path)

    lb.bind("<Double-1>", on_open)

    # Gather and sort .json files
    files = [f for f in os.listdir(projects_dir) if f.lower().endswith(".json")]
    files.sort(
        key=lambda f: os.path.getmtime(os.path.join(projects_dir, f)),
        reverse=True
    )

    # Populate list: show "date | basename" or just "basename"
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
