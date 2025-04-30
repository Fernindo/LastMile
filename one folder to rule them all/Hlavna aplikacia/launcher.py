# launcher.py

import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess

# ─── 1) Where are we? ───────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    # running as launcher.exe
    base_dir = os.getcwd()
else:
    # running as script
    base_dir = os.path.dirname(os.path.abspath(__file__))

# ─── 2) Ensure projects/ exists ─────────────────────────────────────────────
json_dir = os.path.join(base_dir, "projects")
if not os.path.isdir(json_dir):
    messagebox.showerror("Error", "Missing 'projects' folder next to launcher.exe")
    sys.exit(1)

# ─── 3) Build the Archive window ─────────────────────────────────────────────
root = tk.Tk()
root.title(f"Archive — {os.path.basename(base_dir)}")

lb = tk.Listbox(root, width=60, height=20)
lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Populate with .json files, newest first
files = sorted(
    [f for f in os.listdir(json_dir) if f.lower().endswith(".json")],
    key=lambda f: os.path.getmtime(os.path.join(json_dir, f)),
    reverse=True
)
for f in files:
    lb.insert(tk.END, f)

def on_double_click(event):
    sel = lb.curselection()
    if not sel:
        return
    chosen = lb.get(sel[0])
    root.destroy()

    json_path = os.path.join(json_dir, chosen)
    gui_exe   = os.path.join(base_dir, "gui.exe")
    if not os.path.isfile(gui_exe):
        messagebox.showerror("Error", f"'gui.exe' not found in:\n{base_dir}")
        sys.exit(1)

    # Launch the GUI executable with arguments: <project_folder> <json_path>
    subprocess.Popen([gui_exe, base_dir, json_path], cwd=base_dir)
    sys.exit(0)

lb.bind("<Double-1>", on_double_click)
root.mainloop()
