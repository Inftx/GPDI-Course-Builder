"""Generate lesson plans through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.prompts.lesson_plan_prompt import build_lesson_plan_prompt


def generate_lesson_plan(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
) -> str:
    """Generate and save a professional Markdown lesson plan.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module for which to generate the lesson plan.
        duration_hours: Planned lesson duration in hours.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated lesson-plan Markdown.
    """

    prompt_template = build_lesson_plan_prompt(
        "{context}",
        "{qualification}",
        "{module_name}",
        "{duration_hours}",
        "{generation_profile}",
    )

    return generate_document(
        project_name,
        module_name,
        duration_hours,
        "lesson_plans",
        prompt_template,
        ai_provider,
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )
