"""Orchestrate generation of a complete training pack."""

from services.ai.ai_provider import AIProvider
from services.generators.assessment_generator import generate_assessment
from services.generators.facilitator_guide_generator import (
    generate_facilitator_guide,
)
from services.generators.lesson_plan_generator import generate_lesson_plan
from services.generators.teaching_script_generator import generate_teaching_script


def generate_training_pack(
    project_name: str,
    module_name: str,
    duration: float,
    provider: AIProvider,
) -> dict[str, str]:
    """Generate all training-pack documents sequentially.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module for which to generate the training pack.
        duration: Planned session duration in hours.
        provider: Configured provider used by each generator.

    Returns:
        Generated Markdown keyed by training-pack document type.
    """

    lesson_plan = generate_lesson_plan(
        project_name,
        module_name,
        duration,
        provider,
    )
    facilitator_guide = generate_facilitator_guide(
        project_name,
        module_name,
        duration,
        provider,
    )
    teaching_script = generate_teaching_script(
        project_name,
        module_name,
        duration,
        provider,
    )
    assessment = generate_assessment(
        project_name,
        module_name,
        10,
        "Moderate",
        provider,
    )

    return {
        "lesson_plan": lesson_plan,
        "facilitator_guide": facilitator_guide,
        "teaching_script": teaching_script,
        "assessment": assessment,
    }
