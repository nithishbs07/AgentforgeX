import requests
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaGenerationService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Formats context source blocks and sends prompt instructions to the local Ollama LLM.
        """
        # Assemble retrieved document texts into readable context blocks
        context_str = ""
        for idx, chunk in enumerate(context_chunks):
            filename = chunk.get("filename", "unknown")
            page = chunk.get("page_number", "unknown")
            text = chunk.get("chunk_text", "")
            context_str += f"\n--- Source {idx+1}: {filename} (Page {page}) ---\n{text}\n"

        system_instructions = (
            "You are a production-grade local-first RAG assistant. You must formulate your answer using only the provided context.\n"
            "Strict constraints:\n"
            "- Answer the query using ONLY the evidence provided in the context.\n"
            "- If the context does not contain the answer, say 'I cannot answer this based on the provided context.'\n"
            "- Do not synthesize or extrapolate beyond the explicit context evidence.\n"
            "- Prefer citing source filenames and page numbers if referring to statements.\n"
            "- Keep your response clear, factual, and concise."
        )

        user_content = f"Context:\n{context_str}\n\nQuery: {query}\n\nAnswer:"

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": user_content,
            "system": system_instructions,
            "stream": False
        }

        try:
            from app.services.embedding_service import is_ollama_online
            if not is_ollama_online(self.base_url):
                raise ConnectionError("Ollama is offline (DEBUG mode fallback)")

            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()
        except Exception as e:
            logger.error(f"Failed to generate answer from Ollama LLM service: {e}")
            if settings.DEBUG:
                logger.warning("Fallback: generating Mock RAG Answer under DEBUG mode")
                return f"[Mock RAG Response] Answer for query '{query}' generated from context chunks."
            raise RuntimeError(f"Ollama generation failed: {e}")
