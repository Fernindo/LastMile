import os
import sys
import json
import shutil
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, filedialog

# Default JSON template
DEFAULT_TEMPLATE = {"data": "Default session content."}

# Your helper scripts (these get copied into each new project folder)
SCRIPT_FILES = [
    
    "gui.py",
    "gui_functions.py",
    "filter_panel.py",
    "notes_panel.py",
    "excel_processing.py"
]

def browse_destination():
    folder = filedialog.askdirectory(
        title="Select destination folder",
        initialdir=dest_var.get() or os.path.expanduser("~")
    )
    if folder:
        dest_var.set(folder)

def create_project():
    name = name_var.get().strip()
    dest = dest_var.get().strip()                # <-- here we read into `dest`
    if not name:
        messagebox.showerror("Error", "Please enter a project name.")
        return
    if not dest or not os.path.isdir(dest):      # <-- we check `dest`, not `dist`
        messagebox.showerror("Error", "Please choose a valid destination folder.")
        return

    project_dir = os.path.join(dest, name)       # <-- build your path from `dest`
    if os.path.exists(project_dir):
        messagebox.showerror("Error", f"Folder '{project_dir}' already exists.")
        return

    try:
        # 1) Create folders
        os.makedirs(project_dir)
        json_dir = os.path.join(project_dir, "projects")
        os.makedirs(json_dir)

        # 2) Create the initial JSON
        json_path = os.path.join(json_dir, f"{name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TEMPLATE, f, ensure_ascii=False, indent=2)

        # 3) Copy your helper .py scripts
        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        for fname in SCRIPT_FILES:
            src = os.path.join(base_dir, fname)
            dst = os.path.join(project_dir, fname)
            if os.path.exists(src):
                shutil.copy(src, dst)

        # 4) Copy the prebuilt launcher.exe (rename to <project>.exe)
        prebuilt = os.path.join(base_dir, "launcher.exe")
        exe_name = name + (".exe" if os.name == "nt" else "")
        target = os.path.join(project_dir, exe_name)

        if not os.path.exists(prebuilt):
            messagebox.showerror(
                "Error",
                "Missing prebuilt 'launcher.exe'.\n"
                "Make sure launcher.exe is next to this app."
            )
            return

        shutil.copy(prebuilt, target)

        # 5) Done!
        messagebox.showinfo(
            "Success",
            f"Project '{name}' created at:\n\n{project_dir}\n\n"
            f"• JSON: projects/{name}.json\n"
            f"• Launcher: {exe_name}"
        )
        root.destroy()

    except Exception as e:
        messagebox.showerror("Error", str(e))


# --- GUI Setup ---
style = Style(theme="litera")
root = style.master
root.title("Create New Project")
root.resizable(False, False)
root.geometry("520x200")

frm = tb.Frame(root, padding=20)
frm.pack(fill="both", expand=True)

# Destination folder selector
tb.Label(frm, text="Destination Folder:", font=("Segoe UI", 10)).grid(
    row=0, column=0, sticky="e", padx=5, pady=5
)
dest_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
tb.Entry(frm, textvariable=dest_var, width=35).grid(
    row=0, column=1, padx=5, pady=5
)
tb.Button(frm, text="Browse…", bootstyle="secondary", command=browse_destination).grid(
    row=0, column=2, padx=5
)

# Project name
tb.Label(frm, text="Project Name:", font=("Segoe UI", 10)).grid(
    row=1, column=0, sticky="e", padx=5, pady=5
)
name_var = tk.StringVar()
tb.Entry(frm, textvariable=name_var, width=35).grid(
    row=1, column=1, columnspan=2, padx=5, pady=5
)

# Create button
tb.Button(
    frm,
    text="Create Project",
    bootstyle="success",
    width=20,
    command=create_project
).grid(row=2, column=0, columnspan=3, pady=15)

root.mainloop()
