import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import subprocess
import json

project_files = []


def launch_gui(project_name):
    subprocess.Popen(["python", "gui.py", project_name])

def create_new_project():
    name = simpledialog.askstring("New Project", "Enter a name for your new project:")
    if name:
        filename = f"{name}.json"
        if os.path.exists(filename):
            messagebox.showerror("Error", "Project already exists!")
        else:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({}, f)
            launch_gui(name)
            root.destroy()

def open_project_from_list(event=None):
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        filename = project_listbox.get(index)
        name = os.path.splitext(filename)[0]
        launch_gui(name)
        root.destroy()

def delete_project():
    global project_files
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        filename = project_listbox.get(index)
        if messagebox.askyesno("Delete Project", f"Are you sure you want to delete '{filename}'?"):
            os.remove(filename)
            list_projects()

def refresh_project_list():
    query = search_var.get().lower()
    project_listbox.delete(0, tk.END)
    for f in sorted(project_files):
        if query in f.lower():
            project_listbox.insert(tk.END, f)

def list_projects():
    global project_files
    project_files = [f for f in os.listdir() if f.endswith(".json")]
    refresh_project_list()

root = tk.Tk()
root.title("Project Manager")
root.state("zoomed")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

tk.Label(frame, text="Select a project or create a new one:", font=("Arial", 14)).pack(pady=10)

search_var = tk.StringVar()
search_entry = tk.Entry(frame, textvariable=search_var, width=50, font=("Arial", 12))
search_entry.pack(pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_project_list())

project_listbox = tk.Listbox(frame, width=50, height=20, font=("Arial", 12))
project_listbox.pack(pady=5)
project_listbox.bind("<Double-1>", open_project_from_list)

btn_frame = tk.Frame(frame)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Create New Project", width=20, command=create_new_project).pack(side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="Delete Selected Project", width=20, command=delete_project).pack(side=tk.LEFT, padx=10)

list_projects()
root.mainloop()
