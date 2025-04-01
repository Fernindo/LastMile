import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import os
import subprocess
import json

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

def open_project_from_list(event):
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        filename = project_listbox.get(index)
        name = os.path.splitext(filename)[0]
        launch_gui(name)
        root.destroy()

def list_projects():
    files = [f for f in os.listdir() if f.endswith(".json")]
    for f in sorted(files):
        project_listbox.insert(tk.END, f)

root = tk.Tk()
root.title("Project Manager")
root.state("zoomed")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(expand=True)

tk.Label(frame, text="Select a project or create a new one:", font=("Arial", 14)).pack(pady=10)

project_listbox = tk.Listbox(frame, width=50, height=20, font=("Arial", 12))
project_listbox.pack(pady=5)
project_listbox.bind("<Double-1>", open_project_from_list)

btn_frame = tk.Frame(frame)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Create New Project", width=20, command=create_new_project).pack(side=tk.LEFT, padx=10)

tk.Button(btn_frame, text="Open via File", width=20, command=lambda: open_project_from_list(None)).pack(side=tk.LEFT, padx=10)

list_projects()
root.mainloop()