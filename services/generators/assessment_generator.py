"""Generate assessments through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.prompts.assessment_prompt import build_assessment_prompt


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

    return generate_document(
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
