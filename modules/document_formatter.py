import re


SECTION_PATTERNS = [

    "Learning Outcomes",

    "Assessment Criteria",

    "Knowledge Requirements",

    "Practical Activities",

    "Workplace Activities",

    "Internal Assessment",

    "External Assessment",

    "Purpose",

    "Entry Requirements",

    "Module"

]


def format_document(text):

    """
    Improves readability of educational documents
    while preserving every piece of content.
    """

    lines = text.splitlines()

    formatted = []

    for line in lines:

        line = line.strip()

        if not line:
            formatted.append("")
            continue

        # Module headings

        if re.match(r"Module\s+\d+", line, re.IGNORECASE):

            formatted.append("")
            formatted.append("=" * 60)
            formatted.append(line.upper())
            formatted.append("=" * 60)
            formatted.append("")

            continue

        # Standard educational headings

        matched = False

        for heading in SECTION_PATTERNS:

            if line.lower() == heading.lower():

                formatted.append("")
                formatted.append(line.upper())
                formatted.append("-" * len(line))
                formatted.append("")

                matched = True
                break

        if matched:
            continue

        formatted.append(line)

    return "\n".join(formatted)