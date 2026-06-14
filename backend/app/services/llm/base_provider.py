from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generates text given a prompt and optional system instructions.
        """
        pass

    @abstractmethod
    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a structured JSON object given a prompt and optional system instructions.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verifies connectivity to the LLM service.
        """
        pass
