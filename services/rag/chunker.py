"""Utilities for splitting educational documents into logical sections."""

import re


HEADINGS = (
    "Module",
    "Learning Outcomes",
    "Assessment Criteria",
    "Knowledge Requirements",
    "Practical Activities",
    "Workplace Activities",
)


def _get_heading(line):
    """Return a recognised heading and any content that follows it."""

    stripped_line = line.strip()

    module_match = re.match(
        r"^(?P<title>(?:(?:Knowledge|Practical|Work Experience)\s+)?Module\s+\d+[^:]*)"
        r"(?::\s*(?P<content>.*))?$",
        stripped_line,
        flags=re.IGNORECASE,
    )

    if module_match:
        return (
            module_match.group("title"),
            module_match.group("content") or "",
        )

    for heading in HEADINGS[1:]:
        heading_pattern = (
            re.escape(heading[:-1]) + r"s?"
            if heading.endswith("s")
            else re.escape(heading)
        )

        heading_match = re.match(
            rf"^(?P<title>{heading_pattern})(?::\s*(?P<content>.*))?$",
            stripped_line,
            flags=re.IGNORECASE,
        )

        if heading_match:
            return (
                heading_match.group("title"),
                heading_match.group("content") or "",
            )

    return None


def chunk_document(text: str, max_chars: int | None = None) -> list[dict[str, str]]:
    """Split document text into ordered chunks at recognised section headings.

    Each returned chunk is a dictionary with ``title`` and ``content`` keys.
    Text before the first recognised heading is retained in a ``Document`` chunk.
    When ``max_chars`` is set, large sections are split into bounded chunks.
    """

    chunks = []
    current_title = "Document"
    current_lines = []

    for line in text.splitlines():
        heading = _get_heading(line)

        if heading:
            content = "\n".join(current_lines).strip()

            if content:
                chunks.append(
                    {
                        "title": current_title,
                        "content": content,
                    }
                )

            current_title, first_content = heading
            current_lines = [first_content] if first_content else []
            continue

        current_lines.append(line)

    content = "\n".join(current_lines).strip()

    if content:
        chunks.append(
            {
                "title": current_title,
                "content": content,
            }
        )

    if max_chars is None:
        return chunks
    if max_chars < 1:
        raise ValueError("max_chars must be a positive integer.")

    bounded_chunks = []
    for chunk in chunks:
        content = chunk["content"]
        if len(content) <= max_chars:
            bounded_chunks.append(chunk)
            continue

        parts = []
        start = 0
        while start < len(content):
            end = min(start + max_chars, len(content))
            if end < len(content):
                newline = content.rfind("\n", start, end)
                if newline > start:
                    end = newline + 1
            parts.append(content[start:end].strip())
            start = end

        for part_number, part in enumerate(parts, start=1):
            bounded_chunks.append(
                {
                    "title": f"{chunk['title']} (part {part_number})",
                    "content": part,
                }
            )

    return bounded_chunks
