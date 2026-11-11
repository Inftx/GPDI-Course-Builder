"""Generate teaching scripts through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document
from services.prompts.teaching_script_prompt import build_teaching_script_prompt


def generate_teaching_script(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
    audience: str | None = None,
    teaching_style: str | None = None,
    detail_level: str | None = None,
    knowledge_topic_id: str | None = None,
) -> str:
    """Generate and save a context-grounded Markdown teaching script.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module used to retrieve the script context.
        duration_hours: Planned session duration in hours.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated teaching-script Markdown.
    """

    prompt_template = build_teaching_script_prompt(
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
        "teaching_scripts",
        prompt_template,
        ai_provider,
        audience=audience,
        teaching_style=teaching_style,
        detail_level=detail_level,
        knowledge_topic_id=knowledge_topic_id,
    )
