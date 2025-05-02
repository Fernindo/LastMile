import os
import sys
import json
import shutil
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, filedialog
import launcher
import excel_processing
import gui
import gui_functions
import filter_panel
import notes_panel

# ─── Default JSON template ────────────────────────────────────────────────
DEFAULT_TEMPLATE = {"data": "Default session content."}

# ─── Files to copy into each new project ──────────────────────────────────
SCRIPT_FILES = [
    "gui.py",
    "gui_functions.py",
    "filter_panel.py",
    "notes_panel.py",
    "excel_processing.py",
]

# ─── Browse for a destination directory ────────────────────────────────────
def browse_destination():
    folder = filedialog.askdirectory(
        title="Select destination folder",
        initialdir=dest_var.get() or os.path.expanduser("~")
    )
    if folder:
        dest_var.set(folder)

# ─── Create a new project ───────────────────────────────────────────
def create_project():
    name = name_var.get().strip()
    dest = dest_var.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a project name.")
        return
    if not dest or not os.path.isdir(dest):
        messagebox.showerror("Error", "Please choose a valid destination folder.")
        return

    project_dir = os.path.join(dest, name)
    if os.path.exists(project_dir):
        messagebox.showerror("Error", f"Folder '{project_dir}' already exists.")
        return

    try:
        # 1) Create the project folders
        os.makedirs(project_dir)
        json_dir = os.path.join(project_dir, "projects")
        os.makedirs(json_dir)

        # 2) Save the initial JSON (not encrypted)
        json_data = json.dumps(DEFAULT_TEMPLATE, ensure_ascii=False, indent=2)
        json_name = f"{name}.json"
        json_path = os.path.join(json_dir, json_name)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_data)

        # 3) Copy all the helper .py files
        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        for fname in SCRIPT_FILES:
            src = os.path.join(base_dir, fname)
            dst = os.path.join(project_dir, fname)
            if os.path.exists(src):
                shutil.copy(src, dst)

        # 4) Copy the launcher.exe (renaming to <project>.exe)
        prebuilt = os.path.join(base_dir, "launcher.exe")
        exe_name = name + (".exe" if os.name == "nt" else "")
        target = os.path.join(project_dir, exe_name)
        if not os.path.exists(prebuilt):
            messagebox.showerror("Error",
                "Missing 'launcher.exe'.\nMake sure it sits next to this script.")
            return
        shutil.copy(prebuilt, target)

        # 5) Success!
        messagebox.showinfo("Success",
            f"Project '{name}' created at:\n\n{project_dir}\n\n"
            f"• JSON file: projects/{json_name}\n"
            f"• Launcher:  {exe_name}")
        root.destroy()

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ─── GUI Layout ─────────────────────────────────────────────────────────────
style = Style(theme="litera")
root  = style.master
root.title("Create New Project")
root.resizable(False, False)
root.geometry("520x200")

frm = tb.Frame(root, padding=20)
frm.pack(fill="both", expand=True)

# destination
tb.Label(frm, text="Destination Folder:", font=("Segoe UI",10))\
  .grid(row=0, column=0, sticky="e", padx=5, pady=5)
dest_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
tb.Entry(frm, textvariable=dest_var, width=35)\
  .grid(row=0, column=1, padx=5, pady=5)
tb.Button(frm, text="Browse…", bootstyle="secondary", command=browse_destination)\
  .grid(row=0, column=2, padx=5)

# project name
tb.Label(frm, text="Project Name:", font=("Segoe UI",10))\
  .grid(row=1, column=0, sticky="e", padx=5, pady=5)
name_var = tk.StringVar()
tb.Entry(frm, textvariable=name_var, width=35)\
  .grid(row=1, column=1, columnspan=2, padx=5, pady=5)

# create button
tb.Button(frm, text="Create Project", bootstyle="success", width=20,
          command=create_project)\
  .grid(row=2, column=0, columnspan=3, pady=15)

root.mainloop()
