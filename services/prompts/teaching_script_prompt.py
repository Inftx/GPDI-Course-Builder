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

{generation_profile}
""",
        context=context,
        qualification=qualification,
        module_name=module_name,
        duration_hours=duration_hours,
        generation_profile=generation_profile,
    )
