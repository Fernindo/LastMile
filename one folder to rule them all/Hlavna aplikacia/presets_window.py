import tkinter as tk
import ttkbootstrap as tb


def show_presets_window():
    """Open a window showing preset entries."""
    win = tk.Toplevel()
    win.title("📦 Presets")

    # Center the window and set a minimum size similar to doprava.py
    width, height = 600, 400
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")
    win.minsize(600, 400)

    cols = ("ID", "Name", "Created by", "Created at")
    tree = tb.Treeview(win, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Dummy data
    presets = [
        (1, "Preset A", "User1", "2024-01-01"),
        (2, "Preset B", "User2", "2024-02-01"),
        (3, "Preset C", "User3", "2024-03-01"),
    ]
    for preset in presets:
        tree.insert("", "end", values=preset)

    tb.Button(win, text="Close", bootstyle="secondary", command=win.destroy).pack(pady=10)

