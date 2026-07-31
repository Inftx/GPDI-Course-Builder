"""Display live project and generated-output statistics."""

from datetime import datetime
from pathlib import Path

import streamlit as st


PROJECTS_FOLDER = Path("projects")


def get_projects() -> list[Path]:
    """Return project folders, or an empty list when none exist."""

    if not PROJECTS_FOLDER.exists():
        return []

    return [
        project_folder
        for project_folder in PROJECTS_FOLDER.iterdir()
        if project_folder.is_dir()
    ]


def count_files(folder: Path, pattern: str = "*") -> int:
    """Count matching files in a folder, returning zero when it is absent."""

    if not folder.exists():
        return 0

    return sum(
        file_path.is_file()
        for file_path in folder.rglob(pattern)
    )


def get_recent_outputs(projects: list[Path]) -> list[Path]:
    """Return the five newest generated Markdown files across all projects."""

    output_files = []

    for project_folder in projects:
        output_folder = project_folder / "ai_outputs"

        if output_folder.exists():
            output_files.extend(output_folder.rglob("*.md"))

    return sorted(
        output_files,
        key=lambda file_path: file_path.stat().st_mtime,
        reverse=True,
    )[:5]


st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 Dashboard")
st.markdown("## GPDI AI Lecturer Assistant")

projects = get_projects()
documents_processed = sum(
    count_files(project_folder / "documents")
    for project_folder in projects
)
lesson_plans = sum(
    count_files(
        project_folder / "ai_outputs" / "lesson_plans",
        "*.md",
    )
    for project_folder in projects
)
assessments = sum(
    count_files(
        project_folder / "ai_outputs" / "assessments",
        "*.md",
    )
    for project_folder in projects
)

project_column, document_column, lesson_plan_column, assessment_column = st.columns(4)

with project_column:
    st.metric("Projects", len(projects))

with document_column:
    st.metric("Documents Processed", documents_processed)

with lesson_plan_column:
    st.metric("Lesson Plans", lesson_plans)

with assessment_column:
    st.metric("Assessments", assessments)

st.divider()

recent_project_column, recent_output_column = st.columns(2)

with recent_project_column:

    st.subheader("Recent Projects")

    recent_projects = sorted(
        projects,
        key=lambda project_folder: project_folder.stat().st_mtime,
        reverse=True,
    )[:5]

    if recent_projects:
        for project_folder in recent_projects:
            modified_at = datetime.fromtimestamp(
                project_folder.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")
            st.write(f"**{project_folder.name}** — {modified_at}")
    else:
        st.info("No projects are available yet.")

with recent_output_column:

    st.subheader("Recent AI Outputs")

    recent_outputs = get_recent_outputs(projects)

    if recent_outputs:
        for output_file in recent_outputs:
            created_at = datetime.fromtimestamp(
                output_file.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M")
            st.write(f"**{output_file.name}** — {created_at}")
    else:
        st.info("No AI outputs have been generated yet.")
