import os
import sys
import tkinter as tk
from tkinter import messagebox
import gui  # your gui.py defines a main(project_path, json_path) function

# Determine project directory (where launcher.exe lives)
if getattr(sys, "frozen", False):
    project_dir = os.getcwd()
else:
    project_dir = os.path.dirname(os.path.abspath(__file__))

# The folder where all the .json archives live
json_dir = os.path.join(project_dir, "projects")
if not os.path.isdir(json_dir):
    messagebox.showerror("Error", "Missing 'projects' folder.")
    sys.exit(1)

# Build the Archive window
root = tk.Tk()
root.title(f"Archive — {os.path.basename(project_dir)}")

lb = tk.Listbox(root, width=60, height=20)
lb.pack(fill=tk.BOTH, expand=True)

# Populate with all .json files, newest first
files = sorted(
    [f for f in os.listdir(json_dir) if f.lower().endswith(".json")],
    key=lambda f: os.path.getmtime(os.path.join(json_dir, f)),
    reverse=True
)
for f in files:
    lb.insert(tk.END, f)

def open_item(event):
    sel = lb.curselection()
    if not sel:
        return
    chosen = lb.get(sel[0])
    json_path = os.path.join(json_dir, chosen)
    root.destroy()
    # call your GUI's main entrypoint
    gui.main(project_dir, json_path)

lb.bind("<Double-1>", open_item)
root.mainloop()
