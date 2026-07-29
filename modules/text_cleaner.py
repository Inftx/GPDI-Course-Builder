import re


def clean_text(text: str) -> str:
    """
    Cleans extracted document text while preserving
    the original document structure.

    This function:
    - Removes excessive spaces
    - Removes tabs
    - Normalizes line endings
    - Preserves paragraphs
    - Preserves headings
    - Preserves numbered/bulleted lists
    """

    if not text:
        return ""

    # Normalize Windows line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Remove multiple spaces (NOT newlines)
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove spaces before and after line breaks
    text = re.sub(r" *\n *", "\n", text)

    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing spaces
    text = "\n".join(line.rstrip() for line in text.splitlines())

    return text.strip()