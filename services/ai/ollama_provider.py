import os

import ollama

from services.ai.ai_provider import AIProvider


class OllamaProvider(AIProvider):

    def __init__(self):

        self.model = self._resolve_model()

    @staticmethod
    def _resolve_model():

        configured_model = os.getenv("OLLAMA_MODEL")

        if configured_model and configured_model.strip():

            return configured_model.strip()

        return "gemma3:1b"

    def generate(
        self,
        prompt
    ):

        response = ollama.chat(

            model=self.model,

            messages=[

                {

                    "role": "user",

                    "content": prompt

                }

            ]

        )

        return response["message"]["content"]
