"""Context retrieval utilities for Retrieval-Augmented Generation."""

from services.rag.indexer import search_index


def retrieve_context(index, query, max_chunks=5):
    """Return the highest-ranked matching chunks as formatted context.

    Matching records are selected by relevance using ``search_index`` and then
    returned in their original document order. At most ``max_chunks`` records
    are included in the formatted context.
    """

    if max_chunks <= 0:
        return ""

    ranked_chunks = search_index(index, query)[:max_chunks]
    selected_ids = {
        chunk["id"]
        for chunk in ranked_chunks
    }
    ordered_chunks = [
        chunk
        for chunk in index
        if chunk["id"] in selected_ids
    ]

    return "\n\n".join(
        (
            "================================\n"
            f"{chunk['title']}\n\n"
            f"{chunk['content']}"
        )
        for chunk in ordered_chunks
    )
