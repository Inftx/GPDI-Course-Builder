"""Persist and retrieve generated AI output files."""

from datetime import datetime
from pathlib import Path


OUTPUT_FOLDERS = {
    "lesson_plan": "lesson_plans",
    "lesson_plans": "lesson_plans",
    "facilitator_guide": "facilitator_guides",
    "facilitator_guides": "facilitator_guides",
    "assessment": "assessments",
    "assessments": "assessments",
    "quiz": "quizzes",
    "quizzes": "quizzes",
    "teaching_script": "teaching_scripts",
    "teaching_scripts": "teaching_scripts",
    "student_note": "student_notes",
    "student_notes": "student_notes",
    "powerpoint": "powerpoints",
    "powerpoints": "powerpoints",
}


def _normalise_output_type(output_type: str) -> str:
    """Return the storage folder for a supported output type.

    Args:
        output_type: A singular or plural output category, using spaces,
            hyphens, or underscores.

    Raises:
        ValueError: If the output type is not supported.
    """

    normalised_type = output_type.lower().replace("-", "_").replace(" ", "_")

    try:
        return OUTPUT_FOLDERS[normalised_type]
    except KeyError as error:
        raise ValueError(
            f"Unknown output type: {output_type}"
        ) from error


def _get_output_folders(project_name: str) -> dict[str, Path]:
    """Create and return every AI-output folder for a project."""

    output_root = Path("projects") / project_name / "ai_outputs"
    folders = {
        folder_name: output_root / folder_name
        for folder_name in set(OUTPUT_FOLDERS.values())
    }

    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    return folders


def save_output(project_name: str, output_type: str, content: str) -> Path:
    """Save generated content as a timestamped Markdown file.

    Args:
        project_name: Name of the project that owns the generated output.
        output_type: Supported output category, such as ``lesson_plan``.
        content: Markdown content to save.

    Returns:
        The full path to the saved Markdown file.
    """

    output_folder = _normalise_output_type(output_type)
    folders = _get_output_folders(project_name)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.md")
    output_path = folders[output_folder] / filename

    output_path.write_text(content, encoding="utf-8")

    return output_path


def list_outputs(project_name: str, output_type: str) -> list[Path]:
    """Return a project's Markdown outputs, newest first.

    Args:
        project_name: Name of the project that owns the generated outputs.
        output_type: Supported output category to list.

    Returns:
        Markdown file paths ordered from newest to oldest.
    """

    output_folder = _normalise_output_type(output_type)
    folders = _get_output_folders(project_name)

    return sorted(
        folders[output_folder].glob("*.md"),
        key=lambda file_path: file_path.stat().st_mtime,
        reverse=True,
    )


def load_output(file_path: str | Path) -> str:
    """Load and return the Markdown content at a saved output path.

    Args:
        file_path: Path to the generated Markdown file.

    Returns:
        The file's UTF-8 decoded contents.
    """

    return Path(file_path).read_text(encoding="utf-8")
