import tkinter as tk  # Because making painful GUIs is more fun with 90s tech
from tkinter import simpledialog, messagebox, filedialog  # All the dialogue boxes no one asked for
import os  # For playing hide-and-seek with files
import subprocess  # Used to launch other scripts like it's 2004
import json  # For storing sadness in structured form
import shutil  # For deleting entire projects in one line. What could go wrong?
import zipfile  # For pretending compression makes you organized
from datetime import datetime  # So you can timestamp your regrets
from functools import partial  # The lazy man's lambda

project_files = []
DEFAULT_TEMPLATE = {"data": "Default session content."}

def launch_gui(folder_path, file_path=None):
    """
    Launches the GUI (gui.py). Because one GUI wasn't enough.
    """
    import sys  # Oh cool, another import. Right here. Why not.
    this_dir = os.path.dirname(os.path.abspath(__file__))  # Locating this script like it owes us money
    gui_path = os.path.join(this_dir, "gui.py")  # Hardcoded script name. Very robust.
    if file_path:
        subprocess.Popen([sys.executable, gui_path, folder_path, file_path])  # Summon the demon with arguments
    else:
        subprocess.Popen([sys.executable, gui_path, folder_path])  # Summon the demon with fewer arguments


def create_new_project():
    """
    Prompts user to name their next failed attempt at a project.
    """
    name = simpledialog.askstring("New Project", "Enter a name for your new project:")  # Probably something like "Test3"
    if name:
        folder_path = os.path.join("projects", name)  # Store it in the sacred Projects folder
        if os.path.exists(folder_path):
            messagebox.showerror("Error", "Project already exists!")  # Apparently you’ve made this mistake before
        else:
            os.makedirs(folder_path)  # The illusion of progress
            file_path = os.path.join(folder_path, f"{name}.json")  # JSON: because nothing says "project" like curly braces
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_TEMPLATE, f, ensure_ascii=False, indent=2)  # Writing default garbage into your shiny new file
            list_projects()  # Let's pretend this function doesn't rely on globals and magic

def open_project(event=None):
    """
    Handles double-click on a project in the left Listbox.
    AKA: the user's one act of commitment.
    """
    selection = project_listbox.curselection()  # UI equivalent of “which one of my children did I click”
    if selection:
        index = selection[0]
        proj_name = project_listbox.get(index)  # Get the chosen one's name
        folder_path = os.path.join("projects", proj_name)  # Ah yes, folder-based data storage: so advanced
        show_project_files(folder_path)  # Show the contents of their regrets

def show_project_files(folder_path):
    """
    Reads all files in the project's folder and populates the right Listbox.
    AKA: here's your mess, sorted.
    """
    files_listbox.delete(0, tk.END)  # Wipe the slate clean, like the last 3 failed projects
    files_listbox.folder_path = folder_path  # Store the folder path on the widget, because that's normal
    if os.path.isdir(folder_path):  # Check that it's not imaginary like my girlfriend 
        files = sorted(
            os.listdir(folder_path),
            key=lambda f: os.path.getmtime(os.path.join(folder_path, f)),  # We sort by modification time, because why not judge a file by how recently it cried
            reverse=True  # Newest to oldest, so you can ignore the fresh stuff first
        )
        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):  # Sanity check for the one time someone added a folder called “lol”
                files_listbox.insert(tk.END, file)  # Behold: the file parade


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
        launch_gui(folder_path, file_path=file_path)# Time to launch the GUI from inside the GUI. What could go wrong?

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
        proj_name = project_listbox.get(index)
        folder_path = os.path.join("projects", proj_name)
        if messagebox.askyesno("Delete Project", f"Are you sure you want to delete '{folder_path}'?"):
            try:
                shutil.rmtree(folder_path) # Bye-bye entire folder. No undo. No safety net.
                list_projects()
                files_listbox.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete folder:\n{e}")# Oopsie-daisy

def export_project():
    """
    Exports the currently selected project folder as a ZIP file.
    """
    selection = project_listbox.curselection()
    if selection:
        index = selection[0]
        proj_name = project_listbox.get(index)
        folder_path = os.path.join("projects", proj_name)
        dest_path = filedialog.asksaveasfilename(title="Export Project Folder As ZIP",
                                                 initialfile=proj_name,
                                                 defaultextension=".zip",
                                                 filetypes=[("ZIP Files", "*.zip"), ("All Files", "*.*")])
        if dest_path:
            try:
                with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root_dir, dirs, files in os.walk(folder_path):
                        for file in files:
                            abs_file = os.path.join(root_dir, file)
                            rel_path = os.path.relpath(abs_file, folder_path)
                            zipf.write(abs_file, rel_path)# Compress the failure into a single neat package
                messagebox.showinfo("Export", f"Project folder exported as:\n{dest_path}")# Clap for yourself
            except Exception as e:
                messagebox.showerror("Error", f"Could not export project folder:\n{e}")# Export denied!
    else:
        messagebox.showwarning("No Project Selected", "Please select a project to export.")# Because obviously you forgot

def import_project():
    """
    Imports a project folder or file.
    If a ZIP file is selected, it unzips it into the projects folder.
    If a JSON file is selected, it will prompt for a new project name and copy the file.
    """
    file_path = filedialog.askopenfilename(title="Import Project or File", 
                                           filetypes=[("ZIP Files", "*.zip"), ("JSON Files", "*.json"), ("All Files", "*.*")])
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".zip":
            project_dest = filedialog.askdirectory(title="Select Destination Folder for Imported Project", initialdir="projects")
            if project_dest:
                try:
                    with zipfile.ZipFile(file_path, 'r') as zipf:
                        project_name = os.path.splitext(os.path.basename(file_path))[0]
                        target_folder = os.path.join(project_dest, project_name)
                        if os.path.exists(target_folder):
                            messagebox.showerror("Error", "A project with that name already exists!")
                            return
                        os.makedirs(target_folder, exist_ok=True)
                        zipf.extractall(target_folder)
                    messagebox.showinfo("Import", f"Project imported to:\n{target_folder}")
                    list_projects()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not import project folder:\n{e}")
        elif ext == ".json":
            new_project = simpledialog.askstring("Import JSON", "Enter a name for the new project:")
            if new_project:
                target_folder = os.path.join("projects", new_project)
                if os.path.exists(target_folder):
                    messagebox.showerror("Error", "A project with that name already exists!")
                    return
                try:
                    os.makedirs(target_folder, exist_ok=True)
                    dest_file = os.path.join(target_folder, f"{new_project}.json")
                    shutil.copy(file_path, dest_file)
                    messagebox.showinfo("Import", f"Project imported as new project:\n{dest_file}")
                    list_projects()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not import JSON file:\n{e}")
        else:
            messagebox.showerror("Error", "Unsupported file type for import.")

def refresh_project_list():
    """
    Refreshes the project list on the left, filtering by search query.
    Because typing a single letter should absolutely reshape the universe.
    """
    query = search_var.get().lower()  # lowercase, because case-sensitive searching is a war crime
    project_listbox.delete(0, tk.END)  # Wipe the list clean, just like your dreams after a debugging session
    for f in sorted(project_files):  # Alphabetical, because chaos must at least be orderly
        name = os.path.splitext(f)[0]  # Cut off the .json like trimming dead ends
        if query in name.lower():  # Crude filter logic, but good enough for the three projects you'll make
            project_listbox.insert(tk.END, name)  # Resurrect from the void


def list_projects():
    """
    Lists all subfolders in 'projects' (each subfolder is a project).
    So, basically, "ls but worse."
    """
    global project_files  # Go ahead. Just declare a global. YOLO.
    os.makedirs("projects", exist_ok=True)  # In case the "projects" folder spontaneously ceases to exist
    project_files = [f for f in os.listdir("projects") if os.path.isdir(os.path.join("projects", f))]  # Basic directory spelunking
    refresh_project_list()  # Now show the user their failures


def on_close():
    """
    Closes the window.
    """
    root.destroy()# Execute order 66

# -------------------- GUI Setup --------------------
root = tk.Tk()  # Boot up the window like it’s Windows 98
root.title("Project Manager")  # Misleading, but optimistic
root.state("zoomed")  # Full screen by default, because users love surprise UI takeovers


main_frame = tk.Frame(root, padx=20, pady=20)  # Padding to make your shame feel cozy
main_frame.pack(expand=True, fill=tk.BOTH)  # Give it space to breathe. It’s dying.


# LEFT PANEL - Projects
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

tk.Label(left_frame, text="Projects:", font=("Arial", 12)).pack()  # Because otherwise you wouldn’t know what this was
search_var = tk.StringVar()
search_entry = tk.Entry(left_frame, textvariable=search_var, width=30, font=("Arial", 12))
search_entry.pack(pady=5)
search_entry.bind("<KeyRelease>", lambda e: refresh_project_list())

project_listbox = tk.Listbox(left_frame, width=30, height=20, font=("Arial", 12))
project_listbox.pack(pady=5)
project_listbox.bind("<Double-1>", open_project)

# Buttons under the project list.
button_frame_left = tk.Frame(left_frame)
button_frame_left.pack(pady=5)

create_btn = tk.Button(button_frame_left, text="Create New Project", width=20, command=create_new_project)
create_btn.pack(pady=2)

delete_proj_btn = tk.Button(button_frame_left, text="Delete Selected Project", width=20, command=delete_project)
delete_proj_btn.pack(pady=2)

export_proj_btn = tk.Button(button_frame_left, text="Export Project", width=20, command=export_project)
export_proj_btn.pack(pady=2)

import_proj_btn = tk.Button(button_frame_left, text="Import Project/File", width=20, command=import_project)
import_proj_btn.pack(pady=2)

# RIGHT PANEL - Files in Project
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

tk.Label(right_frame, text="Files in Project:", font=("Arial", 12)).pack(anchor="w")

files_listbox = tk.Listbox(right_frame, width=40, height=20, font=("Arial", 12))
files_listbox.folder_path = None
files_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
files_listbox.bind("<Double-1>", open_file_direct)

delete_file_btn = tk.Button(right_frame, text="Delete Selected File", width=25, command=delete_file)
delete_file_btn.pack(pady=5)

list_projects()
root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
