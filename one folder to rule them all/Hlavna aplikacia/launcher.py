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
    lb = Listbox(root, width=60, height=20)
    lb.pack(fill=tk.BOTH, expand=True)

    def on_open(evt):
        sel = lb.curselection()
        if not sel:
            return
        json_file = lb.get(sel[0])
        json_path = os.path.join(projects_dir, json_file)

        # Close the archive window
        root.destroy()

        # Launch the real GUI, passing our base_dir (so it knows where its files live)
        import gui
        gui.start(base_dir, json_path)

    lb.bind("<Double-1>", on_open)

    # Populate the list with all .json files sorted by modified time descending
    files = [
        f for f in os.listdir(projects_dir)
        if f.lower().endswith(".json")
    ]
    files.sort(
        key=lambda f: os.path.getmtime(os.path.join(projects_dir, f)),
        reverse=True
    )
    for f in files:
        lb.insert(tk.END, f)

    root.mainloop()


if __name__ == "__main__":
    main()
