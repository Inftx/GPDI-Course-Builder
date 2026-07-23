import json

from pathlib import Path

from datetime import datetime


def save_document_metadata(

    project_name,

    filename,

    analysis

):
    """
    Saves document metadata for a project.
    """

    project_folder = (
        Path("projects")
        / project_name
    )

    metadata_folder = (
        project_folder
        / "metadata"
    )

    metadata_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    metadata = {

        "filename": filename,

        "uploaded":

        datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),

        "word_count":

        analysis["word_count"],

        "character_count":

        analysis["character_count"],

        "estimated_pages":

        analysis["estimated_pages"],

        "reading_time":

        analysis["reading_time"],

        "headings":

        analysis["headings"],

        "keywords":

        analysis["keywords"]

    }

    file_path = (

        metadata_folder /

        (

            Path(filename).stem

            + ".json"

        )

    )

    with open(

        file_path,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            metadata,

            file,

            indent=4

        )

    return file_path