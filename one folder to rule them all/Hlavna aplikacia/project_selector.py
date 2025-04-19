import tkinter as tk
from tkinter import messagebox
import os
import sys
import json
import shutil
import subprocess

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

def create_project():
    name = name_var.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a project name.")
        return

    # 1) Make folder on Desktop
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    project_dir = os.path.join(desktop, name)
    if os.path.exists(project_dir):
        messagebox.showerror("Error", f"Folder '{project_dir}' already exists.")
        return

    try:
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

        # 5) Write launcher.py that lists only the JSONs and opens gui.py via system python
        launcher_code = f'''\
import os, sys, subprocess, tkinter as tk
from tkinter import messagebox

# Locate this project folder
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
    # Launch the GUI using the system 'python' command
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

        # 6) Build the single-file exe from launcher.py
        subprocess.run(
            ["pyinstaller", "--onefile", "--name", name, "launcher.py"],
            cwd=project_dir,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 7) Move the exe up to project_dir
        dist = os.path.join(project_dir, "dist")
        exe_name = name + (".exe" if os.name == "nt" else "")
        src_exe = os.path.join(dist, exe_name)
        if os.path.exists(src_exe):
            shutil.move(src_exe, os.path.join(project_dir, exe_name))

        # 8) Clean up build artifacts
        shutil.rmtree(os.path.join(project_dir, "build"), ignore_errors=True)
        spec = os.path.join(project_dir, f"{name}.spec")
        if os.path.exists(spec):
            os.remove(spec)
        shutil.rmtree(dist, ignore_errors=True)

        messagebox.showinfo(
            "Success",
            f"Project '{name}' created on your Desktop:\n\n"
            f"{project_dir}\n\n"
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

# --- GUI setup ---
root = tk.Tk()
root.title("Create New Project")
root.resizable(False, False)

tk.Label(root, text="Project Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
name_var = tk.StringVar()
tk.Entry(root, textvariable=name_var, width=40).grid(row=0, column=1, padx=5, pady=5)

tk.Button(root, text="Create Project", width=20, command=create_project).grid(
    row=1, column=0, columnspan=2, pady=10
)

root.mainloop()
