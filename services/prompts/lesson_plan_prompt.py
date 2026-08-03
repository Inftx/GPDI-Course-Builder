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

{generation_profile}
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
    )
