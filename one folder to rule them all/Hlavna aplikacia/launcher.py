import os, sys, subprocess, tkinter as tk
from tkinter import messagebox

# Determine paths & python command
if getattr(sys, "frozen", False):
    project_dir = os.getcwd()
    python_cmd  = "python"              # <-- use system Python
else:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    python_cmd  = sys.executable       # <-- when running as script

json_dir = os.path.join(project_dir, "projects")
if not os.path.isdir(json_dir):
    messagebox.showerror("Error", "Missing 'projects' folder.")
    sys.exit(1)

def open_item(evt):
    sel = lb.curselection()
    if not sel: 
        return
    fn   = lb.get(sel[0])
    full = os.path.join(json_dir, fn)
    subprocess.Popen([
        python_cmd,
        os.path.join(project_dir, "gui.py"),
        project_dir,
        full
    ], cwd=project_dir)

root = tk.Tk()
root.title("Archive — " + os.path.basename(project_dir))

lb = tk.Listbox(root, width=60, height=20)
lb.pack(fill=tk.BOTH, expand=True)
lb.bind("<Double-1>", open_item)

for f in sorted(os.listdir(json_dir), 
                key=lambda f: os.path.getmtime(os.path.join(json_dir, f)), 
                reverse=True):
    if f.lower().endswith(".json"):
        lb.insert(tk.END, f)

root.mainloop()
