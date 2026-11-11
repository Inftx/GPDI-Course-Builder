
import json
from pathlib import Path

from services.rag.chunker import chunk_document
from services.rag.indexer import build_index
from services.rag.storage import save_index


LIST_FIELDS = (
    "documents",
    "modules",
    "module_records",
    "knowledge_topics",
    "learning_outcomes",
    "assessment_criteria",
    "knowledge_requirements",
    "practical_activities",
    "workplace_activities",
    "source_documents",
    "source_references",
    "warnings",
)

DEDUPLICATED_FIELDS = (
    "documents",
    "modules",
    "module_records",
    "knowledge_topics",
    "learning_outcomes",
    "assessment_criteria",
    "knowledge_requirements",
    "practical_activities",
    "workplace_activities",
    "source_references",
    "warnings",
)


def build_course(project_name):
    """Combine supported knowledge schemas without duplicating existing data."""

    project_folder = Path("projects") / project_name
    knowledge_folder = project_folder / "knowledge"
    formatted_folder = project_folder / "formatted"
    extracted_folder = project_folder / "extracted_text"

    course = {
        "project": project_name,
        "documents": [],
        "modules": [],
        "module_records": [],
        "knowledge_topics": [],
        "learning_outcomes": [],
        "assessment_criteria": [],
        "knowledge_requirements": [],
        "practical_activities": [],
        "workplace_activities": [],
        "source_documents": [],
        "source_references": [],
        "warnings": [],
    }

    existing_course = project_folder / "course.json"

    if existing_course.exists():
        existing_data = _read_json_object(existing_course)
        course.update(existing_data)
        course["project"] = project_name

    for key in LIST_FIELDS:
        course[key] = _as_list(course.get(key))

    course["source_documents"] = _normalize_source_documents(
        course["source_documents"]
    )

    # Remove exact duplicates already stored in course.json.
    # Original ordering and distinct entries are preserved.
    for key in DEDUPLICATED_FIELDS:
        unique_values = []
        _extend_unique(unique_values, course[key])
        course[key] = unique_values

    knowledge_files = (
        sorted(knowledge_folder.glob("*.json"))
        if knowledge_folder.exists()
        else []
    )

    for file in knowledge_files:
        knowledge = _read_json_object(file)

        document_name = str(
            knowledge.get("document") or file.stem
        )

        _append_unique(
            course["documents"],
            document_name,
        )

        modules = _as_list(knowledge.get("modules"))

        singular_module = knowledge.get("module")

        if singular_module not in (None, ""):
            modules.extend(_as_list(singular_module))

        for module in modules:
            _append_module(
                course,
                module,
                document_name,
            )

        topics = knowledge.get("knowledge_topics")

        if topics is None:
            topics = knowledge.get(
                "knowledge_topic",
                knowledge.get("topics"),
            )

        _extend_unique(
            course["knowledge_topics"],
            topics,
        )

        for section in (
            "learning_outcomes",
            "assessment_criteria",
            "knowledge_requirements",
            "practical_activities",
            "workplace_activities",
        ):
            _extend_unique(
                course[section],
                knowledge.get(section),
            )

        references = knowledge.get("source_references")

        if references is None:
            references = knowledge.get("source_reference")

        if references is None:
            references = knowledge.get("references")

        _extend_unique(
            course["source_references"],
            references,
        )

        _extend_unique(
            course["warnings"],
            knowledge.get("warnings"),
        )

        source_text = (
            _load_processed_text(
                formatted_folder,
                extracted_folder,
                Path(document_name).stem,
            )
            or knowledge.get("source_text", "")
        )

        if not isinstance(source_text, str):
            source_text = (
                ""
                if source_text is None
                else json.dumps(
                    source_text,
                    ensure_ascii=False,
                )
            )

        _add_source_document(
            course,
            document_name,
            source_text,
            replace_existing=True,
        )

    for source_folder, suffix in (
        (formatted_folder, "_structured.txt"),
        (extracted_folder, "_clean.txt"),
    ):
        if not source_folder.exists():
            continue

        for source_file in sorted(
            source_folder.glob(f"*{suffix}")
        ):
            document_stem = source_file.name[:-len(suffix)]

            _add_source_document(
                course,
                document_stem,
                source_file.read_text(encoding="utf-8"),
                replace_existing=(
                    source_folder == formatted_folder
                    or not (
                        formatted_folder
                        / f"{document_stem}_structured.txt"
                    ).exists()
                ),
            )

            if not any(
                Path(str(name)).stem.casefold()
                == document_stem.casefold()
                for name in course["documents"]
            ):
                _append_unique(
                    course["documents"],
                    document_stem,
                )

    if not any(course.get(key) for key in LIST_FIELDS):
        return course

    output = project_folder / "course.json"

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            course,
            file,
            indent=4,
            ensure_ascii=False,
        )

    knowledge_chunks = chunk_document(
        _format_course_knowledge(course),
        max_chars=5000,
    )

    for source in course["source_documents"]:
        source_chunks = chunk_document(
            source["content"],
            max_chars=5000,
        )

        knowledge_chunks.extend(
            {
                "title": f"{source['name']} — {chunk['title']}",
                "content": chunk["content"],
            }
            for chunk in source_chunks
        )

    rag_index = build_index(knowledge_chunks)

    save_index(
        rag_index,
        project_name,
    )

    return course


def _read_json_object(path: Path) -> dict:
    """Read a JSON object and identify the source file in any error."""

    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)

    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError(
            f"Could not read course knowledge file '{path}': {error}"
        ) from error

    if not isinstance(value, dict):
        raise ValueError(
            f"Course knowledge file '{path}' must contain a JSON object."
        )

    return value


def _as_list(value) -> list:
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [value]


def _append_unique(values: list, value) -> None:
    """Append a non-empty value only if it does not already exist."""

    if value not in (None, "") and value not in values:
        values.append(value)


def _extend_unique(values: list, new_values) -> None:
    """Append unique entries while preserving their original order."""

    for value in _as_list(new_values):
        _append_unique(values, value)


def _normalize_source_documents(sources: list) -> list:
    """Normalize source records and retain one record per document."""

    normalized = []
    source_positions = {}

    for index, source in enumerate(sources, start=1):

        if isinstance(source, dict):
            name = (
                source.get("name")
                or source.get("document")
                or f"Source {index}"
            )

            content = source.get("content", "")

            source_record = {
                **source,
                "name": str(name),
                "content": (
                    content
                    if isinstance(content, str)
                    else str(content)
                ),
            }

        elif isinstance(source, str):
            source_record = {
                "name": source,
                "content": "",
            }

        else:
            source_record = {
                "name": f"Source {index}",
                "content": json.dumps(
                    source,
                    ensure_ascii=False,
                ),
            }

        document_key = Path(
            source_record["name"]
        ).stem.casefold()

        if document_key in source_positions:
            existing = normalized[
                source_positions[document_key]
            ]

            if (
                not existing["content"]
                and source_record["content"]
            ):
                existing["content"] = source_record["content"]

            continue

        source_positions[document_key] = len(normalized)
        normalized.append(source_record)

    return normalized


def _append_module(
    course: dict,
    module,
    document_name: str,
) -> None:
    if module in (None, ""):
        return

    if isinstance(module, dict):

        if not any(
            value not in (None, "", [], {})
            for value in module.values()
        ):
            return

        module_record = {
            "document": document_name,
            **module,
        }

        _append_unique(
            course["module_records"],
            module_record,
        )

        code = str(
            module.get("code") or ""
        ).strip()

        title = str(
            module.get("title")
            or module.get("name")
            or ""
        ).strip()

        if code and title:
            label = f"{code}: {title}"
        else:
            label = (
                title
                or code
                or json.dumps(
                    module,
                    ensure_ascii=False,
                )
            )

    else:
        label = str(module).strip()

        if label:
            _append_unique(
                course["module_records"],
                {
                    "document": document_name,
                    "name": label,
                },
            )

    _append_unique(
        course["modules"],
        label,
    )


def _load_processed_text(
    formatted_folder: Path,
    extracted_folder: Path,
    document_stem: str,
) -> str:
    """Read processed text for a legacy knowledge record."""

    candidates = (
        formatted_folder / f"{document_stem}_structured.txt",
        extracted_folder / f"{document_stem}_clean.txt",
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")

    return ""


def _add_source_document(
    course: dict,
    document_name: str,
    content: str,
    replace_existing: bool = False,
) -> None:
    """Keep one non-empty source record for retrieval and prompt context."""

    content = content.strip()

    if not content:
        return

    document_stem = Path(
        document_name
    ).stem.casefold()

    for source in course["source_documents"]:

        if (
            Path(
                str(source.get("name", ""))
            ).stem.casefold()
            == document_stem
        ):

            if replace_existing or not source["content"]:
                source["name"] = document_name
                source["content"] = content

            return

    course["source_documents"].append(
        {
            "name": document_name,
            "content": content,
        }
    )


def _format_course_knowledge(course: dict) -> str:
    """Format normalized course fields for retrieval."""

    topic_lines = [
        json.dumps(topic, ensure_ascii=False)
        if isinstance(topic, (dict, list))
        else str(topic)
        for topic in course["knowledge_topics"]
    ]

    sections = [
        "Course Documents\n"
        + "\n".join(map(str, course["documents"])),

        "Modules\n"
        + "\n".join(map(str, course["modules"])),

        "Knowledge Topics\n"
        + "\n".join(topic_lines),

        "Learning Outcomes\n"
        + "\n".join(map(str, course["learning_outcomes"])),

        "Assessment Criteria\n"
        + "\n".join(map(str, course["assessment_criteria"])),

        "Knowledge Requirements\n"
        + "\n".join(map(str, course["knowledge_requirements"])),

        "Practical Activities\n"
        + "\n".join(map(str, course["practical_activities"])),

        "Workplace Activities\n"
        + "\n".join(map(str, course["workplace_activities"])),

        "Source References\n"
        + "\n".join(map(str, course["source_references"])),
    ]

    return "\n\n".join(sections)
