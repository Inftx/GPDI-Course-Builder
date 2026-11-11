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

    learning_outcomes = course_data.get("learning_outcomes", []) or []
    assessment_criteria = course_data.get("assessment_criteria", []) or []
    knowledge_requirements = course_data.get("knowledge_requirements", []) or []
    practical_activities = course_data.get("practical_activities", []) or []
    workplace_activities = course_data.get("workplace_activities", []) or []

    graph_modules: list[dict[str, Any]] = []
    seen_module_names: set[str] = set()

    def add_module(module_name: str, aliases: list[str] | None = None) -> None:
        if not module_name:
            return
        normalized_aliases = {
            str(alias).strip().casefold()
            for alias in (aliases or [])
            if alias
        }
        existing = next(
            (
                module
                for module in graph_modules
                if module_name.strip().casefold()
                in {
                    module["name"].casefold(),
                    *(alias.casefold() for alias in module["aliases"]),
                }
                or normalized_aliases.intersection(
                    {
                        module["name"].casefold(),
                        *(alias.casefold() for alias in module["aliases"]),
                    }
                )
            ),
            None,
        )
        if existing:
            if len(module_name) > len(existing["name"]):
                existing["name"] = module_name
            existing["aliases"] = list(
                dict.fromkeys(
                    [
                        *existing["aliases"],
                        *(str(alias).strip() for alias in aliases or [] if alias),
                    ]
                )
            )
            return

        seen_module_names.add(module_name)
        graph_modules.append(
            {
                "name": module_name,
                "aliases": list(dict.fromkeys(str(alias).strip() for alias in aliases or [] if alias)),
                "learning_outcomes": [],
                "assessment_criteria": [],
                "knowledge_requirements": [],
                "practical_activities": [],
                "workplace_activities": [],
            }
        )

    for record in course_data.get("module_records", []) or []:
        if not isinstance(record, dict):
            continue
        code = str(record.get("code") or record.get("identifier") or "").strip()
        title = str(record.get("title") or record.get("name") or "").strip()
        record_name = f"{code}: {title}" if code and title else title or code
        if record_name:
            add_module(record_name, [code, title, str(record.get("id") or "")])

    for value in course_data.get("modules", []) or []:
        if isinstance(value, dict):
            code = str(value.get("code") or value.get("identifier") or "").strip()
            title = str(value.get("title") or value.get("name") or "").strip()
            module_name = f"{code}: {title}" if code and title else title or code
            if module_name:
                add_module(module_name, [code, title, str(value.get("id") or "")])
            continue
        module_name = str(value).strip()
        if module_name:
            parts = [part.strip() for part in module_name.split(":", 1)]
            add_module(module_name, parts)

    for topic in course_data.get("knowledge_topics", []) or []:
        if not isinstance(topic, dict):
            continue
        title = str(topic.get("title", "")).strip()
        code = str(topic.get("code", "")).strip()
        name = ": ".join(part for part in (code, title) if part)
        if not name or name in seen_module_names:
            continue
        seen_module_names.add(name)
        graph_modules.append(
            {
                "name": name,
                "aliases": [part for part in (code, title) if part],
                "learning_outcomes": [],
                "assessment_criteria": [],
                "knowledge_requirements": [
                    str(item.get("description", item))
                    if isinstance(item, dict)
                    else str(item)
                    for item in topic.get("knowledge_items", [])
                ],
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
    """Return a module matched by its full name, code, or topic title."""

    normalized_name = _normalize_heading(module_name)
    for module in graph.get("modules", []):
        if normalized_name in {
            _normalize_heading(module.get("name", "")),
            *(
                _normalize_heading(alias)
                for alias in module.get("aliases", [])
            ),
        }:
            return module
    return None


def list_modules(graph: dict[str, Any]) -> list[str]:
    """Return a list of module names in graph order."""

    return [module.get("name", "") for module in graph.get("modules", [])]
