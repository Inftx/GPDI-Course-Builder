from pathlib import Path


def save_uploaded_file(uploaded_file, project_name):
    """
    Saves the original uploaded document.
    """

    project_folder = Path("projects") / project_name
    documents_folder = project_folder / "documents"

    documents_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = documents_folder / uploaded_file.name

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    return file_path


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

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

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

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(text)

    return file_path