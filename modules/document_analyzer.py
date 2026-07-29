import re
from collections import Counter


def analyze_document(text):
    """
    Analyzes an extracted document and returns
    useful statistics and detected headings.
    """

    headings = []

    patterns = [
        r"Module\s+\d+",
        r"Learning Outcomes?",
        r"Assessment Criteria",
        r"Knowledge Requirements?",
        r"Practical Activities?",
        r"Workplace Activities?"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        headings.extend(matches)

    words = re.findall(
        r"\b\w+\b",
        text.lower()
    )

    word_count = len(words)

    character_count = len(text)

    estimated_pages = max(
        1,
        round(word_count / 500)
    )

    reading_time = max(
        1,
        round(word_count / 200)
    )

    stop_words = {
        "the", "and", "of", "to", "a",
        "in", "is", "for", "on", "with",
        "that", "this", "as", "by",
        "an", "be", "or", "are", "at",
        "from"
    }

    filtered_words = [
        word
        for word in words
        if word not in stop_words
        and len(word) > 3
    ]

    keywords = Counter(
        filtered_words
    ).most_common(10)

    return {

        "headings": sorted(
            list(set(headings))
        ),

        "word_count": word_count,

        "character_count": character_count,

        "estimated_pages": estimated_pages,

        "reading_time": reading_time,

        "keywords": keywords

    }

def save_formatted_text(
    text,
    original_filename,
    project_name
):
    """
    Saves the formatted version of an extracted document.
    """

    from pathlib import Path

    project_folder = Path("projects") / project_name

    formatted_folder = project_folder / "formatted"

    formatted_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        Path(original_filename).stem
        + "_formatted.txt"
    )

    file_path = formatted_folder / filename

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(text)

    return file_path