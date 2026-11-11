from pathlib import Path


def save_uploaded_file(uploaded_file, project_name):
    project_folder = Path("projects") / project_name
    documents_folder = project_folder / "documents"
    documents_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = Path(uploaded_file.name).name
    if not filename or filename in (".", ".."):
        raise ValueError("The uploaded document must have a valid filename.")

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    collision = 0
    while True:
        candidate_name = (
            filename
            if collision == 0
            else f"{stem} ({collision}){suffix}"
        )
        file_path = documents_folder / candidate_name
        if not _upload_outputs_exist(project_folder, candidate_name):
            try:
                with file_path.open("xb") as file:
                    file.write(uploaded_file.getbuffer())
                return file_path
            except FileExistsError:
                pass
        collision += 1


def save_extracted_text(
    text,
    original_filename,
    project_name
):
    """
    Saves the cleaned extracted text.
    """

    project_folder = Path("projects") / project_name

    extracted_folder = (
        project_folder / "extracted_text"
    )

    extracted_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        Path(original_filename).stem
        + "_clean.txt"
    )

    file_path = (
        extracted_folder / filename
    )

    with file_path.open("x", encoding="utf-8") as file:

        file.write(text)

    return file_path


def save_formatted_text(
    text,
    original_filename,
    project_name
):
    """
    Saves the structured version of the document.
    """

    project_folder = Path("projects") / project_name

    formatted_folder = (
        project_folder / "formatted"
    )

    formatted_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        Path(original_filename).stem
        + "_structured.txt"
    )

    file_path = (
        formatted_folder / filename
    )

    with file_path.open("x", encoding="utf-8") as file:

        file.write(text)

    return file_path


def _upload_outputs_exist(project_folder: Path, filename: str) -> bool:
    stem = Path(filename).stem
    return any(
        candidate.exists()
        for candidate in (
            project_folder / "documents" / filename,
            project_folder / "extracted_text" / f"{stem}_clean.txt",
            project_folder / "formatted" / f"{stem}_structured.txt",
            project_folder / "knowledge" / f"{stem}.json",
            project_folder / "metadata" / f"{filename}.json",
            project_folder / "metadata" / f"{stem}.json",
        )
    )