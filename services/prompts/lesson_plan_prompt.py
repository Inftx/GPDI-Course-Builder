"""Prompt builder for lesson-plan generation."""

from services.prompts.prompt_manager import build_prompt


def build_lesson_plan_prompt(
    context: str,
    qualification: str,
    module_name: str,
    duration_hours: float,
    generation_profile: str,
) -> str:
    """Return the lesson-plan prompt string."""

    return build_prompt(
        """
You are writing the FINAL lesson plan document.

Do not explain what you are going to do.
Do not describe sections.
Write the complete finished lesson plan only.

Never describe the output.
Never use instructional phrases such as Provide, Generate, Expand, Include, or Examples below.
Never output placeholders, ellipses (...), template text, TODOs, notes, or unfinished content.

You are an expert curriculum developer writing a complete lesson plan from the supplied course context only.
Do not invent information outside the supplied course context.

COURSE CONTEXT
{context}

LESSON DETAILS
Qualification: {qualification}
Module: {module_name}
Duration: {duration_hours} hours

REQUIREMENTS
Write a complete Markdown lesson plan with all required sections fully developed: Qualification, Module, Duration, Learning Outcomes, Learning Objectives, Resources Required, Introduction, Lesson Activities, Facilitator Notes, Learner Activities, Formative Assessment, Reflection, and Homework.

Return only the Markdown lesson plan.

Begin writing the lesson plan now.
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
    )
