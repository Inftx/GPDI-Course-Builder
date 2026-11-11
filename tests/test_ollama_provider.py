"""Focused tests for services.ai.ollama_provider.

These tests use a fake client. They check configuration and response
handling only; they do not prove that a real model follows a prompt. Use
the manual Ollama check in the Step 1 notes for that.
"""

import contextlib
import io
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.ai import ollama_provider
from services.ai.ollama_provider import OllamaProvider

ENV_KEYS = ("OLLAMA_MODEL", "OLLAMA_HOST", "OLLAMA_NUM_CTX")


def make_response(content="Generated text", **overrides):
    values = {
        "message": SimpleNamespace(content=content),
        "prompt_eval_count": 2050,
        "eval_count": 400,
        "done_reason": "stop",
        "total_duration": 93_000_000_000,
        "load_duration": 1_500_000_000,
        "prompt_eval_duration": 80_000_000_000,
        "eval_duration": 11_000_000_000,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class OllamaProviderTestCase(unittest.TestCase):
    def setUp(self):
        env_patch = patch.dict(os.environ, {}, clear=False)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        for key in ENV_KEYS:
            os.environ.pop(key, None)

    def build_provider(self, response=None):
        client = MagicMock()
        client.chat.return_value = response or make_response()
        with patch.object(
            ollama_provider.ollama,
            "Client",
            return_value=client,
        ) as client_class:
            provider = OllamaProvider()
        return provider, client, client_class


class ConfigurationTests(OllamaProviderTestCase):
    def test_defaults(self):
        provider, _, client_class = self.build_provider()

        self.assertEqual(provider.model, "qwen2.5:3b")
        self.assertEqual(provider.host, "http://127.0.0.1:11434")
        self.assertEqual(provider.num_ctx, 4096)
        client_class.assert_called_once_with(
            host="http://127.0.0.1:11434",
            timeout=600.0,
        )

    def test_environment_overrides(self):
        os.environ["OLLAMA_MODEL"] = "  qwen2.5:1.5b "
        os.environ["OLLAMA_HOST"] = " http://localhost:9999/ "
        os.environ["OLLAMA_NUM_CTX"] = " 8192 "

        provider, _, client_class = self.build_provider()

        self.assertEqual(provider.model, "qwen2.5:1.5b")
        self.assertEqual(provider.host, "http://localhost:9999")
        self.assertEqual(provider.num_ctx, 8192)
        client_class.assert_called_once_with(
            host="http://localhost:9999",
            timeout=600.0,
        )

    def test_blank_num_ctx_uses_default(self):
        os.environ["OLLAMA_NUM_CTX"] = "   "

        provider, _, _ = self.build_provider()

        self.assertEqual(provider.num_ctx, 4096)

    def test_invalid_num_ctx_fails_loudly(self):
        for bad_value in ("abc", "0", "-5", "40.96", "4k"):
            with self.subTest(value=bad_value):
                os.environ["OLLAMA_NUM_CTX"] = bad_value
                with self.assertRaises(ValueError) as caught:
                    self.build_provider()
                self.assertIn("OLLAMA_NUM_CTX", str(caught.exception))
                self.assertIn(repr(bad_value), str(caught.exception))


class GenerateTests(OllamaProviderTestCase):
    def test_request_carries_model_message_and_num_ctx(self):
        os.environ["OLLAMA_NUM_CTX"] = "6144"
        provider, client, _ = self.build_provider()

        with contextlib.redirect_stdout(io.StringIO()):
            result = provider.generate("Write a question.")

        self.assertEqual(result, "Generated text")
        client.chat.assert_called_once_with(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": "Write a question."}],
            options={"num_ctx": 6144},
        )

    def test_measurements_are_recorded(self):
        provider, _, _ = self.build_provider()
        prompt = "x" * 8200

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            provider.generate(prompt)

        record = provider.last_generation
        self.assertEqual(record["model"], "qwen2.5:3b")
        self.assertEqual(record["num_ctx"], 4096)
        self.assertEqual(record["prompt_chars"], 8200)
        self.assertEqual(record["prompt_eval_count"], 2050)
        self.assertEqual(record["eval_count"], 400)
        self.assertEqual(record["context_used"], 2450)
        self.assertEqual(record["chars_per_prompt_token"], 4.0)
        self.assertEqual(record["done_reason"], "stop")
        self.assertEqual(record["total_seconds"], 93.0)
        self.assertEqual(record["load_seconds"], 1.5)
        self.assertEqual(record["prompt_eval_seconds"], 80.0)
        self.assertEqual(record["eval_seconds"], 11.0)
        self.assertGreaterEqual(record["wall_seconds"], 0)
        self.assertIn("Ollama generation:", output.getvalue())
        self.assertIn("num_ctx=4096", output.getvalue())
        self.assertNotIn("WARNING", output.getvalue())

    def test_length_reason_and_full_context_warn(self):
        response = make_response(
            prompt_eval_count=3900,
            eval_count=300,
            done_reason="length",
        )
        provider, _, _ = self.build_provider(response)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = provider.generate("prompt")

        self.assertEqual(result, "Generated text")
        self.assertIn("done_reason='length'", output.getvalue())
        self.assertIn("context window is full", output.getvalue())

    def test_missing_metrics_do_not_break_generation(self):
        response = SimpleNamespace(
            message=SimpleNamespace(content="Plain text"),
        )
        provider, _, _ = self.build_provider(response)

        with contextlib.redirect_stdout(io.StringIO()):
            result = provider.generate("prompt")

        self.assertEqual(result, "Plain text")
        self.assertIsNone(provider.last_generation["prompt_eval_count"])
        self.assertIsNone(provider.last_generation["context_used"])
        self.assertIsNone(provider.last_generation["total_seconds"])

    def test_measuring_failure_never_fails_generation(self):
        provider, _, _ = self.build_provider()

        output = io.StringIO()
        with patch.object(
            ollama_provider,
            "_read_metric",
            side_effect=RuntimeError("boom"),
        ), contextlib.redirect_stdout(output):
            result = provider.generate("prompt")

        self.assertEqual(result, "Generated text")
        self.assertIsNone(provider.last_generation)
        self.assertIn("measurements unavailable", output.getvalue())

    def test_empty_response_raises_runtime_error_with_context(self):
        for content in ("", "   ", None):
            with self.subTest(content=content):
                provider, _, _ = self.build_provider(
                    make_response(content=content)
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError) as caught:
                        provider.generate("prompt")
                message = str(caught.exception)
                self.assertIn("qwen2.5:3b", message)
                self.assertIn("http://127.0.0.1:11434", message)
                self.assertIn("empty response", message)

    def test_client_errors_are_wrapped_as_before(self):
        provider, client, _ = self.build_provider()
        client.chat.side_effect = ConnectionError("server down")

        with self.assertRaises(RuntimeError) as caught:
            provider.generate("prompt")

        self.assertIn("server down", str(caught.exception))
        self.assertIsInstance(caught.exception.__cause__, ConnectionError)


if __name__ == "__main__":
    unittest.main()
