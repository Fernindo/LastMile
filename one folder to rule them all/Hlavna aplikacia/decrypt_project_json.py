#!/usr/bin/env python3
"""
GUI tool to temporarily decrypt a project JSON file created with secure_save_json.

- Opens a file dialog starting in AppData\Roaming\LastMile
- Decrypts it with helpers.secure_load_json
- Writes a plain JSON copy next to it: <name>_decrypted.json
- Also makes a backup of the original
"""

import os
import sys
import json
import datetime
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

# Make sure helpers.py is importable (adjust path if needed)
here = os.path.dirname(os.path.abspath(__file__))
if here not in sys.path:
    sys.path.insert(0, here)

from helpers import secure_load_json, secure_save_json


def decrypt_file(src_path: str) -> str:
    """Decrypt the project JSON and return path of the plain copy."""
    # backup first
    bak_name = f"{src_path}.bak_{datetime.datetime.now():%Y%m%d_%H%M%S}"
    try:
        shutil.copy2(src_path, bak_name)
    except Exception as e:
        messagebox.showwarning("Warning", f"Backup failed: {e}")

    # load & decrypt
    data = secure_load_json(src_path, default={})

    # save plain
    out_path = os.path.splitext(src_path)[0] + "_decrypted.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return out_path


def main():
    root = tk.Tk()
    root.withdraw()  # hide main window

    # Start directly in your AppData\Roaming\LastMile folder
    start_dir = r"C:\Users\slaso\AppData\Roaming\LastMile"

    file_path = filedialog.askopenfilename(
        title="Select encrypted project JSON",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir=start_dir
    )
    if not file_path:
        return

    try:
        out = decrypt_file(file_path)
        messagebox.showinfo("Success", f"Decrypted copy saved as:\n{out}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to decrypt:\n{e}")


if __name__ == "__main__":
    main()
