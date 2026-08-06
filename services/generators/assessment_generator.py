"""Generate assessments through a deterministic section-by-section pipeline."""

import re

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.output.output_manager import save_output


def _contains_forbidden_text(text: str) -> bool:
    """Return True when the text contains placeholder or template-like wording."""

    forbidden_pattern = re.compile(
        r"(?i)(\.\.\.|\bprovide\b|\bexample\b|\btodo\b|\bexpand\b|\bgenerate\b|\binsert\b)"
    )
    return bool(forbidden_pattern.search(text))


def _split_question_blocks(section_content: str) -> list[str]:
    """Split a section into question blocks based on numbered entries."""

    blocks = re.split(r"(?m)^\s*\d+[.)]\s+", section_content.strip())
    return [block.strip() for block in blocks if block and block.strip()]


def _validate_section_a(section_content: str, number_of_questions: int) -> bool:
    """Validate Section A content for question count and four-option MCQs."""

    if not section_content.strip() or _contains_forbidden_text(section_content):
        return False

    blocks = _split_question_blocks(section_content)
    if len(blocks) != number_of_questions:
        return False

    for block in blocks:
        if len(re.findall(r"(?m)^\s*[A-D][.)]\s+", block)) < 4:
            return False

    return True


def _validate_section_b(section_content: str, number_of_questions: int) -> bool:
    """Validate Section B content for question count and absence of MCQs."""

    if not section_content.strip() or _contains_forbidden_text(section_content):
        return False

    blocks = _split_question_blocks(section_content)
    if len(blocks) != number_of_questions:
        return False

    if re.search(r"(?m)^\s*[A-D][.)]\s+", section_content):
        return False

    return True


def _validate_section_c(section_content: str) -> bool:
    """Validate Section C content for five scenario-based questions."""

    if not section_content.strip() or _contains_forbidden_text(section_content):
        return False

    blocks = _split_question_blocks(section_content)
    if len(blocks) != 5:
        return False

    for block in blocks:
        if not re.search(r"(?i)scenario|case study|case", block):
            return False

    return True


def _validate_memorandum(section_content: str) -> bool:
    """Validate the memorandum content."""

    return bool(section_content.strip()) and not _contains_forbidden_text(section_content)


def _build_section_prompt(section_title: str, instructions: str, number_of_questions: int, difficulty: str, module_name: str) -> str:
    """Create a section-specific prompt template for deterministic generation."""

    return f"""
You are writing only {section_title} for the assessment.

{instructions}

Write only the completed Markdown content for {section_title}.
Do not include any other sections.
Do not include placeholders, ellipses (...), template text, TODOs, notes, or unfinished content.
Do not explain your process.
Do not describe the output.

COURSE CONTEXT
{{context}}

ASSESSMENT SETTINGS
Module: {module_name}
Difficulty: {difficulty}
Number of Questions: {number_of_questions}

Return only the finished Markdown content for {section_title}.
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
    """Generate a section until it passes validation or three attempts are exhausted."""

    for _ in range(3):
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

    raise RuntimeError("Assessment section generation failed after 3 attempts.")


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
    """Generate and save a context-grounded Markdown assessment section by section."""

    section_a_prompt = _build_section_prompt(
        "Section A",
        f"Write exactly {number_of_questions} multiple-choice questions. Each question must have four options labelled A, B, C, and D, with one correct answer.",
        number_of_questions,
        difficulty,
        module_name,
    )
    section_b_prompt = _build_section_prompt(
        "Section B",
        f"Write exactly {number_of_questions} short-answer questions. Do not include any multiple-choice questions.",
        number_of_questions,
        difficulty,
        module_name,
    )
    section_c_prompt = _build_section_prompt(
        "Section C",
        "Write exactly 5 scenario-based questions. Each question must contain a clear scenario and be written as a complete question.",
        5,
        difficulty,
        module_name,
    )
    memorandum_prompt = _build_section_prompt(
        "Memorandum",
        "Write a complete memorandum that aligns with the assessment sections and uses only the supplied course context.",
        0,
        difficulty,
        module_name,
    )

    section_a = _generate_validated_section(
        project_name,
        module_name,
        section_a_prompt,
        ai_provider,
        lambda text: _validate_section_a(text, number_of_questions),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )
    section_b = _generate_validated_section(
        project_name,
        module_name,
        section_b_prompt,
        ai_provider,
        lambda text: _validate_section_b(text, number_of_questions),
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

    save_output(project_name, "assessments", document)
    return document
