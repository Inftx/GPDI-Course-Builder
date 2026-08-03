"""Word export helpers for converting Markdown into a .docx document."""

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Inches, Pt


def _style_paragraph(paragraph, font_size: int | None = None) -> None:
    """Apply consistent paragraph formatting for body text and lists."""

    paragraph.style.font.name = "Calibri"
    paragraph.style.font.size = Pt(font_size or 11)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT


def _style_heading(paragraph, level: int) -> None:
    """Apply Word heading styling based on the requested heading levels."""

    paragraph.style = f"Heading {level}"
    paragraph.style.font.name = "Calibri"

    if level == 1:
        paragraph.style.font.size = Pt(20)
        paragraph.style.font.bold = True
    elif level == 2:
        paragraph.style.font.size = Pt(16)
        paragraph.style.font.bold = True
    elif level == 3:
        paragraph.style.font.size = Pt(14)
        paragraph.style.font.bold = True


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
    document.styles["Normal"].font.size = Pt(11)
    document.styles["Normal"].paragraph_format.space_after = Pt(6)
    document.styles["Normal"].paragraph_format.line_spacing = 1.15

    section = document.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    for level in (1, 2, 3):
        heading_style = document.styles[f"Heading {level}"]
        heading_style.font.name = "Calibri"
        heading_style.font.bold = True
        heading_style.font.size = Pt({1: 20, 2: 16, 3: 14}[level])
        heading_style.paragraph_format.space_after = Pt(6)

    lines = markdown_text.splitlines()
    derived_title = None

    for line in lines:
        stripped = line.strip()
        if not derived_title and re.match(r"^#\s+.+", stripped):
            derived_title = stripped[1:].strip()
            break

    heading_title = title or derived_title or "Document"
    title_paragraph = document.add_heading(heading_title, level=1)
    _style_heading(title_paragraph, 1)
    document.add_paragraph()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            document.add_paragraph()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            level = min(len(heading_match.group(1)), 6)
            heading_paragraph = document.add_heading(
                heading_match.group(2).strip(),
                level=level,
            )
            _style_heading(heading_paragraph, level)
            continue

        bullet_match = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bullet_match:
            paragraph = document.add_paragraph(style="List Bullet")
            _style_paragraph(paragraph, font_size=11)
            _add_formatted_runs(paragraph, bullet_match.group(1).strip())
            continue

        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered_match:
            paragraph = document.add_paragraph(style="List Number")
            _style_paragraph(paragraph, font_size=11)
            _add_formatted_runs(paragraph, numbered_match.group(1).strip())
            continue

        paragraph = document.add_paragraph()
        _style_paragraph(paragraph, font_size=11)
        _add_formatted_runs(paragraph, stripped)

    document.save(output_path)
    return output_path
