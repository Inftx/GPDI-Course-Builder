import os

from dotenv import load_dotenv
from google import genai

from modules.ai_provider import AIProvider

load_dotenv()


class GeminiProvider(AIProvider):

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in .env file."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        # Change this in one place if needed
        self.model = "gemini-2.0-flash"

    def generate(self, prompt):

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text