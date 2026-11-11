"""Knowledge-index creation and search utilities for RAG documents."""

import re
from collections import Counter


STOP_WORDS = {
    "about", "after", "again", "against", "also", "among", "and",
    "are", "because", "been", "before", "being", "between", "both",
    "but", "can", "could", "each", "every", "for", "from", "have",
    "into", "more", "most", "must", "not", "only", "other", "over",
    "same", "should", "such", "than", "that", "their", "them", "then",
    "there", "these", "they", "this", "those", "through", "under",
    "upon", "using", "were", "what", "when", "where", "which", "while",
    "will", "with", "would", "your", "context", "course", "document",
    "module", "section",
}


def _extract_keywords(text):
    """Return the 15 most frequent meaningful words in text."""

    words = re.findall(r"\b\w+\b", text.lower())
    keywords = [
        word
        for word in words
        if len(word) >= 4 and word not in STOP_WORDS
    ]

    return [
        word
        for word, _ in Counter(keywords).most_common(15)
    ]


def build_index(chunks):
    """Build ordered searchable records from document chunks.

    Args:
        chunks: Dictionaries containing ``title`` and ``content`` keys.

    Returns:
        A list of records containing chunk metadata and extracted keywords.
    """

    index = []

    for record_id, chunk in enumerate(chunks, start=1):
        content = chunk["content"]

        index.append(
            {
                "id": record_id,
                "title": chunk["title"],
                "content": content,
                "word_count": len(re.findall(r"\b\w+\b", content)),
                "keywords": _extract_keywords(content),
            }
        )

    return index


def search_index(index, query):
    """Return indexed records matching query terms, ordered by relevance.

    Title matches receive the greatest weight, followed by keyword and content
    matches. Records with equal relevance retain their original index order.
    """

    query_terms = {
        word
        for word in re.findall(r"\b\w+\b", query.lower())
        if len(word) >= 4 and word not in STOP_WORDS
    }

    if not query_terms:
        return []

    scored_records = []

    for position, record in enumerate(index):
        title_terms = set(re.findall(r"\b\w+\b", record["title"].lower()))
        keyword_terms = set(record["keywords"])
        content_terms = set(
            re.findall(r"\b\w+\b", record["content"].lower())
        )

        title_matches = len(query_terms & title_terms)
        keyword_matches = len(query_terms & keyword_terms)
        content_matches = len(query_terms & content_terms)
        relevance = (
            title_matches * 3
            + keyword_matches * 2
            + content_matches
        )

        if relevance:
            scored_records.append((relevance, position, record))

    scored_records.sort(key=lambda item: (-item[0], item[1]))

    return [record for _, _, record in scored_records]
