"""Generate lesson plans through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document


LESSON_PLAN_PROMPT_TEMPLATE = """
Generate a professional lesson plan in Markdown using the course context below.
Use the following structure exactly, completing every section with relevant,
practical educational content.

# Lesson Plan

## Qualification

## Module

## Duration

## Learning Outcomes

## Learning Objectives

## Resources Required

## Introduction

## Lesson Activities

## Facilitator Notes

## Learner Activities

## Formative Assessment

## Reflection

## Homework

Course Context

{context}

Lesson Details

Qualification: {qualification}
Module: {module_name}
Duration: {duration_hours} hours
"""


def generate_lesson_plan(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
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

    return generate_document(
        project_name,
        module_name,
        duration_hours,
        "lesson_plans",
        LESSON_PLAN_PROMPT_TEMPLATE,
        ai_provider,
    )
