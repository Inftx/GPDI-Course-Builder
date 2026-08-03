"""Generate facilitator guides through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.prompts.facilitator_prompt import build_facilitator_prompt


def generate_facilitator_guide(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
) -> str:
    """Generate and save a context-grounded Markdown facilitator guide.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module used to retrieve the guide context.
        duration_hours: Planned facilitation duration in hours.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated facilitator-guide Markdown.
    """

    prompt_template = build_facilitator_prompt(
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
        "facilitator_guides",
        prompt_template,
        ai_provider,
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
    )
