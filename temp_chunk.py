    left.pack(side="left", fill="y")
    tb.Label(left, text="Filter:").pack(anchor="w")
    filter_entry = tb.Entry(left, textvariable=root.projects_home_state["filter_text"])
    filter_entry.pack(fill="x", pady=(0, 6))
    right = tb.Labelframe(body, text="Archive", padding=8)
    right.pack(side="left", fill="both", expand=True, padx=(10, 0))

    proj_list = tk.Listbox(left, width=32, height=22)
    proj_list.pack(fill="y")

    # Project action buttons
    proj_btns = tb.Frame(left)
    proj_btns.pack(fill="x", pady=(8, 0))
    create_btn = tb.Button(proj_btns, text="Vytvoriť projekt", bootstyle="success", command=create_project_dialog)
    create_btn.pack(fill="x")
    delete_btn = tb.Button(proj_btns, text="Delete Project", bootstyle="danger")
    delete_btn.pack(fill="x", pady=(6, 0))

    archive_list = tk.Listbox(right)
    archive_list.pack(fill="both", expand=True)

    buttons = tb.Frame(right)
    buttons.pack(fill="x", pady=6)
    open_btn = tb.Button(buttons, text="Open Selected", bootstyle="info")
    open_btn.pack(side="left")

    # ─────────────────────────── Behaviors ───────────────────────────

    def refresh_projects(*_):
        """Refresh only the UI list from in-memory projects and current filter."""
        projects = root.projects_home_state["projects"]
        proj_list.delete(0, "end")
        flt = root.projects_home_state["filter_text"].get().lower()
        for item in projects:
            name = item["name"]
            if flt and flt not in name.lower():
                continue
            proj_list.insert("end", name)
        archive_list.delete(0, "end")
        archive_list._files = []
        root.projects_home_state["selected_project"] = None
        delete_btn.configure(state="disabled")

    # Debounced filter to avoid rescanning/redrawing on each keystroke
    _filter_after = [None]
    def _on_filter_change(*_args):
        if _filter_after[0] is not None:
            try:
                root.after_cancel(_filter_after[0])
            except Exception:
                pass
        _filter_after[0] = root.after(120, refresh_projects)
    root.projects_home_state["filter_text"].trace_add("write", _on_filter_change)

    def rescan_projects():
        projects = discover_projects(root.projects_home_state["projects_root"].get())
        root.projects_home_state["projects"] = projects

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
            who = resolve_author_from_json(fp)
            # Strip extension and trailing timestamp suffix from filename, keep only save name
            stem = base[:-5] if base.lower().endswith('.json') else base
            m = re.match(r"^(?P<name>.+?)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$", stem)
            nice_name = m.group('name') if m else stem
            line = f"{ts}  |  {nice_name}"
            if who:
                line += f"  |  {who}"
            archive_list.insert("end", line)

        archive_list._files = files  


    def open_selected():
        if not load_login_state() and not load_skip_login():
            messagebox.showwarning(
            "Prihlásenie",
            "Aby si mohol otvoriť projekt, prihlás sa (alebo dočasne povol 'Skip prihlásenia')."
        )
            return
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

       
        try:
            if os.path.commonpath([proj_path, projects_root]) != projects_root:
                messagebox.showerror("Safety check failed", "Project path is outside the Projects Root. Aborting.")
                return
        except ValueError:
            messagebox.showerror("Safety check failed", "Invalid paths detected. Aborting.")
            return

        
        ok = messagebox.askyesno(
            "Delete Project",
            f"Delete the entire project '{proj_name}'?\n\n"
            f"This will remove the project folder and its archive permanently.",
            icon="warning",
            default="no",
        )
        if not ok:
            return

        
        try:
            shutil.rmtree(proj_path)
        except Exception as e:
            messagebox.showerror("Delete failed", f"Could not delete project:\n{e}")
            return

       
        rescan_projects()
        refresh_projects()
        messagebox.showinfo("Project deleted", f"'{proj_name}' was deleted.")

    
    proj_list.bind("<<ListboxSelect>>", on_project_select)                 
    archive_list.bind("<Double-Button-1>", lambda e: open_selected())     
    archive_list.bind("<Return>", lambda e: open_selected())               

    open_btn.configure(command=open_selected)
    delete_btn.configure(command=delete_selected_project, state="disabled")

    rescan_projects()
    refresh_projects()
    if owns_root:
        root.mainloop()

if __name__ == "__main__":
    main()

