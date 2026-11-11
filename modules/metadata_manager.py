from datetime import datetime
import json
import os
from pathlib import Path
import tempfile


def save_document_metadata(
    project_name,
    filename,
    analysis,
    content_hash=None,
):
    """Atomically publish metadata without replacing an existing record."""

    source_filename = Path(filename).name
    metadata_folder = Path("projects") / project_name / "metadata"
    metadata_folder.mkdir(parents=True, exist_ok=True)

    metadata = {
        "filename": source_filename,
        **({"content_hash": content_hash} if content_hash else {}),
        "uploaded": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "word_count": analysis["word_count"],
        "character_count": analysis["character_count"],
        "estimated_pages": analysis["estimated_pages"],
        "reading_time": analysis["reading_time"],
        "headings": analysis["headings"],
        "keywords": analysis["keywords"],
    }

    file_path = metadata_folder / f"{source_filename}.json"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".document-metadata-",
        suffix=".tmp",
        dir=metadata_folder,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)
            file.flush()
            os.fsync(file.fileno())

        try:
            os.link(temporary_path, file_path)
        except FileExistsError as error:
            raise FileExistsError(
                f"Metadata for '{source_filename}' already exists at "
                f"'{file_path}'; refusing to overwrite it."
            ) from error
        return file_path
    finally:
        try:
            temporary_path.unlink()
        except OSError:
            pass