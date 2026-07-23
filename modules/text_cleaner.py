import re


def clean_text(text):
    """
    Cleans extracted document text by removing
    unnecessary whitespace and blank lines.
    """

    # Replace multiple spaces with one space
    text = re.sub(r"[ \t]+", " ", text)

    # Remove extra blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text