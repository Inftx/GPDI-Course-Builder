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
Generate a professional facilitator guide in Markdown using only the retrieved
course context below. Do not add facts, requirements, or examples that are
absent from the course context. Structure the content for a facilitator
running a training session.

# Facilitator Guide

## Qualification

## Module

## Duration

## Session Overview

## Learning Outcomes

## Teaching Approach

## Facilitator Notes

## Activity Instructions

## Discussion Points

## Assessment Suggestions

## Reflection Questions

Course Context

{context}

Session Details

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
