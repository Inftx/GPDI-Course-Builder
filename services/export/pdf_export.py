"""Placeholder PDF document exporter."""

from pathlib import Path


def export_pdf(
    markdown: str,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Return the intended PDF output path without creating a document.

    Args:
        markdown: Markdown content to export.
        output_path: Intended destination for the PDF document.
        title: Optional document title.

    Returns:
        The intended output path.
    """

    return Path(output_path)
