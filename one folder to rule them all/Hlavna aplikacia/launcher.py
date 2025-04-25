import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

# Determine the project directory
if getattr(sys, "frozen", False):
    # Running as launcher.exe
    project_dir = os.getcwd()
else:
    # Running as script
    project_dir = os.path.dirname(os.path.abspath(__file__))

# Make sure the JSON archive folder exists
json_dir = os.path.join(project_dir, "projects")
if not os.path.isdir(json_dir):
    messagebox.showerror("Error", "Missing 'projects' folder.")
    sys.exit(1)

def open_item(evt):
    """Launched when the user double-clicks a JSON in the listbox."""
    sel = lb.curselection()
    if not sel:
        return
    fn   = lb.get(sel[0])
    full = os.path.join(json_dir, fn)

    # Launch the frozen GUI executable, passing project_dir and JSON path
    gui_exe = os.path.join(project_dir, "gui.exe")
    subprocess.Popen([
        gui_exe,
        project_dir,
        full
    ], cwd=project_dir)

# Build the Archive window
root = tk.Tk()
root.title("Archive — " + os.path.basename(project_dir))

lb = tk.Listbox(root, width=60, height=20)
lb.pack(fill=tk.BOTH, expand=True)
lb.bind("<Double-1>", open_item)

# Populate with all .json files, newest first
files = sorted(
    [f for f in os.listdir(json_dir) if f.lower().endswith(".json")],
    key=lambda f: os.path.getmtime(os.path.join(json_dir, f)),
    reverse=True
)
for f in files:
    lb.insert(tk.END, f)

root.mainloop()
