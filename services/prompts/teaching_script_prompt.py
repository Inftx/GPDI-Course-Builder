"""Prompt builder for teaching-script generation."""

from services.prompts.prompt_manager import build_prompt


def build_teaching_script_prompt(
    context: str,
    qualification: str,
    module_name: str,
    duration_hours: float,
    generation_profile: str,
) -> str:
    """Return the teaching-script prompt string."""

    return build_prompt(
        """
You are writing the FINAL teaching script document.

Do not explain what you are going to do.
Do not describe sections.
Write the complete finished teaching script only.

Never describe the output.
Never use instructional phrases such as Provide, Generate, Expand, Include, or Examples below.
Never output placeholders, ellipses (...), template text, TODOs, notes, or unfinished content.

You are an expert training facilitator writing a complete teaching script from the supplied course context only.
Do not invent information outside the supplied course context.

COURSE CONTEXT
{context}

SESSION DETAILS
Session Duration: {duration_hours} hours

REQUIREMENTS
Write a complete Markdown teaching script with all required sections fully developed: Module Information, Facilitator Opening, Icebreaker, Introduction, Section-by-Section Script, Practical Activity Facilitation, Common Questions & Suggested Answers, Lesson Summary, Homework Instructions, and Closing Remarks.

Return only the Markdown teaching script.

Begin writing the teaching script now.
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
    )
