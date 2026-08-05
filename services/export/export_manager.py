"""Route Markdown export requests to the appropriate exporter."""

from pathlib import Path

from services.export.pdf_export import export_pdf
from services.export.ppt_export import export_presentation
from services.export.word_exporter import export_to_docx


def export_document(
    markdown_text: str,
    output_type: str,
    output_path: str | Path,
    title: str | None = None,
    include_logo: bool = False,
) -> Path:
    """Export Markdown through the selected document exporter.

    Args:
        markdown_text: Markdown content to export.
        output_type: Supported format: ``docx``.
        output_path: Intended destination for the exported file.
        title: Optional document title.
        include_logo: Include GPDI branding logo in DOCX exports.

    Returns:
        The exported file path.

    Raises:
        ValueError: If ``output_type`` is unsupported.
    """

    exporters = {
        "docx": export_to_docx,
        "pptx": export_presentation,
        "pdf": export_pdf,
    }
    normalised_format = output_type.lower()

    try:
        exporter = exporters[normalised_format]
    except KeyError as error:
        raise ValueError(
            f"Unsupported export format: {output_type}"
        ) from error

    if normalised_format == "docx":
        return exporter(
            markdown_text,
            output_path,
            title,
            include_logo=include_logo,
        )

    return exporter(markdown_text, output_path, title)
