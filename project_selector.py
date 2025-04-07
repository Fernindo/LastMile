
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import subprocess
import json
import shutil
import platform

project_files = []

def launch_gui(project_path):
    subprocess.Popen(["python", "gui.py", project_path])

def create_new_project():
    name = simpledialog.askstring("New Project", "Enter a name for your new project:")
    if name:
        folder_path = os.path.join("projects", name)
        if os.path.exists(folder_path):
            messagebox.showerror("Error", "Project already exists!")
        else:
            os.makedirs(folder_path)
            with open(os.path.join(folder_path, "basket.json"), "w", encoding="utf-8") as f:
                json.dump({}, f)
            list_projects()

def open_project(event=None):
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        project_name = project_listbox.get(index)
        folder_path = os.path.join("projects", project_name)
        show_project_files(folder_path)

def show_project_files(folder_path):
    file_listbox.delete(0, tk.END)
    if os.path.isdir(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                file_listbox.insert(tk.END, file)
        file_listbox.folder_path = folder_path  # attach path to widget

def open_selected_file(event=None):
    selection = file_listbox.curselection()
    if selection:
        index = selection[0]
        file_name = file_listbox.get(index)
        folder_path = file_listbox.folder_path
        file_path = os.path.join(folder_path, file_name)
        launch_gui(folder_path)

def delete_project():
    global project_files
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        name = project_listbox.get(index)
        folder_path = os.path.join("projects", name)
        if messagebox.askyesno("Delete Project", f"Are you sure you want to delete the folder '{folder_path}'?"):
            try:
                shutil.rmtree(folder_path)
                list_projects()
                file_listbox.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete folder:\n{e}")

def refresh_project_list():
    query = search_var.get().lower()
    project_listbox.delete(0, tk.END)
    for f in sorted(project_files):
        name = os.path.splitext(f)[0]
        if query in name.lower():
            project_listbox.insert(tk.END, name)

def list_projects():
    global project_files
    os.makedirs("projects", exist_ok=True)
    project_files = [f for f in os.listdir("projects") if os.path.isdir(os.path.join("projects", f))]
    refresh_project_list()

root = tk.Tk()
root.title("Project Manager")
root.state("zoomed")

main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# Search and project list
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

# File list of selected project
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

tk.Label(right_frame, text="Files in Project:", font=("Arial", 12)).pack()
file_listbox = tk.Listbox(right_frame, width=50, height=20, font=("Arial", 12))
file_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
file_listbox.bind("<Double-1>", open_selected_file)
file_listbox.folder_path = None  # custom attribute to track current folder

list_projects()
root.mainloop()
