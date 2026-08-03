"""Deterministic knowledge-graph construction from processed course data."""

from __future__ import annotations

from typing import Any


_SECTION_KEYS = {
    "learning_outcomes": "learning_outcomes",
    "assessment_criteria": "assessment_criteria",
    "knowledge_requirements": "knowledge_requirements",
    "practical_activities": "practical_activities",
    "workplace_activities": "workplace_activities",
}


def _normalize_heading(value: str) -> str:
    """Normalize headings for deterministic comparisons."""

    return " ".join(value.strip().split()).upper()


def _is_module_heading(value: str) -> bool:
    """Return True when the line appears to introduce a new module."""

    upper = _normalize_heading(value)
    return upper.startswith("MODULE") or upper.startswith("KNOWLEDGE MODULE") or upper.startswith("PRACTICAL MODULE") or upper.startswith("WORK EXPERIENCE MODULE")


def build_knowledge_graph(course_data: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic module-based knowledge graph from course data.

    The graph is built entirely from the existing processed course.json structure
    and preserves the original order of modules and entries.
    """

    modules = course_data.get("modules", []) or []
    learning_outcomes = course_data.get("learning_outcomes", []) or []
    assessment_criteria = course_data.get("assessment_criteria", []) or []
    knowledge_requirements = course_data.get("knowledge_requirements", []) or []
    practical_activities = course_data.get("practical_activities", []) or []
    workplace_activities = course_data.get("workplace_activities", []) or []

    graph_modules: list[dict[str, Any]] = []
    seen_module_names: set[str] = set()

    for module_name in modules:
        if not module_name or module_name in seen_module_names:
            continue

        seen_module_names.add(module_name)
        graph_modules.append(
            {
                "name": module_name,
                "learning_outcomes": [],
                "assessment_criteria": [],
                "knowledge_requirements": [],
                "practical_activities": [],
                "workplace_activities": [],
            }
        )

    module_lookup = {module["name"]: module for module in graph_modules}
    section_lists = {
        "learning_outcomes": learning_outcomes,
        "assessment_criteria": assessment_criteria,
        "knowledge_requirements": knowledge_requirements,
        "practical_activities": practical_activities,
        "workplace_activities": workplace_activities,
    }

    for section_name, entries in section_lists.items():
        current_module_name: str | None = None
        seen_entries: set[str] = set()

        for entry in entries:
            if not entry:
                continue

            if _is_module_heading(entry):
                if entry in module_lookup:
                    current_module_name = entry
                else:
                    current_module_name = None
                continue

            if current_module_name is None and graph_modules:
                current_module_name = graph_modules[0]["name"]

            if current_module_name is None:
                continue

            normalized_entry = _normalize_heading(entry)
            if normalized_entry in seen_entries:
                continue

            seen_entries.add(normalized_entry)
            module_lookup[current_module_name][_SECTION_KEYS[section_name]].append(entry)

    return {"modules": graph_modules}


def get_module(graph: dict[str, Any], module_name: str) -> dict[str, Any] | None:
    """Return the matching module dictionary, if present."""

    for module in graph.get("modules", []):
        if module.get("name") == module_name:
            return module
    return None


def list_modules(graph: dict[str, Any]) -> list[str]:
    """Return a list of module names in graph order."""

    return [module.get("name", "") for module in graph.get("modules", [])]
