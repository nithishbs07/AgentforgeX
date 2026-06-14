import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from app.core.config import settings
from app.services.llm.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.timeout = settings.GEMINI_TIMEOUT
        
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": self.temperature,
                }
            )
            response = model.generate_content(
                prompt,
                request_options={"timeout": self.timeout}
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise RuntimeError(f"Gemini API generation error: {e}")

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment variables.")

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": self.temperature,
                    "response_mime_type": "application/json",
                }
            )
            response = model.generate_content(
                prompt,
                request_options={"timeout": self.timeout}
            )
            response_text = response.text.strip()
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Gemini JSON generation failed: {e}")
            raise RuntimeError(f"Gemini API JSON generation error: {e}")

    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            # Use a fast check to verify API key validity and connectivity
            # Prompting with a simple greeting ensures low latency
            model.generate_content("hello", request_options={"timeout": 5})
            return True
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False
