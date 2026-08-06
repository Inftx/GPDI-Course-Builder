"""Generate assessments through the shared document generator."""

import re

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.prompts.assessment_prompt import build_assessment_prompt


def _extract_section_content(text: str, heading: str) -> str:
    """Return the content for a Markdown section heading."""

    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)

    if not match:
        return ""

    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)

    if next_heading:
        return text[start : start + next_heading.start()]

    return text[start:]


def _count_question_items(section_content: str) -> int:
    """Count numbered question items in a section."""

    return len(
        re.findall(r"(?m)^\s*(?:\d+[.)]|[A-Z][.)])\s+", section_content)
    )


def _is_valid_assessment(output: str, number_of_questions: int) -> bool:
    """Return True when the assessment output satisfies the validation rules."""

    if not output.strip():
        return False

    forbidden_pattern = re.compile(
        r"(?i)(\.\.\.|\bprovide\b|\bexample\b|\btodo\b|\bexpand\b|\bgenerate\b|\binsert\b)"
    )
    if forbidden_pattern.search(output):
        return False

    section_a = _extract_section_content(output, "Section A")
    section_b = _extract_section_content(output, "Section B")
    section_c = _extract_section_content(output, "Section C")

    if _count_question_items(section_a) < number_of_questions:
        return False

    if _count_question_items(section_b) < number_of_questions:
        return False

    if _count_question_items(section_c) < 5:
        return False

    return True


def generate_assessment(
    project_name: str,
    module_name: str,
    number_of_questions: int,
    difficulty: str,
    ai_provider: AIProvider,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
) -> str:
    """Generate and save a context-grounded Markdown assessment.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module used to retrieve the assessment context.
        number_of_questions: Number of questions for Sections A and B.
        difficulty: Required difficulty level for all questions.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated assessment Markdown.
    """

    prompt_template = build_assessment_prompt(
        "{context}",
        "{qualification}",
        module_name,
        "{duration_hours}",
        "{generation_profile}",
        number_of_questions,
        difficulty,
    )

    for attempt in range(3):
        document = generate_document(
            project_name,
            module_name,
            0.0,
            "assessments",
            prompt_template,
            ai_provider,
            audience=audience,
            teaching_style=teaching_style,
            detail_level=detail_level,
        )

        if _is_valid_assessment(document, number_of_questions):
            return document

    raise RuntimeError(
        "Assessment generation failed after 3 attempts due to invalid output."
    )
