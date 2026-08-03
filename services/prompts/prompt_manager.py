"""Central prompt-manager helpers for generator prompt builders."""

from __future__ import annotations

from typing import Any


def build_prompt(prompt: str, **context: Any) -> str:
    """Render a prompt template with simple named placeholders."""

    rendered = prompt
    for key, value in context.items():
        rendered = rendered.replace(f"{{{key}}}", str(value))
    return rendered
