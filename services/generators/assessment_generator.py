"""Generate assessments through a deterministic section-by-section pipeline."""

import re

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.output.output_manager import save_output


def _contains_forbidden_text(text: str) -> bool:
    """Return True when the response contains obvious unfinished placeholders."""

    forbidden_pattern = re.compile(
        r"(?i)(\.{3}|TODO\b|TBD\b|\[insert\b|\[placeholder\b|\[your\s+)"
    )

    return bool(forbidden_pattern.search(text))


def _split_question_blocks(section_content: str) -> list[str]:
    """Split a section into question blocks based on numbered entries."""

    blocks = re.split(
        r"(?m)^\s*\d+[.)]\s+",
        section_content.strip(),
    )

    return [
        block.strip()
        for block in blocks
        if block and block.strip()
    ]


def _validate_section_a(
    section_content: str,
    number_of_questions: int,
) -> bool:
    """Validate Section A as the requested number of four-option MCQs."""

    if not section_content.strip():
        return False

    if _contains_forbidden_text(section_content):
        return False

    blocks = _split_question_blocks(section_content)

    if len(blocks) != number_of_questions:
        return False

    for block in blocks:
        options = re.findall(
            r"(?m)^\s*[A-D][.)]\s+",
            block,
        )

        if len(options) != 4:
            return False

        labels = re.findall(
            r"(?m)^\s*([A-D])[.)]\s+",
            block,
        )

        if labels != ["A", "B", "C", "D"]:
            return False

    return True


def _validate_section_b(
    section_content: str,
    number_of_questions: int,
) -> bool:
    """Validate Section B as the requested number of short-answer questions."""

    if not section_content.strip():
        return False

    if _contains_forbidden_text(section_content):
        return False

    blocks = _split_question_blocks(section_content)

    if len(blocks) != number_of_questions:
        return False

    if re.search(
        r"(?m)^\s*[A-D][.)]\s+",
        section_content,
    ):
        return False

    return True


def _validate_section_c(section_content: str) -> bool:
    """Validate Section C content for five scenario-based questions."""

    if not section_content.strip():
        return False

    if _contains_forbidden_text(section_content):
        return False

    blocks = _split_question_blocks(section_content)

    if len(blocks) != 5:
        return False

    for block in blocks:
        if not re.search(
            r"(?i)\bscenario\b|\bcase study\b|\bcase\b",
            block,
        ):
            return False

    return True


def _validate_memorandum(section_content: str) -> bool:
    """Validate the memorandum content."""

    return (
        bool(section_content.strip())
        and not _contains_forbidden_text(section_content)
    )


def _build_section_prompt(
    section_title: str,
    instructions: str,
    number_of_questions: int,
    difficulty: str,
    module_name: str,
) -> str:
    """Create a focused prompt for generating one assessment section."""

    return f"""
Create {section_title} for the assessment.

{instructions}

Use the supplied course context as the authoritative source.
Do not invent facts that are not supported by the supplied course context.

ASSESSMENT SETTINGS

Module: {module_name}
Difficulty: {difficulty}
Number of Questions: {number_of_questions}

COURSE CONTEXT

{{context}}

Return only the completed content for {section_title}.
"""


def _generate_validated_section(
    project_name: str,
    module_name: str,
    prompt_template: str,
    ai_provider: AIProvider,
    validator,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
) -> str:
    """Generate a section until it passes validation or attempts are exhausted."""

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        section = generate_document(
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

        if validator(section):
            return section

        print(
            f"Assessment validation failed on attempt "
            f"{attempt}/{max_attempts}."
        )

    raise RuntimeError(
        "Assessment section generation failed after "
        f"{max_attempts} attempts."
    )


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
    """Generate and save a context-grounded Markdown assessment."""

    if number_of_questions < 1:
        raise ValueError(
            "Number of questions must be at least 1."
        )

    section_a_prompt = _build_section_prompt(
        "Section A",
        (
            f"Write exactly {number_of_questions} "
            "multiple-choice questions. "
            "Each question must have exactly four options "
            "labelled A, B, C, and D. "
            "Each question must have one correct answer."
        ),
        number_of_questions,
        difficulty,
        module_name,
    )

    section_b_prompt = _build_section_prompt(
        "Section B",
        (
            f"Write exactly {number_of_questions} "
            "short-answer questions. "
            "Do not use multiple-choice options."
        ),
        number_of_questions,
        difficulty,
        module_name,
    )

    section_c_prompt = _build_section_prompt(
        "Section C",
        (
            "Write exactly 5 scenario-based questions. "
            "Each question must contain a clear scenario "
            "followed by a complete question."
        ),
        5,
        difficulty,
        module_name,
    )

    memorandum_prompt = _build_section_prompt(
        "Memorandum",
        (
            "Write a complete memorandum containing the correct "
            "answers and appropriate marking guidance for all "
            "assessment sections."
        ),
        0,
        difficulty,
        module_name,
    )

    section_a = _generate_validated_section(
        project_name,
        module_name,
        section_a_prompt,
        ai_provider,
        lambda text: _validate_section_a(
            text,
            number_of_questions,
        ),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )

    section_b = _generate_validated_section(
        project_name,
        module_name,
        section_b_prompt,
        ai_provider,
        lambda text: _validate_section_b(
            text,
            number_of_questions,
        ),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )

    section_c = _generate_validated_section(
        project_name,
        module_name,
        section_c_prompt,
        ai_provider,
        _validate_section_c,
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )

    memorandum = _generate_validated_section(
        project_name,
        module_name,
        memorandum_prompt,
        ai_provider,
        _validate_memorandum,
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )

    document = "\n\n".join(
        [
            "# Assessment",
            "## Section A",
            section_a.strip(),
            "## Section B",
            section_b.strip(),
            "## Section C",
            section_c.strip(),
            "## Memorandum",
            memorandum.strip(),
        ]
    )

    save_output(
        project_name,
        "assessments",
        document,
    )

    return document