"""Generate facilitator guides through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document


FACILITATOR_GUIDE_PROMPT_TEMPLATE = """
Generate a professional facilitator guide in Markdown using the course context
below. Use the following structure exactly, completing every section with
relevant, practical educational content.

# Facilitator Guide

## Qualification Information

## Module Information

## Purpose of the Module

## Learning Outcomes

## Session Preparation

## Required Resources

## Facilitation Notes

## Teaching Strategy

## Suggested Activities

## Discussion Questions

## Practical Activities

## Assessment Guidance

## Common Learner Challenges

## Tips for Facilitators

## Closing Summary

Course Context

{context}

Guide Details

Qualification: {qualification}
Module: {module_name}
Duration: {duration_hours} hours
"""


def generate_facilitator_guide(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
) -> str:
    """Generate and save a professional Markdown facilitator guide.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module for which to generate the guide.
        duration_hours: Planned facilitation duration in hours.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated facilitator-guide Markdown.
    """

    return generate_document(
        project_name,
        module_name,
        duration_hours,
        "facilitator_guides",
        FACILITATOR_GUIDE_PROMPT_TEMPLATE,
        ai_provider,
    )
