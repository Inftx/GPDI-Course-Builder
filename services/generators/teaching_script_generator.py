"""Generate teaching scripts through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document


TEACHING_SCRIPT_PROMPT_TEMPLATE = """
Generate a conversational facilitator teaching script in Markdown using only
the retrieved course context below. Do not add facts, requirements, or examples
that are absent from the course context. Include practical timings appropriate
to the stated session duration.

# Teaching Script

## Module Information

## Facilitator Opening

## Icebreaker

## Introduction

## Section-by-Section Script

For every learning outcome, explain the content, give real-world examples, ask
learner questions, suggest demonstrations, provide transition statements, and
include expected learner responses.

## Practical Activity Facilitation

## Common Questions & Suggested Answers

## Lesson Summary

## Homework Instructions

## Closing Remarks

Course Context

{context}

Session Details

Session Duration: {duration_hours} hours
"""


def generate_teaching_script(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
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

    return generate_document(
        project_name,
        module_name,
        duration_hours,
        "teaching_scripts",
        TEACHING_SCRIPT_PROMPT_TEMPLATE,
        ai_provider,
    )
