from dataclasses import dataclass, field
from typing import Any


@dataclass
class GenerationWizardState:
    project: str | None = None
    module: str | None = None
    module_label: str | None = None
    knowledge_topic: str | None = None
    knowledge_topic_label: str | None = None
    output_type: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    step: int = 1


class GenerationWizard:
    STEPS = [
        "Select Project",
        "Select Module",
        "Select Output Type",
        "Configure Options",
        "Review",
        "Generate",
    ]

    def __init__(self) -> None:
        self._state = GenerationWizardState()

    def current_step(self) -> str:
        return self.STEPS[self._state.step - 1]

    def next_step(self) -> None:
        if self._state.step < len(self.STEPS):
            self._state.step += 1

    def previous_step(self) -> None:
        if self._state.step > 1:
            self._state.step -= 1

    def go_to_step(self, step: int) -> None:
        if 1 <= step <= len(self.STEPS):
            self._state.step = step

    def set_project(self, name: str) -> None:
        if self._state.project != name:
            self._state.module = None
            self._state.module_label = None
            self._state.knowledge_topic = None
            self._state.knowledge_topic_label = None
        self._state.project = name

    def set_module(self, identifier: str, label: str | None = None) -> None:
        if self._state.module != identifier:
            self._state.knowledge_topic = None
            self._state.knowledge_topic_label = None
        self._state.module = identifier
        self._state.module_label = label or identifier

    def set_knowledge_topic(
        self,
        identifier: str | None,
        label: str | None = None,
    ) -> None:
        self._state.knowledge_topic = identifier
        self._state.knowledge_topic_label = label or identifier

    def set_output_type(self, output_type: str) -> None:
        self._state.output_type = output_type

    def set_options(self, options: dict[str, Any]) -> None:
        self._state.options = options.copy()

    def get_state(self) -> GenerationWizardState:
        return self._state

    def reset(self) -> None:
        self._state = GenerationWizardState()
