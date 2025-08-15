import os
import json
import datetime
from typing import List, Dict

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "ui_settings.json")
DEFAULT_TEMPLATE = {"data": "Default session content."}


def load_app_settings() -> Dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_app_settings(data: Dict) -> None:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_projects_root(settings: Dict) -> str:
    return settings.get("projects_root", "")


def set_projects_root(path: str) -> None:
    settings = load_app_settings()
    settings["projects_root"] = path
    save_app_settings(settings)


def discover_projects(root: str) -> List[Dict]:
    projects: List[Dict] = []
    if not root or not os.path.isdir(root):
        return projects
    for name in os.listdir(root):
        project_path = os.path.join(root, name)
        if os.path.isdir(project_path):
            projects.append({"name": name, "path": project_path})
    projects.sort(key=lambda p: p["name"].lower())
    return projects


def _sort_key(fname: str, folder: str) -> float:
    name, _ = os.path.splitext(fname)
    if "_" in name:
        base, date_part = name.split("_", 1)
        try:
            dt = datetime.datetime.strptime(date_part, "%Y-%m-%d_%H-%M-%S")
            return dt.timestamp()
        except ValueError:
            pass
    return os.path.getmtime(os.path.join(folder, fname))


def get_project_archive(project_path: str) -> List[str]:
    json_dir = os.path.join(project_path, "projects")
    if not os.path.isdir(json_dir):
        return []
    files = [f for f in os.listdir(json_dir) if f.lower().endswith(".json")]
    files.sort(key=lambda f: _sort_key(f, json_dir), reverse=True)
    return [os.path.join(json_dir, f) for f in files]


def create_project(root: str, name: str) -> Dict:
    project_dir = os.path.join(root, name)
    json_dir = os.path.join(project_dir, "projects")
    os.makedirs(json_dir, exist_ok=True)
    json_path = os.path.join(json_dir, f"{name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_TEMPLATE, f, ensure_ascii=False, indent=2)
    return {"name": name, "path": project_dir, "json_path": json_path}
