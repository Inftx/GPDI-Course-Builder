"""Reusable RAG-backed document-generation workflow."""

import json
from pathlib import Path

from services.ai.ai_provider import AIProvider
from services.output.output_manager import save_output
from services.rag.chunker import chunk_document
from services.rag.indexer import build_index
from services.rag.retriever import retrieve_context
from services.knowledge import build_knowledge_graph, get_module


def _load_course_knowledge(project_name: str) -> dict[str, object]:
    """Load the consolidated processed course knowledge for a project.

    Args:
        project_name: Name of the project whose knowledge is loaded.

    Returns:
        The parsed ``course.json`` knowledge dictionary.

    Raises:
        FileNotFoundError: If the project has no processed course knowledge.
    """

    course_path = Path("projects") / project_name / "course.json"

    if not course_path.exists():
        raise FileNotFoundError(
            "Processed course knowledge was not found for this project."
        )

    with course_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _format_knowledge(knowledge: dict[str, object]) -> str:
    """Format processed course knowledge as a document for RAG chunking."""

    return "\n\n".join(
        [
            "Course Documents\n" + "\n".join(knowledge["documents"]),
            "\n".join(knowledge["modules"]),
            "Learning Outcomes\n" + "\n".join(
                knowledge["learning_outcomes"]
            ),
            "Assessment Criteria\n" + "\n".join(
                knowledge["assessment_criteria"]
            ),
            "Knowledge Requirements\n" + "\n".join(
                knowledge["knowledge_requirements"]
            ),
            "Practical Activities\n" + "\n".join(
                knowledge["practical_activities"]
            ),
            "Workplace Activities\n" + "\n".join(
                knowledge["workplace_activities"]
            ),
        ]
    )


def _format_module_context(module: dict[str, object] | None) -> str:
    """Convert a module from the knowledge graph into structured Markdown."""

    if not module:
        return ""

    def _section_block(title: str, values: list[str]) -> str:
        if not values:
            return f"## {title}\n\nNo entries available."
        return f"## {title}\n\n" + "\n".join(values)

    sections = [
        "# Module",
        module.get("name", "") or "",
        "",
        _section_block("Learning Outcomes", list(module.get("learning_outcomes", []) or [])),
        _section_block("Assessment Criteria", list(module.get("assessment_criteria", []) or [])),
        _section_block("Knowledge Requirements", list(module.get("knowledge_requirements", []) or [])),
        _section_block("Practical Activities", list(module.get("practical_activities", []) or [])),
        _section_block("Workplace Activities", list(module.get("workplace_activities", []) or [])),
    ]
    return "\n\n".join(section for section in sections if section != "")


def generate_document(
    project_name: str,
    module_name: str,
    duration_hours: float,
    output_type: str,
    prompt_template: str,
    ai_provider: AIProvider,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
) -> str:
    """Generate, save, and return a RAG-informed Markdown document.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module used to retrieve relevant course context.
        duration_hours: Planned lesson duration in hours.
        output_type: Output category accepted by ``save_output``.
        prompt_template: Template with ``context``, ``qualification``,
            ``module_name``, and ``duration_hours`` placeholders.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated Markdown document.
    """

    knowledge = _load_course_knowledge(project_name)
    graph = build_knowledge_graph(knowledge)
    module_context = ""

    if module_name:
        module_context = _format_module_context(get_module(graph, module_name))

    chunks = chunk_document(_format_knowledge(knowledge))
    index = build_index(chunks)
    context = retrieve_context(index, module_name)
    profile_section = "\n".join(
        [
            "Generation Profile",
            f"Audience: {audience or 'General audience'}",
            f"Teaching Style: {teaching_style or 'Standard'}",
            f"Detail Level: {detail_level or 'Moderate'}",
        ]
    )

    knowledge_graph_context = ""
    if module_context:
        knowledge_graph_context = f"Knowledge Graph\n\n{module_context}"

    prompt_context = "\n\n".join(
        part for part in [knowledge_graph_context, f"RAG Context\n\n{context}"] if part
    )

    prompt = prompt_template.format(
        context=prompt_context,
        qualification=knowledge["project"],
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=profile_section,
    )

    if "{generation_profile}" not in prompt_template:
        prompt = f"{prompt}\n\n{profile_section}"
    document = ai_provider.generate(prompt)

    save_output(project_name, output_type, document)

    return document
