"""Placeholder PowerPoint document exporter."""

from pathlib import Path


def export_presentation(
    markdown: str,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Return the intended PowerPoint output path without creating a file.

    Args:
        markdown: Markdown content to export.
        output_path: Intended destination for the PowerPoint presentation.
        title: Optional presentation title.

    Returns:
        The intended output path.
    """

    return Path(output_path)
