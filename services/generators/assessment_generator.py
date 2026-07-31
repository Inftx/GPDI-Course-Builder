"""Generate assessments through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document


def generate_assessment(
    project_name: str,
    module_name: str,
    number_of_questions: int,
    difficulty: str,
    ai_provider: AIProvider,
) -> str:
    """Generate and save a context-grounded Markdown assessment.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module used to retrieve the assessment context.
        number_of_questions: Number of questions for Sections A and B.
        difficulty: Required difficulty level for all questions.
        ai_provider: Configured provider used to generate AI content.

    Returns:
        The generated assessment Markdown.
    """

    prompt_template = f"""
Generate a professional Markdown assessment using only the retrieved course
context below. Do not add facts, requirements, or examples that are absent
from the course context.

# Assessment

## Instructions

## Section A
{number_of_questions} Multiple Choice Questions

## Section B
{number_of_questions} Short Answer Questions

## Section C
5 Scenario-Based Questions

## Marking Guide

## Memorandum

Assessment Settings

Module: {module_name}
Difficulty: {difficulty}

Course Context

{{context}}
"""

    return generate_document(
        project_name,
        module_name,
        0.0,
        "assessments",
        prompt_template,
        ai_provider,
    )
