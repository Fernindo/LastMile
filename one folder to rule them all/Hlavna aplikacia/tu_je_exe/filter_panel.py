import tkinter as tk
from tkinter import ttk

def create_filter_panel(parent, on_mousewheel_callback):
    """
    Creates a horizontally scrollable filter panel.

    Parameters:
        parent: The parent tkinter container (e.g., root).
        on_mousewheel_callback: Function to apply filters or trigger update on filter change.

    Returns:
        filter_frame: Frame to add checkboxes and filter controls.
        setup_category_tree: Function to call with your category structure.
    """
    filter_container = tk.Frame(parent, bg="white", width=100)
    filter_container.pack_propagate(False)  # ✅ lock the width

    canvas = tk.Canvas(filter_container, bg="white", highlightthickness=0)
    h_scrollbar = tk.Scrollbar(filter_container, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=h_scrollbar.set)

    filter_frame = tk.Frame(canvas, bg="white")
    canvas_window = canvas.create_window((0, 0), window=filter_frame, anchor="nw")

    canvas.pack(fill=tk.BOTH, expand=True)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_enter(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _on_leave(event):
        canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(event):
        if event.state & 0x0001:
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    filter_frame.bind("<Enter>", _on_enter)
    filter_frame.bind("<Leave>", _on_leave)
    filter_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    category_vars = {}
    table_vars = {}

    def setup_category_tree(category_structure):
        tk.Label(filter_frame, text="Prehliadač databázových tabuliek", font=("Arial", 10, "bold"), bg="white").pack(anchor="w", padx=5, pady=5)

        def toggle_category(category, children_frame, classes):
            def handler(*args):
                show = category_vars[category].get()
                children_frame.pack_forget()
                for class_id, _ in classes:
                    table_vars[class_id].set(False)
                if show:
                    children_frame.pack(anchor="w", fill="x", padx=20)
                on_mousewheel_callback()
            return handler

        for category, classes in category_structure.items():
            category_vars[category] = tk.BooleanVar(value=False)
            outer_frame = tk.Frame(filter_frame, bg="white")
            outer_frame.pack(anchor="w", fill="x", padx=5, pady=2)

            children_frame = tk.Frame(outer_frame, bg="white")

            cat_checkbox = ttk.Checkbutton(outer_frame, text=category, variable=category_vars[category])
            cat_checkbox.pack(anchor="w")

            category_vars[category].trace_add("write", toggle_category(category, children_frame, classes))

            for class_id, table_name in classes:
                table_vars[class_id] = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(children_frame, text=table_name, variable=table_vars[class_id], command=on_mousewheel_callback, bg="white")
                chk.pack(anchor="w", pady=1)

        tk.Button(filter_frame, text="Resetovať filtre", command=lambda: reset_filters()).pack(anchor="w", pady=10, padx=5)

    def reset_filters():
        for var in table_vars.values():
            var.set(False)
        for var in category_vars.values():
            var.set(False)
        on_mousewheel_callback()

    return filter_container, setup_category_tree, category_vars, table_vars
