import os
import json
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, simpledialog

# Directory containing all projects
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)


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


def start():
    """Launch the project selector window."""

    root = tk.Tk()
    style = Style(master=root, theme="litera")
    root.title("Project Selector")
    root.geometry("500x300")

    frame = tb.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    # Labels
    tb.Label(frame, text="Projects:", font=("Segoe UI", 10)) \
        .grid(row=0, column=0, sticky="w")
    tb.Label(frame, text="Versions:", font=("Segoe UI", 10)) \
        .grid(row=0, column=1, sticky="w")

    # Project list
    project_list = tk.Listbox(frame, height=10)
    project_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    # Version list
    version_list = tk.Listbox(frame, height=10)
    version_list.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    def on_project_select(event):
        """Update the version list when a project is selected."""
        selection = project_list.curselection()
        version_list.delete(0, tk.END)
        if not selection:
            return
        project = project_list.get(selection[0])
        for ver in list_versions(project):
            version_list.insert(tk.END, ver)

    def refresh_projects():
        """Reload the project list from disk."""
        project_list.delete(0, tk.END)
        for proj in list_projects():
            project_list.insert(tk.END, proj)

    def open_version():
        """Open the selected project version using the main GUI."""
        psel = project_list.curselection()
        vsel = version_list.curselection()
        if not psel or not vsel:
            messagebox.showwarning("Warning", "Please select a project and version.")
            return
        project = project_list.get(psel[0])
        version = version_list.get(vsel[0])
        fpath = os.path.join(PROJECTS_DIR, project, version)
        root.destroy()
        import gui
        gui.start(os.path.join(PROJECTS_DIR, project), fpath)

    def create_project():
        """Prompt for a project name and create its folder with a starter file."""
        name = simpledialog.askstring("New Project", "Project name:")
        if not name:
            return
        pdir = os.path.join(PROJECTS_DIR, name)
        if os.path.exists(pdir):
            messagebox.showerror("Error", "Project already exists.")
            return
        os.makedirs(pdir, exist_ok=True)
        starter = os.path.join(pdir, f"{name}.json")
        with open(starter, "w", encoding="utf-8") as f:
            json.dump({"user_name": "", "items": [], "notes": []}, f, ensure_ascii=False, indent=2)
        refresh_projects()
        root.destroy()
        import gui
        gui.start(pdir, starter)

    project_list.bind("<<ListboxSelect>>", on_project_select)

    # Open button
    tb.Button(frame, text="Open", bootstyle="success", command=open_version) \
        .grid(row=2, column=0, columnspan=2, pady=10)

    # Create project button
    tb.Button(frame, text="New Project", bootstyle="info", command=create_project) \
        .grid(row=3, column=0, columnspan=2, pady=(0, 10))

    # Populate projects
    refresh_projects()

    root.mainloop()


if __name__ == "__main__":
    start()
