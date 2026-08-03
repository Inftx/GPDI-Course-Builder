"""Persistent storage helpers for RAG indexes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_index(index: Any, project_name: str) -> Path:
    """Persist a RAG index for a project to disk."""

    project_folder = Path("projects") / project_name
    rag_folder = project_folder / "rag"
    rag_folder.mkdir(parents=True, exist_ok=True)

    index_path = rag_folder / "index.json"
    with index_path.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=4, ensure_ascii=False)

    return index_path


def load_index(project_name: str) -> Any | None:
    """Load a persisted RAG index for a project, if it exists."""

    index_path = Path("projects") / project_name / "rag" / "index.json"
    if not index_path.exists():
        return None

    with index_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
