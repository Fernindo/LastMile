import os
import sys
import json
import shutil
import subprocess
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, filedialog

# Default JSON template
DEFAULT_TEMPLATE = {"data": "Default session content."}

# Your helper scripts
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
        # 1) Create project folder
        os.makedirs(project_dir)
        # 2) Create 'projects' subfolder for JSONs
        json_dir = os.path.join(project_dir, "projects")
        os.makedirs(json_dir)
        # 3) Write the initial JSON
        json_path = os.path.join(json_dir, f"{name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TEMPLATE, f, ensure_ascii=False, indent=2)
        # 4) Copy helper scripts
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for fname in SCRIPT_FILES:
            src = os.path.join(base_dir, fname)
            dst = os.path.join(project_dir, fname)
            if os.path.exists(src):
                shutil.copy(src, dst)
        # 5) Write launcher.py
        launcher_code = f'''\
import os, sys, subprocess, tkinter as tk
from tkinter import messagebox

if getattr(sys, "frozen", False):
    project_dir = os.getcwd()
else:
    project_dir = os.path.dirname(os.path.abspath(__file__))

json_dir = os.path.join(project_dir, "projects")
if not os.path.isdir(json_dir):
    messagebox.showerror("Error", "Missing 'projects' folder.")
    sys.exit(1)

def open_item(evt):
    sel = lb.curselection()
    if not sel: return
    fn = lb.get(sel[0])
    full = os.path.join(json_dir, fn)
    subprocess.Popen([
        "python",
        os.path.join(project_dir, "gui.py"),
        project_dir,
        full
    ], cwd=project_dir)

root = tk.Tk()
root.title("Archive — " + os.path.basename(project_dir))

lb = tk.Listbox(root, width=60, height=20)
lb.pack(fill=tk.BOTH, expand=True)
lb.bind("<Double-1>", open_item)

files = sorted(
    [f for f in os.listdir(json_dir) if f.lower().endswith('.json')],
    key=lambda f: os.path.getmtime(os.path.join(json_dir, f)),
    reverse=True
)
for f in files:
    lb.insert(tk.END, f)

root.mainloop()
'''
        launcher_py = os.path.join(project_dir, "launcher.py")
        with open(launcher_py, "w", encoding="utf-8") as f:
            f.write(launcher_code)

       # 6) Copy prebuilt launcher.exe and rename it
        prebuilt_launcher = os.path.join(base_dir, "launcher.exe")
        exe_name = name + (".exe" if os.name == "nt" else "")
        target_exe = os.path.join(project_dir, exe_name)

        if os.path.exists(prebuilt_launcher):
            shutil.copy(prebuilt_launcher, target_exe)
        else:
            messagebox.showerror(
                "Error",
                "Missing prebuilt 'launcher.exe'.\nPlease make sure it's in the same folder as this app."
            )
            return

        # 8) Clean up
        shutil.rmtree(os.path.join(project_dir, "build"), ignore_errors=True)
        spec = os.path.join(project_dir, f"{name}.spec")
        if os.path.exists(spec):
            os.remove(spec)
        shutil.rmtree(dist, ignore_errors=True)

        messagebox.showinfo(
            "Success",
            f"Project '{name}' created at:\n\n{project_dir}\n\n"
            f"• JSON in: projects/{name}.json\n"
            f"• Launcher exe: {exe_name}"
        )
        root.destroy()

    except subprocess.CalledProcessError:
        messagebox.showwarning(
            "Build Error",
            "Project folder created, but failed to build the .exe.\n"
            "Ensure PyInstaller is installed and on your PATH."
        )
    except Exception as e:
        messagebox.showerror("Error", str(e))

# --- GUI setup with ttkbootstrap ---
style = Style(theme="litera")
root = style.master
root.title("Create New Project")
root.resizable(False, False)
root.geometry("520x200")

frame = tb.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

# Destination selector
tb.Label(frame, text="Destination Folder:", font=("Segoe UI", 10)).grid(
    row=0, column=0, sticky="e", padx=5, pady=5
)
dest_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
# Removed bootstyle from Entry to avoid missing method error
tb.Entry(frame, textvariable=dest_var, width=35).grid(row=0, column=1, padx=5, pady=5)
tb.Button(frame, text="Browse…", bootstyle="secondary", command=browse_destination).grid(
    row=0, column=2, padx=5
)

# Project name
tb.Label(frame, text="Project Name:", font=("Segoe UI", 10)).grid(
    row=1, column=0, sticky="e", padx=5, pady=5
)
name_var = tk.StringVar()
# Removed bootstyle from Entry here as well
tb.Entry(frame, textvariable=name_var, width=35).grid(row=1, column=1, columnspan=2, padx=5, pady=5)

# Create button
tb.Button(
    frame,
    text="Create Project",
    bootstyle="success",
    width=20,
    command=create_project
).grid(row=2, column=0, columnspan=3, pady=15)

root.mainloop()
