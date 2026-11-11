
"""Generate assessments through a deterministic section-by-section pipeline."""

import re
from collections.abc import Callable

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.output.output_manager import save_output


# Preferred format for newly generated questions.
_EXPLICIT_QUESTION_MARKER = re.compile(
    r"(?im)^[ \t]*QUESTION[ \t]+(\d+)[ \t]*:[ \t]*"
)

# Backward-compatible format for existing tests and older generated content.
_QUESTION_MARKER = re.compile(
    r"(?m)^[ \t]*(\d+)[.)][ \t]+"
)

_OPTION_MARKER = re.compile(
    r"(?m)^[ \t]*(?:[-*+][ \t]+)?([A-Z])[.)][ \t]+"
)


def _question_matches(section_content: str):
    """Prefer explicit QUESTION markers, falling back to legacy numbering."""

    explicit_matches = list(
        _EXPLICIT_QUESTION_MARKER.finditer(section_content)
    )

    if explicit_matches:
        return explicit_matches

    return list(_QUESTION_MARKER.finditer(section_content))


def _contains_forbidden_text(text: str) -> bool:
    """Detect obvious unfinished placeholders."""

    forbidden_pattern = re.compile(
        r"(?i)(\.{3}|TODO\b|TBD\b|\[insert\b|\[placeholder\b|\[your\s+)"
    )

    return bool(forbidden_pattern.search(text))


def _split_question_blocks(section_content: str) -> list[str]:
    """Split a section into question blocks."""

    matches = _question_matches(section_content)
    blocks = []

    for index, match in enumerate(matches):
        start = match.end()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(section_content)
        )

        question = section_content[start:end].strip()

        if question:
            blocks.append(question)

    return blocks


def _question_count_errors(
    section_content: str,
    expected_count: int,
) -> list[str]:
    """Validate question count and sequential numbering."""

    matches = _question_matches(section_content)
    errors = []

    if len(matches) != expected_count:
        errors.append(
            f"Expected exactly {expected_count} numbered questions; "
            f"found {len(matches)}."
        )

    numbers = [int(match.group(1)) for match in matches]
    expected_numbers = list(range(1, len(numbers) + 1))

    if numbers != expected_numbers:
        errors.append(
            "Question numbers must be unique and sequential starting at 1."
        )

    return errors


def _section_a_errors(
    section_content: str,
    number_of_questions: int,
) -> list[str]:
    """Validate Section A multiple-choice questions."""

    if not section_content.strip():
        return ["Section A is empty."]

    if _contains_forbidden_text(section_content):
        return ["Section A contains a forbidden placeholder."]

    errors = _question_count_errors(
        section_content,
        number_of_questions,
    )

    for question_number, block in enumerate(
        _split_question_blocks(section_content),
        start=1,
    ):
        labels = _OPTION_MARKER.findall(block)

        if len(labels) != 4:
            errors.append(
                f"Question {question_number} must have exactly four options; "
                f"found {len(labels)}."
            )

        if labels != ["A", "B", "C", "D"]:
            errors.append(
                f"Question {question_number} options must be labelled "
                "A, B, C, and D exactly once and in order."
            )

    return errors


def _validate_section_a(
    section_content: str,
    number_of_questions: int,
) -> bool:
    return not _section_a_errors(
        section_content,
        number_of_questions,
    )


def _section_b_errors(
    section_content: str,
    number_of_questions: int,
) -> list[str]:
    """Validate Section B short-answer questions."""

    if not section_content.strip():
        return ["Section B is empty."]

    if _contains_forbidden_text(section_content):
        return ["Section B contains a forbidden placeholder."]

    errors = _question_count_errors(
        section_content,
        number_of_questions,
    )

    if _OPTION_MARKER.search(section_content):
        errors.append(
            "Section B must not contain multiple-choice options."
        )

    return errors


def _validate_section_b(
    section_content: str,
    number_of_questions: int,
) -> bool:
    return not _section_b_errors(
        section_content,
        number_of_questions,
    )


def _section_c_errors(section_content: str) -> list[str]:
    """Validate five scenario-based questions."""

    if not section_content.strip():
        return ["Section C is empty."]

    if _contains_forbidden_text(section_content):
        return ["Section C contains a forbidden placeholder."]

    errors = _question_count_errors(section_content, 5)

    for question_number, block in enumerate(
        _split_question_blocks(section_content),
        start=1,
    ):
        if not re.search(
            r"(?i)\bscenario\b|\bcase study\b|\bcase\b",
            block,
        ):
            errors.append(
                f"Question {question_number} must contain a scenario or case."
            )

    return errors


def _validate_section_c(section_content: str) -> bool:
    return not _section_c_errors(section_content)


def _grounding_reference_errors(
    section_content: str,
    section_name: str,
    expected_count: int,
) -> list[str]:
    """Require a source-reference tag in every question block."""

    errors = []
    blocks = _split_question_blocks(section_content)

    if len(blocks) != expected_count:
        return errors

    for question_number, block in enumerate(blocks, start=1):
        if not re.search(
            r"\[Source:\s*[^\]]+\]",
            block,
            flags=re.IGNORECASE,
        ):
            errors.append(
                f"{section_name} question {question_number} must cite a "
                "source heading from the supplied course context."
            )

    return errors


def _build_section_prompt(
    section_title: str,
    instructions: str,
    number_of_questions: int,
    difficulty: str,
    module_name: str,
) -> str:
    """Build a strict, section-specific assessment prompt."""

    return f"""
Create {section_title} for the assessment.

You are generating assessment questions, not summarising or reorganising
the course material.

{instructions}

MANDATORY OUTPUT FORMAT

Start every question on a new line using this exact structure:

QUESTION 1: Write the complete question here.

For the next question, use QUESTION 2:, then QUESTION 3:, and continue
sequentially until the required number of questions is reached.

Do not use numbered headings, numbered topic summaries, or numbered
subpoints as substitutes for questions.

Do not write an introduction, conclusion, explanation of your approach,
or commentary about the assessment.

For multiple-choice questions:
- Put each option on its own line.
- Use exactly A), B), C), and D).
- Provide four plausible options.
- Ensure there is only one correct answer.

For every question:
- Write a complete and assessable question.
- Use the supplied course context as the authoritative source.
- Do not invent facts that are not supported by the supplied context.
- Include a source reference in this format:
  [Source: exact heading shown in the supplied context]
- Cite a heading that actually appears in the supplied context.

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
    validator: Callable[[str], bool],
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
    validation_feedback: Callable[[str], list[str]] | None = None,
    knowledge_topic_id: str | None = None,
) -> str:
    """Generate and validate a section without publishing intermediate drafts."""

    max_attempts = 3
    previous_section = ""
    failures = ["The response did not match the required structure."]

    for attempt in range(1, max_attempts + 1):
        current_prompt = prompt_template

        if attempt > 1 and validation_feedback is not None:
            feedback = validation_feedback(previous_section)

            current_prompt += (
                "\n\nThe previous response failed validation.\n"
                "Correct these specific structural problems:\n- "
                + "\n- ".join(feedback)
                + "\n\nGenerate the complete section again. "
                "Do not describe the corrections. "
                "Do not reproduce the previous failed response."
            )

        section = generate_document(
            project_name,
            module_name,
            0.0,
            "assessments",
            current_prompt,
            ai_provider,
            audience=audience,
            teaching_style=teaching_style,
            detail_level=detail_level,
            knowledge_topic_id=knowledge_topic_id,
            save_result=False,
        )

        if validator(section):
            return section

        previous_section = section

        failures = (
            validation_feedback(section)
            if validation_feedback is not None
            else ["The response did not match the required structure."]
        )

        print(
            f"Assessment validation failed on attempt "
            f"{attempt}/{max_attempts}: {'; '.join(failures)}"
        )

    raise RuntimeError(
        "Assessment section generation failed after "
        f"{max_attempts} attempts. Last validation errors: "
        f"{'; '.join(failures)}"
    )


def _extract_memorandum_section(
    memorandum: str,
    heading: str,
    following_headings: tuple[str, ...],
) -> str:
    """Extract content between memorandum headings."""

    heading_pattern = re.compile(
        rf"(?im)^[ \t]*{re.escape(heading)}[ \t]*$"
    )

    match = heading_pattern.search(memorandum)

    if not match:
        return ""

    start = match.end()
    end = len(memorandum)

    for next_heading in following_headings:
        next_pattern = re.compile(
            rf"(?im)^[ \t]*{re.escape(next_heading)}[ \t]*$"
        )
        next_match = next_pattern.search(memorandum, start)

        if next_match:
            end = min(end, next_match.start())

    return memorandum[start:end].strip()


def _numbered_marking_entries(section_content: str) -> list[int]:
    """Extract top-level numbered marking entries."""

    return [
        int(match.group(1))
        for match in re.finditer(
            r"(?m)^[ \t]*(\d+)[.)][ \t]+\S",
            section_content,
        )
    ]


def _memorandum_errors(
    memorandum: str,
    section_a: str,
    section_b: str,
    section_c: str,
) -> list[str]:
    """Validate answer-key coverage and marking-guide numbering."""

    if not memorandum.strip():
        return ["The memorandum is empty."]

    if _contains_forbidden_text(memorandum):
        return ["The memorandum contains a forbidden placeholder."]

    required_headings = [
        "Section A Answer Key",
        "Section B Marking Guide",
        "Section C Marking Guide",
    ]

    errors = []

    for heading in required_headings:
        if not re.search(
            rf"(?im)^[ \t]*{re.escape(heading)}[ \t]*$",
            memorandum,
        ):
            errors.append(
                f"Memorandum is missing the heading '{heading}'."
            )

    if errors:
        return errors

    section_a_memo = _extract_memorandum_section(
        memorandum,
        "Section A Answer Key",
        (
            "Section B Marking Guide",
            "Section C Marking Guide",
        ),
    )

    section_b_memo = _extract_memorandum_section(
        memorandum,
        "Section B Marking Guide",
        ("Section C Marking Guide",),
    )

    section_c_memo = _extract_memorandum_section(
        memorandum,
        "Section C Marking Guide",
        (),
    )

    expected_a = len(_split_question_blocks(section_a))
    expected_b = len(_split_question_blocks(section_b))
    expected_c = len(_split_question_blocks(section_c))

    answer_matches = list(
        re.finditer(
            r"(?m)^[ \t]*(\d+)[.)][ \t]+([A-D])[ \t]*$",
            section_a_memo,
        )
    )

    answer_numbers = [
        int(match.group(1))
        for match in answer_matches
    ]

    if len(answer_matches) != expected_a:
        errors.append(
            f"Section A answer key must contain exactly {expected_a} "
            f"answers; found {len(answer_matches)}."
        )

    if answer_numbers != list(range(1, expected_a + 1)):
        errors.append(
            "Section A answer key numbers must be sequential, unique, "
            "and complete."
        )

    for section_name, content, expected_count in (
        ("Section B", section_b_memo, expected_b),
        ("Section C", section_c_memo, expected_c),
    ):
        numbers = _numbered_marking_entries(content)

        if len(numbers) != expected_count:
            errors.append(
                f"{section_name} marking guide must contain exactly "
                f"{expected_count} numbered entries; found {len(numbers)}."
            )

        if numbers != list(range(1, expected_count + 1)):
            errors.append(
                f"{section_name} marking guide entries must be sequential, "
                "unique, and complete."
            )

    return errors


def generate_assessment(
    project_name: str,
    module_name: str,
    number_of_questions: int,
    difficulty: str,
    ai_provider: AIProvider,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
    knowledge_topic_id: str | None = None,
) -> str:
    """Generate and save a complete context-grounded assessment."""

    if number_of_questions < 1:
        raise ValueError("Number of questions must be at least 1.")

    section_a_prompt = _build_section_prompt(
        "Section A",
        (
            f"Write exactly {number_of_questions} multiple-choice questions. "
            "Each question must have exactly four options labelled A), B), "
            "C), and D). Each question must have one correct answer."
        ),
        number_of_questions,
        difficulty,
        module_name,
    )

    section_b_prompt = _build_section_prompt(
        "Section B",
        (
            f"Write exactly {number_of_questions} short-answer questions. "
            "Do not include multiple-choice options."
        ),
        number_of_questions,
        difficulty,
        module_name,
    )

    section_c_prompt = _build_section_prompt(
        "Section C",
        (
            "Write exactly 5 scenario-based questions. "
            "Each question must contain a realistic scenario or case "
            "followed by a complete question."
        ),
        5,
        difficulty,
        module_name,
    )

    memorandum_prompt = _build_section_prompt(
        "Memorandum",
        (
            "Write a complete memorandum for the exact generated questions "
            "provided below. Do not invent, renumber, or omit questions.\n\n"
            "Use the exact heading 'Section A Answer Key' followed by one "
            "answer per line in the format '1. A'.\n"
            "Use the exact heading 'Section B Marking Guide' followed by "
            "numbered marking guidance for every Section B question.\n"
            "Use the exact heading 'Section C Marking Guide' followed by "
            "numbered marking guidance for every Section C question.\n"
            "Do not add or omit answers."
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
        lambda content: (
            _validate_section_a(content, number_of_questions)
            and not _grounding_reference_errors(
                content,
                "Section A",
                number_of_questions,
            )
        ),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
        validation_feedback=lambda content: (
            _section_a_errors(content, number_of_questions)
            + _grounding_reference_errors(
                content,
                "Section A",
                number_of_questions,
            )
        ),
        knowledge_topic_id=knowledge_topic_id,
    )

    section_b = _generate_validated_section(
        project_name,
        module_name,
        section_b_prompt,
        ai_provider,
        lambda content: (
            _validate_section_b(content, number_of_questions)
            and not _grounding_reference_errors(
                content,
                "Section B",
                number_of_questions,
            )
        ),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
        validation_feedback=lambda content: (
            _section_b_errors(content, number_of_questions)
            + _grounding_reference_errors(
                content,
                "Section B",
                number_of_questions,
            )
        ),
        knowledge_topic_id=knowledge_topic_id,
    )

    section_c = _generate_validated_section(
        project_name,
        module_name,
        section_c_prompt,
        ai_provider,
        lambda content: (
            _validate_section_c(content)
            and not _grounding_reference_errors(
                content,
                "Section C",
                5,
            )
        ),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
        validation_feedback=lambda content: (
            _section_c_errors(content)
            + _grounding_reference_errors(
                content,
                "Section C",
                5,
            )
        ),
        knowledge_topic_id=knowledge_topic_id,
    )

    memorandum_prompt += (
        "\n\nGENERATED ASSESSMENT QUESTIONS\n\n"
        "Use these exact questions and options when preparing the answer "
        "key and marking guidance.\n\n"
        "SECTION A\n"
        f"{section_a.strip()}\n\n"
        "SECTION B\n"
        f"{section_b.strip()}\n\n"
        "SECTION C\n"
        f"{section_c.strip()}"
    )

    def memo_errors(content: str) -> list[str]:
        return _memorandum_errors(
            content,
            section_a,
            section_b,
            section_c,
        )

    memorandum = _generate_validated_section(
        project_name,
        module_name,
        memorandum_prompt,
        ai_provider,
        lambda content: not memo_errors(content),
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
        validation_feedback=memo_errors,
        knowledge_topic_id=knowledge_topic_id,
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

    # Publish only the complete assessment after every section passes.
    save_output(
        project_name,
        "assessments",
        document,
    )

    return document
