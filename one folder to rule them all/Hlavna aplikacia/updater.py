# updater.py
import requests
import os
import sys
import shutil
import tempfile
import subprocess
import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
import threading

GITHUB_API = "https://api.github.com/repos/Fernindo/LastMile/releases/latest"
CURRENT_VERSION = "1.0.0"   # match your Nuitka --product-version


def get_latest_release():
    try:
        response = requests.get(GITHUB_API, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Update check failed:", e)
        return None


def check_for_updates(root=None):
    """
    Check for updates and show GUI prompt if new version is available.
    `root` should be a Tk() or ttkbootstrap.Window instance.
    """
    release = get_latest_release()
    if not release:
        return

    latest_version = release["tag_name"].lstrip("v")
    if latest_version <= CURRENT_VERSION:
        print("No updates available.")
        return

    # Ask the user
    if not messagebox.askyesno(
        "Update available",
        f"New version {latest_version} is available.\n"
        "Do you want to update now?",
        parent=root,
    ):
        return

    # Find .exe asset
    asset = next((a for a in release["assets"] if a["name"].endswith(".exe")), None)
    if not asset:
        messagebox.showerror("Update", "No installer found in release.", parent=root)
        return

    url = asset["browser_download_url"]

    # Create progress window
    win = tb.Toplevel(root)
    win.title("Updating...")
    win.geometry("400x120")

    label = tb.Label(win, text="Downloading update...")
    label.pack(pady=10)

    progress = tb.Progressbar(win, mode="determinate", length=350)
    progress.pack(pady=10)

    def do_download():
        temp_dir = tempfile.mkdtemp()
        new_exe_path = os.path.join(temp_dir, asset["name"])
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                downloaded = 0
                with open(new_exe_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            progress["value"] = downloaded / total * 100
                            win.update_idletasks()
            label.config(text="Download complete. Restarting...")
            if sys.platform == "win32":
                subprocess.Popen([new_exe_path])
                sys.exit(0)
            else:
                messagebox.showinfo("Update", "Download finished. Please restart manually.", parent=win)
        except Exception as e:
            messagebox.showerror("Update failed", str(e), parent=win)
            win.destroy()

    threading.Thread(target=do_download, daemon=True).start()
