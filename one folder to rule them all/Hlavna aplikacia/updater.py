import requests
import os
import sys
import shutil
import tempfile
import subprocess

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


def check_for_updates():
    release = get_latest_release()
    if not release:
        return

    latest_version = release["tag_name"].lstrip("v")
    if latest_version <= CURRENT_VERSION:
        print("No updates available.")
        return

    print(f"New version {latest_version} available!")

    # Find .exe asset
    asset = next((a for a in release["assets"] if a["name"].endswith(".exe")), None)
    if not asset:
        print("No installer found in release.")
        return

    url = asset["browser_download_url"]
    print("Downloading from:", url)

    # Download to temp file
    temp_dir = tempfile.mkdtemp()
    new_exe_path = os.path.join(temp_dir, asset["name"])

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(new_exe_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    print("Downloaded update to", new_exe_path)

    # Relaunch new version, close current one
    if sys.platform == "win32":
        print("Restarting with new version...")
        subprocess.Popen([new_exe_path])
        sys.exit(0)
    else:
        print("Manual restart required.")
