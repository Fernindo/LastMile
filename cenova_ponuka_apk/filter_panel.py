import tkinter as tk
from tkinter import ttk

def create_filter_panel(parent, on_mousewheel_callback):
    filter_container = tk.Frame(parent, bg="white", width=250)
    filter_container.pack_propagate(False)

    canvas = tk.Canvas(filter_container, bg="white", highlightthickness=0)
    scrollbar = tk.Scrollbar(filter_container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    filter_frame = tk.Frame(canvas, bg="white")
    canvas_frame = canvas.create_window((0, 0), window=filter_frame, anchor="nw")

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")

    filter_frame.bind("<Enter>", _bind_mousewheel)
    filter_frame.bind("<Leave>", _unbind_mousewheel)
    filter_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    category_vars = {}
    table_vars = {}

    def setup_category_tree(category_structure):
        # Clear previous widgets in case of reload
        for widget in filter_frame.winfo_children():
            widget.destroy()

        tk.Label(
            filter_frame,
            text="Prehliadač databázových tabuliek",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w", padx=5, pady=5)

        def toggle_category(cat, children_frame, subcats):
            def handler(*args):
                show = category_vars[cat].get()
                if show:
                    children_frame.pack(anchor="w", fill="x", padx=20)
                else:
                    children_frame.pack_forget()
                on_mousewheel_callback()
            return handler

        for category, classes in category_structure.items():
            category_vars[category] = tk.BooleanVar(value=False)

            outer_frame = tk.Frame(filter_frame, bg="white")
            outer_frame.pack(anchor="w", fill="x", padx=5, pady=2)

            cat_checkbox = ttk.Checkbutton(
                outer_frame,
                text=category,
                variable=category_vars[category]
            )
            cat_checkbox.pack(anchor="w")

            children_frame = tk.Frame(outer_frame, bg="white")

            for class_id, table_name in classes:
                table_vars[class_id] = tk.BooleanVar(value=False)

                def table_toggle_callback(cid=class_id):
                    def inner(*args):
                        on_mousewheel_callback()
                    return inner

                table_vars[class_id].trace_add("write", table_toggle_callback())

                chk = tk.Checkbutton(
                    children_frame,
                    text=table_name,
                    variable=table_vars[class_id],
                    bg="white"
                )
                chk.pack(anchor="w", pady=1)

            category_vars[category].trace_add("write", toggle_category(category, children_frame, classes))

        tk.Button(
            filter_frame,
            text="Resetovať filtre",
            command=reset_filters
        ).pack(anchor="w", pady=10, padx=5)

    def reset_filters():
        for var in table_vars.values():
            var.set(False)
        for var in category_vars.values():
            var.set(False)
        on_mousewheel_callback()

    return filter_container, setup_category_tree, category_vars, table_vars
