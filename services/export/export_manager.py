"""Route Markdown export requests to the appropriate exporter."""

from pathlib import Path

from services.export.pdf_export import export_pdf
from services.export.ppt_export import export_presentation
from services.export.word_export import export_word


def export_document(
    markdown: str,
    output_format: str,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Export Markdown through the selected document exporter.

    Args:
        markdown: Markdown content to export.
        output_format: Supported format: ``docx``, ``pptx``, or ``pdf``.
        output_path: Intended destination for the exported file.
        title: Optional document title.

    Returns:
        The exported file path.

    Raises:
        ValueError: If ``output_format`` is unsupported.
    """

    exporters = {
        "docx": export_word,
        "pptx": export_presentation,
        "pdf": export_pdf,
    }
    normalised_format = output_format.lower()

    try:
        exporter = exporters[normalised_format]
    except KeyError as error:
        raise ValueError(
            f"Unsupported export format: {output_format}"
        ) from error

    return exporter(markdown, output_path, title)
