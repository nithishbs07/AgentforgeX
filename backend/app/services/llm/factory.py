from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider

class LLMFactory:
    _provider_instance = None

    @classmethod
    def get_provider(cls) -> BaseLLMProvider:
        if cls._provider_instance is None:
            provider_type = settings.LLM_PROVIDER.lower()
            if provider_type == "gemini":
                cls._provider_instance = GeminiProvider()
            else:
                cls._provider_instance = OllamaProvider()
        return cls._provider_instance

    @classmethod
    def reset_provider(cls) -> None:
        """Resets the cached provider instance, useful if config changes dynamically."""
        cls._provider_instance = None
