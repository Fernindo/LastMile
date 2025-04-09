import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import subprocess
import json
import shutil
from datetime import datetime
from functools import partial

project_files = []
DEFAULT_TEMPLATE = {"data": "Default session content."}

def launch_gui(folder_path, file_path=None):
    """
    Launches the GUI (gui.py).
    If file_path is provided, it's passed as the second argument for loading that specific JSON.
    """
    import sys
    this_dir = os.path.dirname(os.path.abspath(__file__))
    gui_path = os.path.join(this_dir, "gui.py")

    if file_path:
        subprocess.Popen([sys.executable, gui_path, folder_path, file_path])
    else:
        subprocess.Popen([sys.executable, gui_path, folder_path])

def create_new_project():
    """
    Creates a new project folder under 'projects' and places a fresh .json file in it.
    """
    name = simpledialog.askstring("New Project", "Enter a name for your new project:")
    if name:
        folder_path = os.path.join("projects", name)
        if os.path.exists(folder_path):
            messagebox.showerror("Error", "Project already exists!")
        else:
            os.makedirs(folder_path)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(folder_path, f"{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TEMPLATE, f)
            list_projects()

def open_project(event=None):
    """
    Handles double-click on a project in the left Listbox.
    Shows the JSON files (backups, basket.json, etc.) of that project in the right Listbox.
    """
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        project_name = project_listbox.get(index)
        folder_path = os.path.join("projects", project_name)
        show_project_files(folder_path)

def show_project_files(folder_path):
    """
    Reads all files in the project's folder and populates the right Listbox.
    """
    # Clear current items
    files_listbox.delete(0, tk.END)
    files_listbox.folder_path = folder_path

    if os.path.isdir(folder_path):
        files = sorted(os.listdir(folder_path))
        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                files_listbox.insert(tk.END, file)

def open_file_direct(event):
    """
    Double-click handler for the 'Files in Project' Listbox.
    This opens the selected JSON file in gui.py.
    """
    selection = files_listbox.curselection()
    if selection:
        index = selection[0]
        file_name = files_listbox.get(index)
        folder_path = files_listbox.folder_path
        file_path = os.path.join(folder_path, file_name)
        launch_gui(folder_path, file_path=file_path)

def delete_file():
    """
    Deletes the currently selected file in the right Listbox.
    """
    selection = files_listbox.curselection()
    if selection:
        index = selection[0]
        file_name = files_listbox.get(index)
        folder_path = files_listbox.folder_path
        file_path = os.path.join(folder_path, file_name)

        if messagebox.askyesno("Delete File", f"Are you sure you want to delete '{file_name}'?"):
            try:
                os.remove(file_path)
                show_project_files(folder_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete file:\n{e}")

def delete_project():
    """
    Deletes the entire project folder (and all its files) after confirmation.
    """
    global project_files
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        project_name = project_listbox.get(index)
        folder_path = os.path.join("projects", project_name)
        if messagebox.askyesno("Delete Project", f"Are you sure you want to delete '{folder_path}'?"):
            try:
                shutil.rmtree(folder_path)
                list_projects()
                files_listbox.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete folder:\n{e}")

def refresh_project_list():
    """
    Refreshes the project list on the left, filtering by search query.
    """
    query = search_var.get().lower()
    project_listbox.delete(0, tk.END)
    for f in sorted(project_files):
        name = os.path.splitext(f)[0]
        if query in name.lower():
            project_listbox.insert(tk.END, name)

def list_projects():
    """
    Lists all subfolders in 'projects' (each subfolder is a project).
    """
    global project_files
    os.makedirs("projects", exist_ok=True)
    project_files = [f for f in os.listdir("projects") if os.path.isdir(os.path.join("projects", f))]
    refresh_project_list()

def on_close():
    """
    Close the window. No new JSON files are created or updated automatically.
    """
    root.destroy()

# -------------------- GUI Setup --------------------
root = tk.Tk()
root.title("Project Manager")
root.state("zoomed")

main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# LEFT PANEL - Projects
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

tk.Label(left_frame, text="Projects:", font=("Arial", 12)).pack()
search_var = tk.StringVar()
search_entry = tk.Entry(left_frame, textvariable=search_var, width=30, font=("Arial", 12))
search_entry.pack(pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_project_list())

project_listbox = tk.Listbox(left_frame, width=30, height=20, font=("Arial", 12))
project_listbox.pack(pady=5)
project_listbox.bind("<Double-1>", open_project)

tk.Button(left_frame, text="Create New Project", width=25, command=create_new_project).pack(pady=5)
tk.Button(left_frame, text="Delete Selected Project", width=25, command=delete_project).pack(pady=5)

# RIGHT PANEL - Files in Project
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

tk.Label(right_frame, text="Files in Project:", font=("Arial", 12)).pack(anchor="w")

# This Listbox will display the files (e.g., basket.json, backup_*.json, etc.)
files_listbox = tk.Listbox(right_frame, width=40, height=20, font=("Arial", 12))
files_listbox.folder_path = None
files_listbox.pack(pady=5, fill=tk.BOTH, expand=True)

# Double-click to open a file in the GUI
files_listbox.bind("<Double-1>", open_file_direct)

tk.Button(right_frame, text="Delete Selected File", width=25, command=delete_file).pack(pady=5)

# INIT
list_projects()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
