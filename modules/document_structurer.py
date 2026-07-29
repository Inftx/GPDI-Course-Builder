import re


SECTION_HEADINGS = [

    "Purpose",

    "Entry Requirements",

    "Exit Level Outcomes",

    "Learning Outcomes",

    "Knowledge Requirements",

    "Assessment Criteria",

    "Internal Assessment",

    "External Assessment",

    "Practical Activities",

    "Workplace Activities",

    "Integrated Assessment",

    "Resources",

    "References"

]


def structure_document(text: str) -> str:
    """
    Improves readability without changing
    any educational content.
    """

    lines = text.splitlines()

    structured = []

    for line in lines:

        line = line.strip()

        if not line:
            structured.append("")
            continue

        # -----------------------------
        # MODULE HEADINGS
        # -----------------------------

        if re.match(r"Module\s+\d+", line, re.IGNORECASE):

            structured.append("")
            structured.append("=" * 70)
            structured.append(line.upper())
            structured.append("=" * 70)
            structured.append("")

            continue

        # -----------------------------
        # KNOWLEDGE MODULES
        # -----------------------------

        if re.match(
            r"Knowledge Module\s+\d+",
            line,
            re.IGNORECASE
        ):

            structured.append("")
            structured.append("=" * 70)
            structured.append(line.upper())
            structured.append("=" * 70)
            structured.append("")

            continue

        # -----------------------------
        # PRACTICAL MODULES
        # -----------------------------

        if re.match(
            r"Practical Module\s+\d+",
            line,
            re.IGNORECASE
        ):

            structured.append("")
            structured.append("=" * 70)
            structured.append(line.upper())
            structured.append("=" * 70)
            structured.append("")

            continue

        # -----------------------------
        # WORK EXPERIENCE MODULES
        # -----------------------------

        if re.match(
            r"Work Experience Module\s+\d+",
            line,
            re.IGNORECASE
        ):

            structured.append("")
            structured.append("=" * 70)
            structured.append(line.upper())
            structured.append("=" * 70)
            structured.append("")

            continue

        # -----------------------------
        # STANDARD HEADINGS
        # -----------------------------

        matched = False

        for heading in SECTION_HEADINGS:

            if line.lower() == heading.lower():

                structured.append("")
                structured.append(line.upper())
                structured.append("-" * len(line))
                structured.append("")

                matched = True
                break

        if matched:
            continue

        structured.append(line)

    return "\n".join(structured)