import tkinter as tk
from tkinter import ttk

def create_filter_panel(parent, on_mousewheel_callback,
                        width_fraction=0.2,
                        min_width=250,
                        max_width=450):
    """
    Creates a horizontally scrollable filter panel that automatically
    resizes based on the parent window's width.

    Parameters:
        parent: The parent tkinter container (e.g., root).
        on_mousewheel_callback: Function to apply filters or trigger update on filter change.
        width_fraction: Fraction of parent width to assign to the panel (0 < f < 1).
        min_width: Minimum panel width in pixels.
        max_width: Maximum panel width in pixels.

    Returns:
        filter_container: Frame to add checkboxes and filter controls.
        setup_category_tree: Function to call with your category structure.
        category_vars, table_vars: Dicts of tkinter BooleanVars for categories and tables.
    """
    # Container frame that will hold the scrollable panel
    filter_container = tk.Frame(parent, bg="white")
    filter_container.pack_propagate(False)

    # Dynamically adjust width when parent is resized
    def _adjust_width(event):
        total_w = event.width
        target = int(total_w * width_fraction)
        target = max(min(target, max_width), min_width)
        filter_container.config(width=target)
    parent.bind("<Configure>", _adjust_width)

    # Inner canvas and horizontal scrollbar
    canvas = tk.Canvas(filter_container, bg="white", highlightthickness=0)
    h_scrollbar = tk.Scrollbar(filter_container, orient="horizontal", command=canvas.xview)
    canvas.configure(xscrollcommand=h_scrollbar.set)

    filter_frame = tk.Frame(canvas, bg="white")
    canvas_window = canvas.create_window((0, 0), window=filter_frame, anchor="nw")

    canvas.pack(fill=tk.BOTH, expand=True)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Enable scrolling via Shift+Wheel when hovering
    def _on_enter(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    def _on_leave(event):
        canvas.unbind_all("<MouseWheel>")
    def _on_mousewheel(event):
        if event.state & 0x0001:  # Shift key held
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
    filter_frame.bind("<Enter>", _on_enter)
    filter_frame.bind("<Leave>", _on_leave)
    filter_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # State variables
    category_vars = {}
    table_vars = {}

    def setup_category_tree(category_structure):
        tk.Label(filter_frame,
                 text="Prehliadač databázových tabuliek",
                 font=("Arial", 10, "bold"),
                 bg="white").pack(anchor="w", padx=5, pady=5)

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
            cat_checkbox = ttk.Checkbutton(
                outer_frame, text=category,
                variable=category_vars[category]
            )
            cat_checkbox.pack(anchor="w")
            category_vars[category].trace_add(
                "write",
                toggle_category(category, children_frame, classes)
            )

            for class_id, table_name in classes:
                table_vars[class_id] = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(
                    children_frame,
                    text=table_name,
                    variable=table_vars[class_id],
                    command=on_mousewheel_callback,
                    bg="white"
                )
                chk.pack(anchor="w", pady=1)

        tk.Button(
            filter_frame,
            text="Resetovať filtre",
            command=lambda: reset_filters()
        ).pack(anchor="w", pady=10, padx=5)

    def reset_filters():
        for var in table_vars.values(): var.set(False)
        for var in category_vars.values(): var.set(False)
        on_mousewheel_callback()

    return filter_container, setup_category_tree, category_vars, table_vars
