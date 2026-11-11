"""Ollama provider with an explicit context size and per-call measurements.

Configuration (environment variables, all optional):

    OLLAMA_MODEL    Model name.                    Default: qwen2.5:3b
    OLLAMA_HOST     Ollama server address.         Default: http://127.0.0.1:11434
    OLLAMA_NUM_CTX  Context window sent with every Default: 4096
                    request (tokens, whole number > 0).

``OLLAMA_NUM_CTX`` is this application's own setting. It is passed to Ollama
as the per-request ``num_ctx`` option, which overrides the server default.
It is unrelated to the server-side ``OLLAMA_CONTEXT_LENGTH`` variable.

Every successful call stores its measurements in ``last_generation`` and
prints one summary line, matching how the rest of the application reports
diagnostics. Measuring never changes the generated text and can never make
a generation fail.
"""

import os
import time
from typing import Any

import ollama

from services.ai.ai_provider import AIProvider

DEFAULT_HOST = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_NUM_CTX = 4096
REQUEST_TIMEOUT_SECONDS = 600.0
_NANOSECONDS = 1_000_000_000


def _read_metric(response: Any, name: str) -> Any:
    """Return a response attribute, or None when the response lacks it."""

    return getattr(response, name, None)


def _seconds(nanoseconds: Any) -> float | None:
    """Convert an Ollama nanosecond duration to seconds."""

    if isinstance(nanoseconds, (int, float)) and not isinstance(
        nanoseconds, bool
    ):
        return round(nanoseconds / _NANOSECONDS, 2)
    return None


class OllamaProvider(AIProvider):

    def __init__(self):
        self.model = self._resolve_model()

        self.host = os.getenv(
            "OLLAMA_HOST",
            DEFAULT_HOST,
        ).strip().rstrip("/")

        self.num_ctx = self._resolve_num_ctx()

        self.client = ollama.Client(
            host=self.host,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        # Measurements from the most recent successful generate() call.
        self.last_generation: dict[str, Any] | None = None

    @staticmethod
    def _resolve_model():
        configured_model = os.getenv("OLLAMA_MODEL")

        if configured_model and configured_model.strip():
            return configured_model.strip()

        return DEFAULT_MODEL

    @staticmethod
    def _resolve_num_ctx() -> int:
        """Read OLLAMA_NUM_CTX, failing loudly on an invalid value."""

        raw_value = os.getenv("OLLAMA_NUM_CTX")

        if raw_value is None or not raw_value.strip():
            return DEFAULT_NUM_CTX

        message = (
            "OLLAMA_NUM_CTX must be a whole number greater than zero "
            f"(for example 4096); got {raw_value!r}."
        )

        try:
            value = int(raw_value.strip())
        except ValueError:
            raise ValueError(message) from None

        if value <= 0:
            raise ValueError(message)

        return value

    def generate(self, prompt):
        started = time.perf_counter()

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={"num_ctx": self.num_ctx},
            )

            self._record_generation(
                response,
                prompt,
                time.perf_counter() - started,
            )

            content = response.message.content

            if not content or not content.strip():
                raise ValueError(
                    "Ollama returned an empty response."
                )

            return content

        except Exception as exc:
            raise RuntimeError(
                f"Ollama generation failed using model "
                f"'{self.model}' at '{self.host}': {exc}"
            ) from exc

    def _record_generation(
        self,
        response: Any,
        prompt: str,
        wall_seconds: float,
    ) -> None:
        """Store and print the measurements for one call.

        Instrumentation must never break generation, so any failure here is
        reported and swallowed.
        """

        try:
            prompt_tokens = _read_metric(response, "prompt_eval_count")
            output_tokens = _read_metric(response, "eval_count")
            done_reason = _read_metric(response, "done_reason")
            prompt_chars = len(prompt)

            context_used = None
            if isinstance(prompt_tokens, int) and isinstance(
                output_tokens, int
            ):
                context_used = prompt_tokens + output_tokens

            # An indicator only: an unusually high value can mean the prompt
            # was cut off; a cached prompt prefix can also raise it.
            chars_per_token = None
            if isinstance(prompt_tokens, int) and prompt_tokens > 0:
                chars_per_token = round(prompt_chars / prompt_tokens, 1)

            self.last_generation = {
                "model": self.model,
                "num_ctx": self.num_ctx,
                "prompt_chars": prompt_chars,
                "prompt_eval_count": prompt_tokens,
                "eval_count": output_tokens,
                "context_used": context_used,
                "chars_per_prompt_token": chars_per_token,
                "done_reason": done_reason,
                "wall_seconds": round(wall_seconds, 2),
                "total_seconds": _seconds(
                    _read_metric(response, "total_duration")
                ),
                "load_seconds": _seconds(
                    _read_metric(response, "load_duration")
                ),
                "prompt_eval_seconds": _seconds(
                    _read_metric(response, "prompt_eval_duration")
                ),
                "eval_seconds": _seconds(
                    _read_metric(response, "eval_duration")
                ),
            }

            record = self.last_generation
            print(
                "Ollama generation: "
                f"model={record['model']!r}, "
                f"num_ctx={record['num_ctx']}, "
                f"prompt_chars={record['prompt_chars']}, "
                f"prompt_tokens={record['prompt_eval_count']}, "
                f"output_tokens={record['eval_count']}, "
                f"context_used={record['context_used']}, "
                f"chars_per_prompt_token={record['chars_per_prompt_token']}, "
                f"done_reason={record['done_reason']!r}, "
                f"wall_seconds={record['wall_seconds']}"
            )

            if done_reason == "length":
                print(
                    "WARNING: Ollama stopped because it reached its output "
                    "limit (done_reason='length'); the text may be cut off."
                )

            if context_used is not None and context_used >= self.num_ctx:
                print(
                    "WARNING: the context window is full "
                    f"({context_used} of {self.num_ctx} tokens used); "
                    "the prompt or the answer may have been cut off."
                )

        except Exception as exc:  # noqa: BLE001
            self.last_generation = None
            print(f"Ollama generation: measurements unavailable ({exc}).")
