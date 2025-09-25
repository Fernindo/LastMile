# updater.py
import requests
import os
import sys
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *

LATEST_JSON = "https://fernindo.github.io/LastMile/latest.json"
CURRENT_VERSION = "1.0.0"   # match your Nuitka --product-version


def get_latest_release():
    """Fetch release info from the hosted latest.json file."""
    try:
        response = requests.get(LATEST_JSON, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Update check failed:", e)
        return None


def check_for_updates(root):
    """
    Show update popup inside the Project Selector window (root).
    """
    release = get_latest_release()
    if not release:
        return

    latest_version = release.get("tag_name", "").lstrip("v")
    if not latest_version or latest_version <= CURRENT_VERSION:
        print("No updates available.")
        return

    # Find .exe asset
    asset = next((a for a in release.get("assets", []) if a["name"].endswith(".exe")), None)
    if not asset:
        print("No .exe file found in release.")
        return

    url = asset["browser_download_url"]

    # Create popup window as child of Project Selector
    win = tb.Toplevel(root)
    win.title("Update Available")
    win.geometry("420x200")
    win.resizable(False, False)
    win.transient(root)       # keep above parent
    win.grab_set()            # make modal

    # Info label
    label = ttk.Label(
        win,
        text=f"New version {latest_version} is available.\nDo you want to update now?",
        justify="center",
        font=("Segoe UI", 11)
    )
    label.pack(pady=20)

    # Progress bar (hidden at first)
    progress = ttk.Progressbar(win, mode="determinate", length=350)
    progress.pack(pady=10)
    progress.pack_forget()

    def do_download():
        progress.pack(pady=10)
        label.config(text="Downloading update...")
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
                try:
                    current_exe = sys.executable

                    # Backup old exe just in case
                    backup_exe = current_exe + ".bak"
                    try:
                        if os.path.exists(backup_exe):
                            os.remove(backup_exe)
                        os.rename(current_exe, backup_exe)
                    except Exception:
                        pass

                    # Replace with new exe
                    shutil.copy2(new_exe_path, current_exe)

                    # Relaunch instantly
                    os.execl(current_exe, current_exe, *sys.argv)

                except Exception as e:
                    label.config(text=f"Update failed:\n{e}")
            else:
                label.config(text="Download finished. Please restart manually.")

        except Exception as e:
            label.config(text=f"Update failed:\n{e}")

    # Button actions
    def start_update():
        update_btn.config(state="disabled")
        skip_btn.config(state="disabled")
        threading.Thread(target=do_download, daemon=True).start()

    def skip_update():
        win.destroy()

    # Buttons
    btn_frame = ttk.Frame(win)
    btn_frame.pack(pady=5)

    update_btn = ttk.Button(btn_frame, text="Update", bootstyle=SUCCESS, command=start_update)
    update_btn.grid(row=0, column=0, padx=10)

    skip_btn = ttk.Button(btn_frame, text="Skip", bootstyle=SECONDARY, command=skip_update)
    skip_btn.grid(row=0, column=1, padx=10)
