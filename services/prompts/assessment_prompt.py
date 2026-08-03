"""Prompt builder for assessment generation."""

from services.prompts.prompt_manager import build_prompt


def build_assessment_prompt(
    context: str,
    qualification: str,
    module_name: str,
    duration_hours: float,
    generation_profile: str,
    number_of_questions: int,
    difficulty: str,
) -> str:
    """Return the assessment prompt string."""

    return build_prompt(
        """
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

{context}

{generation_profile}
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
        number_of_questions=number_of_questions,
        difficulty=difficulty,
    )
