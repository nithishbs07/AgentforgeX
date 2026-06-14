import json
import logging
import requests
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider
from app.services.embedding_service import is_ollama_online

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not is_ollama_online(self.base_url):
            raise ConnectionError("Ollama is offline")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Ollama generation error: {e}")

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        if not is_ollama_online(self.base_url):
            raise ConnectionError("Ollama is offline")

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        if system_instruction:
            payload["system"] = system_instruction

        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            response_text = str(data.get("response", "")).strip()
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Ollama JSON generation failed: {e}")
            raise RuntimeError(f"Ollama JSON generation error: {e}")

    def health_check(self) -> bool:
        return is_ollama_online(self.base_url)
