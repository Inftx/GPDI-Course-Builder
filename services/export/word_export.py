"""Compatibility wrapper for the Word document exporter."""

from pathlib import Path

from services.export.word_exporter import export_to_docx


def export_word(
    markdown: str,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Export Markdown content to a Word document."""

    return export_to_docx(markdown, output_path, title)
