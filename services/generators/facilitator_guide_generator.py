"""Generate facilitator guides through the shared document generator."""

from services.ai.ai_provider import AIProvider
from services.generators.base_generator import generate_document


FACILITATOR_GUIDE_PROMPT_TEMPLATE = """
Generate a complete professional facilitator guide in Markdown using only the
retrieved course context below. Do not add facts, requirements, or examples
that are absent from the course context. Use the session duration only to plan
the guide's pacing.

# Facilitator Guide

## Module Information

## Learning Outcomes

## Session Objectives

## Required Resources

## Preparation Checklist

## Lesson Delivery

### Introduction

### Main Lesson

### Practical Activities

### Group Activities

### Discussion Questions

### Assessment Preparation

### Common Learner Questions

### Facilitator Tips

### Summary

### Homework

Course Context

{context}

Guide Details

Session Duration: {duration_hours} hours
"""


def generate_facilitator_guide(
    project_name: str,
    module_name: str,
    duration_hours: float,
    ai_provider: AIProvider,
) -> str:
    """Generate and save a context-grounded Markdown facilitator guide.

    Args:
        project_name: Name of the project containing processed knowledge.
        module_name: Module used to retrieve the guide context.
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
