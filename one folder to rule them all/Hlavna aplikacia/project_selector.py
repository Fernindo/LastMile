import os
import json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, simpledialog

# Directory containing all projects
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")


def list_projects():
    """Return a list of project folders."""
    if not os.path.isdir(PROJECTS_DIR):
        return []
    return [d for d in os.listdir(PROJECTS_DIR)
            if os.path.isdir(os.path.join(PROJECTS_DIR, d))]


def list_versions(project):
    """Return a list of version files for the given project."""
    pdir = os.path.join(PROJECTS_DIR, project)
    if not os.path.isdir(pdir):
        return []
    return [f for f in os.listdir(pdir) if f.endswith('.json')]


def on_project_select(event):
    """Update the version list when a project is selected."""
    selection = project_list.curselection()
    version_list.delete(0, tk.END)
    if not selection:
        return
    project = project_list.get(selection[0])
    for ver in list_versions(project):
        version_list.insert(tk.END, ver)


def open_version():
    """Open the selected project version."""
    psel = project_list.curselection()
    vsel = version_list.curselection()
    if not psel or not vsel:
        messagebox.showwarning("Warning", "Please select a project and version.")
        return
    project = project_list.get(psel[0])
    version = version_list.get(vsel[0])
    fpath = os.path.join(PROJECTS_DIR, project, version)
    try:
        root.destroy()
        import gui
        gui.start(BASE_DIR, fpath)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open project: {e}")


def create_project():
    """Prompt for a new project name and create its folder and initial file."""
    name = simpledialog.askstring("New Project", "Project name:")
    if not name:
        return
    pdir = os.path.join(PROJECTS_DIR, name)
    if os.path.exists(pdir):
        messagebox.showerror("Error", "Project already exists.")
        return
    os.makedirs(pdir, exist_ok=True)
    initial = os.path.join(pdir, f"{name}.json")
    try:
        with open(initial, "w", encoding="utf-8") as f:
            json.dump({}, f)
        project_list.insert(tk.END, name)
        root.destroy()
        import gui
        gui.start(BASE_DIR, initial)
    except Exception as e:
        messagebox.showerror("Error", f"Could not create project: {e}")


style = Style(theme="litera")
root = style.master
root.title("Project Selector")
root.geometry("500x300")

frame = tb.Frame(root, padding=20)
frame.pack(fill="both", expand=True)
frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)

# Labels
tb.Label(frame, text="Projects:", font=("Segoe UI", 10))\
    .grid(row=0, column=0, sticky="w")
tb.Label(frame, text="Versions:", font=("Segoe UI", 10))\
    .grid(row=0, column=1, sticky="w")

# Project list
project_list = tk.Listbox(frame, height=10)
project_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
project_list.bind("<<ListboxSelect>>", on_project_select)

# Version list
version_list = tk.Listbox(frame, height=10)
version_list.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

# Buttons
tb.Button(frame, text="Open", bootstyle="success", command=open_version)\
    .grid(row=2, column=0, padx=5, pady=10, sticky="ew")
tb.Button(frame, text="New Project", bootstyle="info", command=create_project)\
    .grid(row=2, column=1, padx=5, pady=10, sticky="ew")

# Populate projects
for proj in list_projects():
    project_list.insert(tk.END, proj)

root.mainloop()
