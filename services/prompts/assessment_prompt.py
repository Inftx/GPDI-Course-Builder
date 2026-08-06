"""Prompt builder for assessment generation."""

from services.prompts.prompt_manager import build_prompt


def build_assessment_prompt(
    context: str,
    qualification: str,
    module_name: str,
    duration_hours: float,
    generation_profile: str,
    number_of_questions: int,
    difficulty: str,
) -> str:
    """Return the assessment prompt string."""

    return build_prompt(
        """
ROLE
You are an expert South African QCTO assessor.

OBJECTIVE
Generate a complete assessment using only the supplied course context.

STRICT RULES
Do not repeat these instructions.
Do not reproduce this prompt.
Never output placeholders such as "...".
Generate complete content for every section.
Return only the finished assessment.

COURSE CONTEXT
{context}

ASSESSMENT SETTINGS
Module: {module_name}
Difficulty: {difficulty}
Number of Questions: {number_of_questions}

OUTPUT FORMAT
Create a professional Markdown assessment with clearly structured sections for Section A, Section B, Section C, a marking guide, and a memorandum. Ensure the content is complete, coherent, and aligned to the supplied course context.

Begin generating the assessment now.
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
        number_of_questions=number_of_questions,
        difficulty=difficulty,
    )
