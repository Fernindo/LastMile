import os
import json
import shutil
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from tkinter import messagebox, filedialog, simpledialog
from datetime import datetime

# Single-app Projects Home embedded in project_selector.py
# No new code files. Only creates project JSONs when you make a new project.

UI_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "ui_settings.json")

# ───────────────────────── Helpers: settings ─────────────────────────

def load_settings():
    if os.path.exists(UI_SETTINGS_FILE):
        try:
            with open(UI_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(data):
    try:
        with open(UI_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot save settings:\n{e}")

def get_projects_root():
    st = load_settings()
    # fallback to a local "workspace" folder, but we won't auto-create it
    return st.get("projects_root", os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace")))

def set_projects_root(path):
    st = load_settings()
    st["projects_root"] = path
    save_settings(st)

# ─────────────────────── Helpers: projects & archive ───────────────────────

def discover_projects(root):
    items = []
    if not os.path.isdir(root):
        return items
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isdir(p):
            continue
        json_dir = os.path.join(p, "projects")
        if os.path.isdir(json_dir):
            items.append({"name": name, "path": p})
    return items

def project_archive(project_path):
    json_dir = os.path.join(project_path, "projects")
    if not os.path.isdir(json_dir):
        return []
    files = [os.path.join(json_dir, f) for f in os.listdir(json_dir) if f.lower().endswith(".json")]
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)  # newest first
    return files

def create_project(root, name):
    if not name:
        raise ValueError("Project name is required.")
    safe = name.strip()
    if not safe:
        raise ValueError("Project name is required.")
    proj_dir = os.path.join(root, safe)
    json_dir = os.path.join(proj_dir, "projects")
    os.makedirs(json_dir, exist_ok=True)
    # Seed one main JSON if missing
    main_json = os.path.join(json_dir, f"{safe}.json")
    if not os.path.exists(main_json):
        with open(main_json, "w", encoding="utf-8") as f:
            json.dump({"project": safe, "created": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    return {"name": safe, "path": proj_dir, "json": main_json}

# ─────────────────────────── Launch GUI safely ───────────────────────────

def launch_gui_in_same_root(root, project_dir, json_path):
    """
    IMPORTANT:
    - Do NOT destroy the Tk root; gui.start() expects a default root to exist.
    - Instead, fully clear the root to avoid pack/grid conflicts, then let gui.start build on it.
    """
    # Persist chosen root before switching screens
    set_projects_root(root.projects_home_state["projects_root"].get())

    # Completely clear the root so there are no pack-managed widgets left
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass

    # Now import and start the main GUI (it will find the existing default root)
    import gui
    gui.start(project_dir, json_path)

# ──────────────────────────────── Main UI ────────────────────────────────

def main():
    style = Style(theme="litera")
    root = style.master
    root.title("Projects Home")
    root.geometry("980x600")

    # Keep a small state dict on the root so helper functions can access it
    root.projects_home_state = {
        "projects_root": tk.StringVar(value=get_projects_root()),
        "projects": [],
        "selected_project": None,
    }

    # Top bar
    top = tb.Frame(root, padding=10)
    top.pack(side="top", fill="x")

    tb.Label(top, text="Projects Root:").pack(side="left")
    root_entry = tb.Entry(top, textvariable=root.projects_home_state["projects_root"], width=60)
    root_entry.pack(side="left", padx=6)

    def browse_root():
        cur = root.projects_home_state["projects_root"].get()
        path = filedialog.askdirectory(initialdir=cur or os.getcwd(), title="Choose Projects Root")
        if path:
            root.projects_home_state["projects_root"].set(path)
            set_projects_root(path)
            refresh_projects()

    tb.Button(top, text="Browse…", bootstyle="secondary", command=browse_root).pack(side="left")

    def create_project_dialog():
        name = simpledialog.askstring("New Project", "Project name:")
        if not name:
            return
        try:
            info = create_project(root.projects_home_state["projects_root"].get(), name)
        except Exception as e:
            messagebox.showerror("Create project failed", str(e))
            return
        refresh_projects()
        select_project_by_name(info["name"])

    tb.Button(top, text="Create Project", bootstyle="success", command=create_project_dialog).pack(side="right")

    # Body: left projects list (with Delete), right archive list
    body = tb.Frame(root, padding=10)
    body.pack(fill="both", expand=True)

    left = tb.Labelframe(body, text="Projects", padding=8)
    left.pack(side="left", fill="y")
    right = tb.Labelframe(body, text="Archive", padding=8)
    right.pack(side="left", fill="both", expand=True, padx=(10, 0))

    proj_list = tk.Listbox(left, width=32, height=22)
    proj_list.pack(fill="y")

    # Project action buttons
    proj_btns = tb.Frame(left)
    proj_btns.pack(fill="x", pady=(8, 0))
    delete_btn = tb.Button(proj_btns, text="Delete Project", bootstyle="danger")
    delete_btn.pack(side="left")

    archive_list = tk.Listbox(right)
    archive_list.pack(fill="both", expand=True)

    buttons = tb.Frame(right)
    buttons.pack(fill="x", pady=6)
    open_btn = tb.Button(buttons, text="Open Selected", bootstyle="info")
    open_btn.pack(side="left")

    # ─────────────────────────── Behaviors ───────────────────────────

    def refresh_projects():
        projects = discover_projects(root.projects_home_state["projects_root"].get())
        root.projects_home_state["projects"] = projects
        proj_list.delete(0, "end")
        for item in projects:
            proj_list.insert("end", item["name"])
        archive_list.delete(0, "end")
        archive_list._files = []
        root.projects_home_state["selected_project"] = None
        delete_btn.configure(state="disabled")

    def select_project_by_name(name):
        for idx, item in enumerate(root.projects_home_state["projects"]):
            if item["name"] == name:
                proj_list.selection_clear(0, "end")
                proj_list.selection_set(idx)
                on_project_select(None)
                break

    def on_project_select(event):
        sel = proj_list.curselection()
        if not sel:
            delete_btn.configure(state="disabled")
            return
        idx = sel[0]
        proj = root.projects_home_state["projects"][idx]
        root.projects_home_state["selected_project"] = proj
        delete_btn.configure(state="normal")

        archive_list.delete(0, "end")
        files = project_archive(proj["path"])
        for fp in files:
            base = os.path.basename(fp)
            ts = datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M")
            archive_list.insert("end", f"{ts}  |  {base}")
        archive_list._files = files  # attach list for easy lookup

    def open_selected():
        proj = root.projects_home_state["selected_project"]
        if not proj:
            messagebox.showwarning("No project selected", "Please select a project.")
            return
        files = getattr(archive_list, "_files", [])
        sel = archive_list.curselection()
        if not sel or not files:
            messagebox.showwarning("No archive selected", "Please select a JSON entry from the archive.")
            return
        json_path = files[sel[0]]
        launch_gui_in_same_root(root, proj["path"], json_path)

    def delete_selected_project():
        """Delete the selected project folder safely (ONLY from Projects list)."""
        sel = proj_list.curselection()
        if not sel:
            messagebox.showwarning("No project selected", "Please select a project to delete.")
            return

        proj = root.projects_home_state["projects"][sel[0]]
        proj_name = proj["name"]
        proj_path = os.path.abspath(proj["path"])
        projects_root = os.path.abspath(root.projects_home_state["projects_root"].get())

        # Safety checks: ensure project is under projects_root
        try:
            if os.path.commonpath([proj_path, projects_root]) != projects_root:
                messagebox.showerror("Safety check failed", "Project path is outside the Projects Root. Aborting.")
                return
        except ValueError:
            messagebox.showerror("Safety check failed", "Invalid paths detected. Aborting.")
            return

        # Confirm irreversible delete
        ok = messagebox.askyesno(
            "Delete Project",
            f"Delete the entire project '{proj_name}'?\n\n"
            f"This will remove the project folder and its archive permanently.",
            icon="warning",
            default="no",
        )
        if not ok:
            return

        # Perform delete
        try:
            shutil.rmtree(proj_path)
        except Exception as e:
            messagebox.showerror("Delete failed", f"Could not delete project:\n{e}")
            return

        # Refresh lists
        refresh_projects()
        messagebox.showinfo("Project deleted", f"'{proj_name}' was deleted.")

    # List bindings
    proj_list.bind("<<ListboxSelect>>", on_project_select)                 # ONLY selects and populates Archive
    archive_list.bind("<Double-Button-1>", lambda e: open_selected())      # double-click Archive -> open
    archive_list.bind("<Return>", lambda e: open_selected())               # Enter on Archive -> open

    open_btn.configure(command=open_selected)
    delete_btn.configure(command=delete_selected_project, state="disabled")

    refresh_projects()
    root.mainloop()

if __name__ == "__main__":
    main()
