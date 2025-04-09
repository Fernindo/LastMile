import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import json
import shutil
from datetime import datetime
from functools import partial

project_files = []
DEFAULT_TEMPLATE = {"data": "Default session content."}


def launch_gui(project_path, version_file=None):
    import gui
    gui.run_gui(project_path, version_file)


def create_new_project():
    name = simpledialog.askstring("New Project", "Enter a name for your new project:")
    if name:
        name = name.strip().replace(" ", "_")
        folder_path = os.path.join("projects", name)
        file_path = os.path.join(folder_path, f"{name}.json")

        if os.path.exists(folder_path):
            messagebox.showerror("Error", "Project already exists!")
        else:
            os.makedirs(folder_path)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TEMPLATE, f)
            list_projects()




def open_project(event=None):
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        project_name = project_listbox.get(index).replace("📁 ", "").split("  —")[0]


        folder_path = os.path.join("projects", project_name)
        show_project_files(folder_path)


def open_file_direct(file_path):
    folder_path = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    launch_gui(folder_path, version_file=filename)


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

    global current_folder_path
    current_folder_path = folder_path


    if os.path.isdir(folder_path):
        files = sorted(os.listdir(folder_path), reverse=True)
        file_list = tk.Listbox(file_list_container, font=("Arial", 12), height=25, activestyle="none", borderwidth=0, highlightthickness=0)
        file_list.pack(fill=tk.BOTH, expand=True)

        for file in files:
            full_path = os.path.join(folder_path, file)
            if file.endswith(".json") and os.path.isfile(full_path):
                mod_time = os.path.getmtime(full_path)
                formatted_time = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                display_name = f"{file}  —  {formatted_time}"
                file_list.insert(tk.END, display_name)


        def on_file_open(event):
            selection = file_list.curselection()
            if selection:
                file_name = file_list.get(selection[0]).split("  —")[0]

                file_path = os.path.join(folder_path, file_name)
                open_file_direct(file_path)

        file_list.bind("<Double-1>", on_file_open)


def delete_project():
    global project_files
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        name = project_listbox.get(index).replace("📁 ", "").split("  —")[0]


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
        if query in f.lower():
            folder_path = os.path.join("projects", f)
            if os.path.isdir(folder_path):
                mod_time = os.path.getmtime(folder_path)
                formatted_time = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
                display_name = f"📁 {f}  —  {formatted_time}"

                project_listbox.insert(tk.END, display_name)




def list_projects():
    global project_files
    os.makedirs("projects", exist_ok=True)
    project_files = [f for f in os.listdir("projects") if os.path.isdir(os.path.join("projects", f))]
    refresh_project_list()


def on_close():
    root.destroy()


# GUI Setup
root = tk.Tk()
root.title("Project Manager")
root.geometry("700x650")

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

current_folder_path = None  # This is now a global variable


file_list_container = tk.Frame(file_action_frame)
file_list_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

# INIT
list_projects()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
