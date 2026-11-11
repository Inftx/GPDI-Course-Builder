import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from modules.document_analyzer import analyze_document
from modules.document_processor import process_document
from modules.file_manager import (
    save_extracted_text,
    save_formatted_text,
    save_uploaded_file,
)
from modules.knowledge_builder import build_knowledge
from modules.metadata_manager import save_document_metadata


UploadStatus = Literal["success", "failure", "duplicate"]
UploadSignature = tuple[str, str]


@dataclass
class DocumentUploadResult:
    filename: str
    status: UploadStatus
    message: str
    analysis: dict[str, Any] | None = None
    knowledge: dict[str, Any] | None = None
    raw_text: str = ""
    cleaned_text: str = ""
    structured_text: str = ""


def process_uploaded_documents(
    uploaded_files,
    project_name: str,
    attempted_uploads: set[UploadSignature] | None = None,
) -> list[DocumentUploadResult]:
    """Process a submitted batch and return a visible result for each file."""

    if attempted_uploads is None:
        attempted_uploads = set()

    results = []
    for uploaded_file in uploaded_files:
        filename = str(getattr(uploaded_file, "name", "Uploaded document"))
        signature = None
        try:
            digest = hashlib.sha256(uploaded_file.getbuffer()).hexdigest()
            signature = (project_name, digest)
            if signature in attempted_uploads:
                results.append(
                    DocumentUploadResult(
                        filename=filename,
                        status="duplicate",
                        message="This exact document was already submitted in this session.",
                    )
                )
                continue
            if _project_has_processed_content(project_name, digest):
                results.append(
                    DocumentUploadResult(
                        filename=filename,
                        status="duplicate",
                        message=(
                            "An identical document has already been processed "
                            "successfully in this project."
                        ),
                    )
                )
                continue

            stored_path = save_uploaded_file(uploaded_file, project_name)
            processed = process_document(uploaded_file)
            analysis = analyze_document(processed["structured"])

            save_extracted_text(
                processed["clean"],
                stored_path.name,
                project_name,
            )
            save_formatted_text(
                processed["structured"],
                stored_path.name,
                project_name,
            )
            knowledge = build_knowledge(
                processed["structured"],
                stored_path.name,
                project_name,
            )
            save_document_metadata(
                project_name,
                stored_path.name,
                analysis,
                content_hash=digest,
            )
            attempted_uploads.add(signature)
            results.append(
                DocumentUploadResult(
                    filename=stored_path.name,
                    status="success",
                    message="Document processed successfully.",
                    analysis=analysis,
                    knowledge=knowledge,
                    raw_text=processed["raw"],
                    cleaned_text=processed["clean"],
                    structured_text=processed["structured"],
                )
            )
        except Exception as error:
            results.append(
                DocumentUploadResult(
                    filename=filename,
                    status="failure",
                    message=f"Document could not be processed: {error}",
                )
            )

    return results


def _project_has_processed_content(project_name: str, digest: str) -> bool:
    metadata_folder = Path("projects") / project_name / "metadata"
    if not metadata_folder.exists():
        return False
    for metadata_file in metadata_folder.glob("*.json"):
        if not metadata_file.is_file():
            continue
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if (
            isinstance(metadata, dict)
            and isinstance(metadata.get("content_hash"), str)
            and metadata["content_hash"].casefold() == digest.casefold()
        ):
            return True
    return False
