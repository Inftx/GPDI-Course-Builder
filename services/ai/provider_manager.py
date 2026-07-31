class ProviderManager:

    @staticmethod
    def get_provider(provider_name):

        if provider_name == "ollama":
            from services.ai.ollama_provider import OllamaProvider

            return OllamaProvider()

        if provider_name == "gemini":
            from services.ai.gemini_provider import GeminiProvider

            return GeminiProvider()

        raise ValueError(
            f"Unknown provider: {provider_name}"
        )
