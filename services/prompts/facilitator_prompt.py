"""Prompt builder for facilitator-guide generation."""

from services.prompts.prompt_manager import build_prompt


def build_facilitator_prompt(
    context: str,
    qualification: str,
    module_name: str,
    duration_hours: float,
    generation_profile: str,
) -> str:
    """Return the facilitator-guide prompt string."""

    return build_prompt(
        """
You are writing the FINAL facilitator guide document.

Do not explain what you are going to do.
Do not describe sections.
Write the complete finished facilitator guide only.

Never describe the output.
Never use instructional phrases such as Provide, Generate, Expand, Include, or Examples below.
Never output placeholders, ellipses (...), template text, TODOs, notes, or unfinished content.

You are an expert facilitator guide writer working from the supplied course context only.
Do not invent information outside the supplied course context.

COURSE CONTEXT
{context}

SESSION DETAILS
Qualification: {qualification}
Module: {module_name}
Duration: {duration_hours} hours

REQUIREMENTS
Write a complete Markdown facilitator guide with all required sections fully developed: Qualification, Module, Duration, Session Overview, Learning Outcomes, Teaching Approach, Facilitator Notes, Activity Instructions, Discussion Points, Assessment Suggestions, and Reflection Questions.

Return only the Markdown facilitator guide.

Begin writing the facilitator guide now.
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
    )
