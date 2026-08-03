"""Word export helpers for converting Markdown into a .docx document."""

import re
from pathlib import Path

from docx import Document


def _add_formatted_runs(paragraph, text: str) -> None:
    """Add paragraph text with bold markers converted to bold runs."""

    pattern = re.compile(r"(\*\*[^*]+\*\*)")
    last_index = 0

    for match in pattern.finditer(text):
        if match.start() > last_index:
            paragraph.add_run(text[last_index:match.start()])

        bold_text = match.group(1)[2:-2]
        run = paragraph.add_run(bold_text)
        run.bold = True

        last_index = match.end()

    if last_index < len(text):
        paragraph.add_run(text[last_index:])


def export_to_docx(
    markdown_text: str,
    output_path: str | Path,
    title: str | None = None,
) -> Path:
    """Convert Markdown content into a .docx document.

    The exporter supports:
    - Markdown headings as Word headings
    - Bullet lists and numbered lists
    - Paragraphs
    - Bold inline formatting
    - A document title derived from the first heading or supplied title
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = Document()
    document.styles["Normal"].font.name = "Calibri"
    document.styles["Normal"].font.size = 11

    lines = markdown_text.splitlines()
    derived_title = None

    for line in lines:
        stripped = line.strip()
        if not derived_title and re.match(r"^#\s+.+", stripped):
            derived_title = stripped[1:].strip()
            break

    heading_title = title or derived_title or "Document"
    document.add_heading(heading_title, level=1)
    document.add_paragraph()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            document.add_paragraph()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            level = min(len(heading_match.group(1)), 6)
            document.add_heading(heading_match.group(2).strip(), level=level)
            continue

        bullet_match = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bullet_match:
            paragraph = document.add_paragraph(style="List Bullet")
            _add_formatted_runs(paragraph, bullet_match.group(1).strip())
            continue

        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered_match:
            paragraph = document.add_paragraph(style="List Number")
            _add_formatted_runs(paragraph, numbered_match.group(1).strip())
            continue

        paragraph = document.add_paragraph()
        _add_formatted_runs(paragraph, stripped)

    document.save(output_path)
    return output_path
