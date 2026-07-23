from pathlib import Path

from modules.project_storage import (
    ensure_projects_folder,
    save_project
)


PROJECTS_FOLDER = Path("projects")


def create_project(project_name):

    ensure_projects_folder()

    project_path = PROJECTS_FOLDER / project_name

    if project_path.exists():
        return False, "Project already exists."

    project_path.mkdir()

    (project_path / "documents").mkdir()

    (project_path / "extracted_text").mkdir()

    (project_path / "exports").mkdir()


    metadata = {
        "name": project_name,
        "status": "New",
        "documents": {},
        "analysis": {},
        "lesson_plan": {},
        "student_notes": {},
        "assessment": {},
        "powerpoint": {}
    }


    save_project(
        project_path,
        metadata
    )


    return True, "Project created successfully."



def get_projects():

    ensure_projects_folder()

    projects = []

    for folder in PROJECTS_FOLDER.iterdir():

        if folder.is_dir():

            projects.append(folder.name)

    projects.sort()

    return projects



def prepare_project_structure(project_name):

    project_path = PROJECTS_FOLDER / project_name

    required_folders = [
        "documents",
        "extracted_text",
        "exports"
    ]


    for folder in required_folders:

        folder_path = project_path / folder

        folder_path.mkdir(
            exist_ok=True
        )