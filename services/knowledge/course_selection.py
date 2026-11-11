"""Build stable module and topic selections from processed course data."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeTopicOption:
    identifier: str
    label: str
    module_identifier: str


@dataclass
class CourseModuleOption:
    identifier: str
    label: str
    aliases: set[str] = field(default_factory=set)
    topics: list[KnowledgeTopicOption] = field(default_factory=list)


def resolve_module_identifier(
    modules: list[CourseModuleOption],
    value: str | None,
) -> str | None:
    """Resolve a current or legacy module value to its canonical identifier."""

    if not value:
        return None
    module = _find_module(modules, value)
    return module.identifier if module else None


def get_course_module_options(
    course_data: dict[str, Any],
) -> list[CourseModuleOption]:
    """Return selectable modules with only their associated processed topics."""

    modules: list[CourseModuleOption] = []

    def add_module(identifier: str, label: str, aliases: list[str]) -> None:
        normalized = identifier.strip().casefold()
        existing = next(
            (
                module
                for module in modules
                if module.identifier.casefold() == normalized
            ),
            None,
        )
        if existing is None:
            existing = CourseModuleOption(identifier.strip(), label.strip())
            modules.append(existing)
        elif len(label.strip()) > len(existing.label):
            existing.label = label.strip()
        existing.aliases.update(
            alias.strip()
            for alias in aliases
            if isinstance(alias, str) and alias.strip()
        )
        existing.aliases.update((existing.identifier, existing.label))

    for record in _as_values(course_data.get("module_records")):
        if not isinstance(record, dict):
            continue
        code = _as_text(record.get("code") or record.get("identifier"))
        title = _as_text(record.get("title"))
        name = _as_text(record.get("name"))
        name_code, name_title = _split_module_label(name)
        if not code and name_code:
            code = name_code
        if not title:
            title = name_title or name
        identifier = code or _as_text(record.get("id")) or title
        if identifier:
            label = f"{code}: {title}" if code and title else title or code
            add_module(
                identifier,
                label,
                [code, title, name, _as_text(record.get("id"))],
            )

    for value in _as_values(course_data.get("modules")):
        if isinstance(value, dict):
            code = _as_text(value.get("code") or value.get("identifier"))
            title = _as_text(value.get("title") or value.get("name"))
            identifier = code or _as_text(value.get("id")) or title
            if identifier:
                label = f"{code}: {title}" if code and title else title or code
                add_module(identifier, label, [code, title, _as_text(value.get("id"))])
            continue

        module_name = _as_text(value)
        if not module_name:
            continue
        code, title = _split_module_label(module_name)
        if code:
            matching = _find_module(modules, code)
            if matching:
                if title and ":" not in matching.label:
                    matching.label = module_name
                matching.aliases.update((module_name, title))
            else:
                add_module(code, module_name, [code, title, module_name])
        elif _find_module(modules, module_name) is None:
            add_module(module_name, module_name, [module_name])

    topic_values = _as_values(course_data.get("knowledge_topics"))
    for topic in topic_values:
        topic_option = _make_topic_option(topic)
        if topic_option is None:
            continue

        parent = _get_topic_module_reference(topic)
        module = _find_module(modules, parent) if parent else None
        if not parent:
            module = _find_module_by_topic_prefix(modules, topic_option.identifier)
        if (
            module is None
            and not parent
            and len(modules) == 1
            and "-" not in topic_option.identifier
        ):
            module = modules[0]
        if module is None:
            continue

        topic_option.module_identifier = module.identifier
        if not any(
            existing.identifier.casefold() == topic_option.identifier.casefold()
            for existing in module.topics
        ):
            module.topics.append(topic_option)

    return modules


def find_topic_for_module(
    course_data: dict[str, Any],
    module_identifier: str,
    topic_identifier: str,
) -> dict[str, Any] | str | None:
    """Resolve a topic ID only when it belongs to the selected module."""

    modules = get_course_module_options(course_data)
    canonical_identifier = resolve_module_identifier(modules, module_identifier)
    if canonical_identifier is None:
        return None

    for topic in _as_values(course_data.get("knowledge_topics")):
        option = _make_topic_option(topic)
        if not option or option.identifier.casefold() != topic_identifier.casefold():
            continue
        parent = _get_topic_module_reference(topic)
        owner = _find_module(modules, parent) if parent else None
        if not parent:
            owner = _find_module_by_topic_prefix(modules, option.identifier)
        if (
            owner is None
            and not parent
            and len(modules) == 1
            and "-" not in option.identifier
        ):
            owner = modules[0]
        if owner and owner.identifier.casefold() == canonical_identifier.casefold():
            return topic
    return None


def _as_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _split_module_label(value: str) -> tuple[str, str]:
    if ":" not in value:
        return "", ""
    identifier, label = (part.strip() for part in value.split(":", 1))
    return (identifier, label) if identifier and label else ("", "")


def _as_values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _find_module(
    modules: list[CourseModuleOption],
    value: str,
) -> CourseModuleOption | None:
    normalized = value.strip().casefold()
    return next(
        (
            module
            for module in modules
            if normalized == module.identifier.casefold()
            or any(alias.casefold() == normalized for alias in module.aliases)
        ),
        None,
    )


def _find_module_by_topic_prefix(
    modules: list[CourseModuleOption],
    topic_identifier: str,
) -> CourseModuleOption | None:
    candidates = [
        module
        for module in modules
        if any(
            topic_identifier.casefold().startswith(f"{alias.casefold()}-")
            for alias in {module.identifier, *module.aliases}
            if alias
        )
    ]
    return max(candidates, key=lambda module: len(module.identifier), default=None)


def _make_topic_option(value: Any) -> KnowledgeTopicOption | None:
    if isinstance(value, dict):
        identifier = _as_text(
            value.get("code") or value.get("identifier") or value.get("id")
        )
        title = _as_text(value.get("title") or value.get("name"))
        if not identifier:
            identifier = title
        if not identifier:
            return None
        label = f"{identifier}: {title}" if title and title != identifier else identifier
        return KnowledgeTopicOption(identifier, label, "")
    if isinstance(value, str) and value.strip():
        identifier = value.strip()
        return KnowledgeTopicOption(identifier, identifier, "")
    return None


def _get_topic_module_reference(topic: Any) -> str:
    if not isinstance(topic, dict):
        return ""
    for key in ("module_identifier", "module_id", "module_code", "module"):
        value = topic.get(key)
        if isinstance(value, dict):
            value = value.get("code") or value.get("identifier") or value.get("name")
        text = _as_text(value)
        if text:
            return text
    return ""
