"""Reusable RAG-backed document-generation workflow."""

from pathlib import Path

from modules.course_builder import build_course
from services.ai.ai_provider import AIProvider
from services.output.output_manager import save_output
from services.rag.chunker import chunk_document
from services.rag.indexer import build_index, search_index
from services.rag.retriever import retrieve_context
from services.knowledge import build_knowledge_graph, get_module
from services.knowledge.course_selection import (
    find_topic_for_module,
    get_course_module_options,
    resolve_module_identifier,
)


def _load_course_knowledge(project_name: str) -> dict[str, object]:
    """Rebuild and return course knowledge from the latest processed sources.

    Args:
        project_name: Name of the project whose knowledge is rebuilt.

    Returns:
        The consolidated course knowledge dictionary.

    Raises:
        FileNotFoundError: If the project has no processed course knowledge.
    """

    project_path = Path("projects") / project_name
    if not project_path.exists():
        raise FileNotFoundError(
            f"Project '{project_name}' was not found."
        )
    knowledge = build_course(project_name)
    if not knowledge.get("documents") and not knowledge.get("modules"):
        raise ValueError(
            "No processed course sources are available. Upload and process "
            "course documents, then rebuild the Course Knowledge Base."
        )
    return knowledge


def _source_chunks(knowledge: dict[str, object]) -> list[dict[str, str]]:
    """Create individually attributable retrieval chunks from source text."""

    chunks = []
    for source in knowledge.get("source_documents", []) or []:
        if not isinstance(source, dict):
            continue
        source_name = str(source.get("name", "")).strip()
        content = str(source.get("content", "")).strip()
        if not content:
            continue
        for chunk in chunk_document(content, max_chars=5000):
            chunks.append(
                {
                    "title": f"{source_name} — {chunk['title']}",
                    "content": chunk["content"],
                }
            )
    return chunks


def _format_module_context(module: dict[str, object] | None) -> str:
    """Convert a module from the knowledge graph into structured Markdown."""

    if not module:
        return ""

    sections = ["# Selected Module", str(module.get("name") or "")]
    for key, title in (
        ("learning_outcomes", "Learning Outcomes"),
        ("assessment_criteria", "Assessment Criteria"),
        ("knowledge_requirements", "Knowledge Requirements"),
        ("practical_activities", "Practical Activities"),
        ("workplace_activities", "Workplace Activities"),
    ):
        values = [str(value) for value in module.get(key, []) or [] if value]
        if values:
            sections.append(f"## {title}\n\n" + "\n".join(values))

    return "\n\n".join(section for section in sections if section != "")


def _format_module_topics(
    knowledge: dict[str, object],
    module_name: str,
) -> tuple[str, str]:
    """Return topic details and search terms belonging to a selected module."""

    options = get_course_module_options(knowledge)
    module_identifier = resolve_module_identifier(options, module_name)
    selected_module = next(
        (
            option
            for option in options
            if option.identifier == module_identifier
        ),
        None,
    )
    if selected_module is None or not selected_module.topics:
        return "", ""

    topic_records = {
        str(topic.get("code") or "").casefold(): topic
        for topic in knowledge.get("knowledge_topics", []) or []
        if isinstance(topic, dict) and topic.get("code")
    }
    context_sections = []
    query_parts = []

    for topic_option in selected_module.topics:
        topic = topic_records.get(topic_option.identifier.casefold())
        if topic is None:
            continue

        title = str(topic.get("title") or topic_option.label)
        description = str(topic.get("description") or "")
        items = [
            str(item.get("description", item))
            if isinstance(item, dict)
            else str(item)
            for item in topic.get("knowledge_items", []) or []
        ]
        context_sections.append(
            "\n".join(
                part
                for part in (
                    f"### {title}",
                    description,
                    "\n".join(items),
                )
                if part
            )
        )
        query_parts.extend((title, description, *items))

    return "\n\n".join(context_sections), " ".join(query_parts)


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
    knowledge_topic_id: str | None = None,
    save_result: bool = True,
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
    module = get_module(graph, module_name)
    if module is None:
        available_modules = [
            item.get("name", "")
            for item in graph.get("modules", [])
            if item.get("name")
        ]
        available = ", ".join(available_modules) or "none identified"
        raise ValueError(
            f"Module '{module_name}' was not found in processed course "
            f"knowledge. Available modules/topics: {available}. "
            "Rebuild the Course Knowledge Base or select a listed module."
        )

    topic = None
    topic_context = ""
    topic_query = ""
    topic_evidence_words = 0
    if knowledge_topic_id:
        topic = find_topic_for_module(
            knowledge,
            module_name,
            knowledge_topic_id,
        )
        if topic is None:
            raise ValueError(
                f"Knowledge topic '{knowledge_topic_id}' is not available "
                f"for module '{module_name}'. Select a topic belonging to "
                "the selected module."
            )
        if isinstance(topic, dict):
            topic_parts = [
                str(topic.get("code") or knowledge_topic_id),
                str(topic.get("title") or ""),
                str(topic.get("description") or ""),
            ]
            topic_items = [
                str(item.get("description", item))
                if isinstance(item, dict)
                else str(item)
                for item in topic.get("knowledge_items", []) or []
            ]
            topic_context = (
                "Selected Knowledge Topic\n"
                + ": ".join(part for part in topic_parts[:2] if part)
                + ("\n" + topic_parts[2] if topic_parts[2] else "")
                + ("\n" + "\n".join(topic_items) if topic_items else "")
            )
            topic_query = " ".join([*topic_parts, *topic_items])
            topic_evidence_words = len(
                " ".join([topic_parts[2], *topic_items]).split()
            )
        else:
            topic_context = f"Selected Knowledge Topic\n{topic}"
            topic_query = str(topic)

    module_context = _format_module_context(module)
    source_chunks = _source_chunks(knowledge)
    source_index = build_index(source_chunks)
    module_topics_context = ""
    module_topics_query = ""
    if not knowledge_topic_id:
        module_topics_context, module_topics_query = _format_module_topics(
            knowledge,
            module_name,
        )
    retrieval_query = " ".join(
        [
            module_name,
            module_context,
            topic_query,
            module_topics_query,
        ]
    )
    retrieved_chunks = search_index(source_index, retrieval_query)[:5]
    source_context = retrieve_context(source_index, retrieval_query)
    context_sections = [
        section
        for section in (
            topic_context,
            module_context,
            module_topics_context,
            source_context,
        )
        if section.strip()
    ]
    context = "\n\n".join(context_sections)
    context_words = sum(
        len(str(chunk.get("content", "")).split())
        for chunk in retrieved_chunks
    )
    context_words += len(
        " ".join((topic_context, module_context)).split()
    )
    source_names = [
        str(source.get("name", ""))
        for source in knowledge.get("source_documents", [])
        if isinstance(source, dict) and source.get("name")
    ]
    module_knowledge_words = sum(
        len(str(value).split())
        for section in (
            "learning_outcomes",
            "assessment_criteria",
            "knowledge_requirements",
            "practical_activities",
            "workplace_activities",
        )
        for value in module.get(section, []) or []
    )
    print(
        "Course retrieval: "
        f"module={module_name!r}, "
        f"source_documents={source_names!r}, "
        f"retrieved_sources="
        f"{[chunk['title'] for chunk in retrieved_chunks]!r}, "
        f"context_length={len(context)}"
    )
    if source_chunks and not retrieved_chunks:
        raise ValueError(
            f"No relevant uploaded source material was found for module "
            f"'{module_name}'. Select a module or knowledge topic that is "
            "covered by the uploaded documents, then rebuild the Course "
            "Knowledge Base."
        )
    if (
        not context.strip()
        or context_words < 5
        or (
            not retrieved_chunks
            and module_knowledge_words + topic_evidence_words < 5
        )
    ):
        raise ValueError(
            f"No usable course context was retrieved for module "
            f"'{module_name}'. Verify that processed source text or "
            "module-specific knowledge is available, then rebuild the "
            "Course Knowledge Base before generating content."
        )

    profile_section = "\n".join(
        [
            "Generation Profile",
            f"Audience: {audience or 'General audience'}",
            f"Teaching Style: {teaching_style or 'Standard'}",
            f"Detail Level: {detail_level or 'Moderate'}",
        ]
    )

    prompt = prompt_template.format(
        context=context,
        qualification=knowledge.get("project", project_name),
        module_name=str(module.get("name") or module_name),
        duration_hours=duration_hours,
        generation_profile=profile_section,
    )

    if "{generation_profile}" not in prompt_template:
        prompt = f"{prompt}\n\n{profile_section}"

    system_prompt = """
You are a curriculum developer creating professional learning and assessment material.

Use the supplied course context as the main source of content.

Create original content from the supplied course context. Treat it as source
evidence, not a document to retrieve or reproduce. Do not copy existing questions
or answer keys, lesson plans, guides, or scripts from it. For assessments, write
new questions based on the source facts.

Follow the requested document type, section, question count, difficulty, audience, and formatting requirements.

Produce complete, useful content suitable for learners and facilitators.

Do not discuss your reasoning or the generation process.

Return the requested content directly.
"""
    prompt = f"{system_prompt}\n\n{prompt}"

    document = ai_provider.generate(prompt)

    if save_result:
        save_output(project_name, output_type, document)

    return document
