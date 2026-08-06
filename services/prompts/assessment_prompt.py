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
You are writing the FINAL assessment document.

Do not explain what you are going to do.
Do not describe sections.
Write the complete finished assessment only.

Never describe the output.
Never use instructional phrases such as Provide, Generate, Expand, Include, or Examples below.
Never output placeholders, ellipses (...), template text, TODOs, notes, or unfinished content.

You are an expert South African QCTO assessor writing a complete assessment from the supplied course context only.
Do not invent information outside the supplied course context.

COURSE CONTEXT
{context}

ASSESSMENT SETTINGS
Module: {module_name}
Difficulty: {difficulty}
Number of Questions: {number_of_questions}

REQUIREMENTS
Section A: exactly {number_of_questions} multiple choice questions, four options each, one correct answer.
Section B: exactly {number_of_questions} short-answer questions.
Section C: exactly 5 scenario-based questions.
Include a marking guide and a memorandum.

Return only the Markdown assessment.

Begin writing the assessment now.
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
        number_of_questions=number_of_questions,
        difficulty=difficulty,
    )
