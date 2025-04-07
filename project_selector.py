import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import subprocess
import json
import shutil
from datetime import datetime
from functools import partial  # for safer and faster lambda replacements

project_files = []
DEFAULT_TEMPLATE = {"data": "Default session content."}

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
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(folder_path, f"{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TEMPLATE, f)
            list_projects()

def open_project(event=None):
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        project_name = project_listbox.get(index)
        folder_path = os.path.join("projects", project_name)
        show_project_files(folder_path)

def open_file_direct(event, file_path):
    folder_path = os.path.dirname(file_path)
    launch_gui(folder_path)

def delete_file_with_confirm(file_path):
    file_name = os.path.basename(file_path)
    if messagebox.askyesno("Delete File", f"Are you sure you want to delete '{file_name}'?"):
        try:
            os.remove(file_path)
            show_project_files(os.path.dirname(file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete file:\n{e}")

def show_project_files(folder_path):
    for widget in file_list_container.winfo_children():
        widget.destroy()

    file_listbox.folder_path = folder_path

    if os.path.isdir(folder_path):
        files = sorted(os.listdir(folder_path))
        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                row = tk.Frame(file_list_container)
                row.pack(fill=tk.X, pady=1)

                file_label = tk.Label(row, text=file, font=("Arial", 12), anchor="w", cursor="hand2")
                file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
                file_label.bind("<Double-1>", partial(open_file_direct, file_path=file_path))

                x_button = tk.Button(
                    row,
                    text="x",
                    font=("Arial", 10),
                    fg="black",
                    width=2,
                    relief=tk.FLAT,
                    command=partial(delete_file_with_confirm, file_path)
                )
                x_button.pack(side=tk.RIGHT, padx=(0, 5))

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
                for widget in file_list_container.winfo_children():
                    widget.destroy()
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

def on_close():
    try:
        for project in project_files:
            folder = os.path.join("projects", project)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = os.path.join(folder, f"{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TEMPLATE, f)
    except Exception as e:
        print(f"Error during saving: {e}")
    root.destroy()

# GUI Setup
root = tk.Tk()
root.title("Project Manager")
root.state("zoomed")

main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(expand=True, fill=tk.BOTH)

# LEFT PANEL
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

# RIGHT PANEL
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

tk.Label(right_frame, text="Files in Project:", font=("Arial", 12)).pack(anchor="w")

file_action_frame = tk.Frame(right_frame)
file_action_frame.pack(fill=tk.BOTH, expand=True)

file_listbox = tk.Label()  # Dummy, just for storing folder_path
file_listbox.folder_path = None

file_list_container = tk.Frame(file_action_frame)
file_list_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

# INIT
list_projects()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
