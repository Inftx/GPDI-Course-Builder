"""Placeholder Word document exporter."""

from pathlib import Path


def export_word(
    markdown: str,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Return the intended Word output path without creating a document.

    Args:
        markdown: Markdown content to export.
        output_path: Intended destination for the Word document.
        title: Optional document title.

    Returns:
        The intended output path.
    """

    return Path(output_path)
