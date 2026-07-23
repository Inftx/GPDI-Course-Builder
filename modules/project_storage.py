import json
from pathlib import Path

PROJECTS_FOLDER = Path("projects")


def ensure_projects_folder():
    PROJECTS_FOLDER.mkdir(exist_ok=True)


def save_project(project_path, data):
    with open(project_path / "project.json", "w") as file:
        json.dump(data, file, indent=4)


def load_project(project_path):
    with open(project_path / "project.json", "r") as file:
        return json.load(file)