# notes_panel.py

import tkinter as tk
import os

def create_notes_panel(parent, project_name):
    """
    Creates a note-taking panel that saves/loads notes to a text file.
    File: {project_name}_notes.txt
    """
    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    label = tk.Label(frame, text="Poznámky:", font=("Arial", 10))
    label.pack(anchor="w")

    text_widget = tk.Text(frame, height=6, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True)

    file_path = f"{project_name}_notes.txt"

    def save_notes():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_widget.get("1.0", tk.END).strip())
        print(f"📝 Notes saved to {file_path}")

    def on_text_change(event):
        if text_widget.edit_modified():
            save_notes()
            text_widget.edit_modified(False)

    text_widget.bind("<<Modified>>", on_text_change)
    text_widget.bind("<FocusOut>", lambda e: save_notes())

    # Load existing notes if present
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            text_widget.insert("1.0", f.read())
        text_widget.edit_modified(False)

    return frame
