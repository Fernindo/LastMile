import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap import Style

import projects
import gui


def main() -> None:
    """Launch the Projects Home screen."""
    settings = projects.load_app_settings()
    projects_root = tk.StringVar(value=projects.get_projects_root(settings))

    style = Style(theme="litera")
    root = style.master
    root.title("Projects Home")
    root.geometry("900x500")

    top = tb.Frame(root, padding=10)
    top.pack(fill="x")

    tb.Label(top, text="Projects Root:").pack(side="left")
    root_entry = tb.Entry(top, textvariable=projects_root, width=50)
    root_entry.pack(side="left", padx=5)

    def browse_root() -> None:
        path = filedialog.askdirectory(
            initialdir=projects_root.get() or os.path.expanduser("~")
        )
        if path:
            projects_root.set(path)
            projects.set_projects_root(path)
            refresh_projects()

    tb.Button(top, text="Browse…", command=browse_root).pack(side="left")

    def create_project() -> None:
        root_dir = projects_root.get()
        if not root_dir:
            messagebox.showerror("Error", "Please choose a Projects Root first.")
            return
        name = simpledialog.askstring("Project Name", "Enter project name:")
        if name:
            projects.create_project(root_dir, name.strip())
            refresh_projects()

    tb.Button(
        top, text="Create Project", bootstyle="success", command=create_project
    ).pack(side="right")

    main = tb.Frame(root, padding=10)
    main.pack(fill="both", expand=True)

    project_list = tk.Listbox(main, width=30)
    project_list.pack(side="left", fill="y")

    archive_list = tk.Listbox(main)
    archive_list.pack(side="left", fill="both", expand=True, padx=10)

    archive_map: dict[str, str] = {}

    def refresh_projects() -> None:
        project_list.delete(0, tk.END)
        root_dir = projects_root.get()
        for proj in projects.discover_projects(root_dir):
            project_list.insert(tk.END, proj["name"])
        archive_list.delete(0, tk.END)
        archive_map.clear()

    def refresh_archive(event=None) -> None:
        archive_list.delete(0, tk.END)
        archive_map.clear()
        sel = project_list.curselection()
        if not sel:
            return
        name = project_list.get(sel[0])
        project_path = os.path.join(projects_root.get(), name)
        for path in projects.get_project_archive(project_path):
            base = os.path.basename(path)
            name_part, _ = os.path.splitext(base)
            if "_" in name_part:
                base_name, date_part = name_part.split("_", 1)
                display = f"{date_part} | {base_name}"
            else:
                display = name_part
            archive_list.insert(tk.END, display)
            archive_map[display] = path

    project_list.bind("<<ListboxSelect>>", refresh_archive)

    def open_selected(event=None) -> None:
        p_sel = project_list.curselection()
        a_sel = archive_list.curselection()
        if not (p_sel and a_sel):
            return
        project_name = project_list.get(p_sel[0])
        project_dir = os.path.join(projects_root.get(), project_name)
        display = archive_list.get(a_sel[0])
        json_path = archive_map.get(display)
        if json_path:
            root.destroy()
            gui.start(project_dir, json_path)

    archive_list.bind("<Double-1>", open_selected)

    tb.Button(root, text="Open", bootstyle="primary", command=open_selected).pack(
        pady=5
    )

    refresh_projects()
    root.mainloop()


if __name__ == "__main__":
    main()

