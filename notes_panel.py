# notes_panel.py

import tkinter as tk

def create_notes_panel(parent, basket_items):
    """
    Creates a note-taking panel in the given parent frame.
    Notes are saved into basket_items['_notes'] and persist via save_basket().
    """
    frame = tk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    label = tk.Label(frame, text="Poznámky (budú exportované):", font=("Arial", 10))
    label.pack(anchor="w")

    text_widget = tk.Text(frame, height=6, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True)

    def save_notes():
        basket_items["_notes"] = text_widget.get("1.0", tk.END).strip()


    def on_text_change(event):
        if text_widget.edit_modified():
            save_notes()
            text_widget.edit_modified(False)

    # Bind both text change and focus-out to make sure we catch edits
    text_widget.bind("<<Modified>>", on_text_change)
    text_widget.bind("<FocusOut>", lambda e: save_notes())

    # Restore saved notes if available
    if "_notes" in basket_items:
        text_widget.insert("1.0", basket_items["_notes"])

    return frame
