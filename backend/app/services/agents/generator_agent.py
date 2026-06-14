import os
import time
import requests
import logging
from typing import Dict, Any
from app.core.config import settings
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

class GeneratorAgent:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Generates the answer. If route is direct, calls Ollama directly.
        If route is retrieval, formats context chunks and uses generator_prompt.txt.
        Supports answer regeneration based on verifier feedback.
        """
        start_time = time.time()
        query = state.get("query", "")
        route = state.get("route", "direct")
        
        # Determine if this is a regeneration attempt
        # If we already have an answer in state, we are performing a regeneration
        is_regeneration = False
        attempts = state.get("verification_attempts", 0)
        if state.get("answer"):
            is_regeneration = True
            attempts = 1

        answer = ""

        if route == "direct":
            logger.info("GeneratorAgent: Direct LLM generation path triggered.")
            prompt = query
            if is_regeneration:
                prompt = "Previous answer was insufficiently supported by evidence. Generate a new answer strictly responding to: " + query
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        else:
            logger.info("GeneratorAgent: Retrieval-augmented LLM generation path triggered.")
            context_chunks = state.get("retrieved_chunks", [])
            
            # Format context chunks
            context_str = ""
            for idx, chunk in enumerate(context_chunks):
                filename = chunk.get("filename", "unknown")
                page = chunk.get("page_number", "unknown")
                text = chunk.get("chunk_text", "")
                context_str += f"\n--- Source {idx+1}: {filename} (Page {page}) ---\n{text}\n"

            # Load RAG prompt template from file
            prompt_path = os.path.join(PROMPTS_DIR, "generator_prompt.txt")
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    prompt_template = f.read()
            except Exception as e:
                logger.error(f"Failed to read generator prompt from file: {e}")
                prompt_template = "Context:\n{context}\n\nQuery: {query}\n\nAnswer:"

            prompt = prompt_template.format(context=context_str, query=query)
            if is_regeneration:
                if state.get("adaptive_retrieval_used") or state.get("retrieval_attempts", 1) == 2:
                    prompt = "Previous answer was insufficiently supported by evidence. Additional evidence has been retrieved. Generate a new answer strictly grounded in the expanded context.\n\n" + prompt
                else:
                    prompt = "Previous answer was insufficiently supported by evidence. Generate a new answer strictly using the provided context.\n\n" + prompt

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

        try:
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            answer = provider.generate(prompt)
        except Exception as e:
            logger.error(f"LLM generation request failed: {e}")
            if settings.DEBUG:
                logger.warning("Fallback: Generating Mock LLM response under DEBUG mode.")
                if route == "direct":
                    if is_regeneration:
                        answer = f"[Mock Direct Response - Regenerated] Answer to: '{query}'."
                    else:
                        answer = f"[Mock Direct Response] Answer to: '{query}'."
                else:
                    if is_regeneration:
                        answer = f"[Mock RAG Response - Regenerated] Answer for query '{query}' generated from context chunks."
                    else:
                        answer = f"[Mock RAG Response] Answer for query '{query}' generated from context chunks."
            else:
                raise RuntimeError(f"LLM generation failed: {e}")

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Update metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["generator_time_ms"] = elapsed_ms
        if is_regeneration:
            execution_metadata["regenerated"] = True
        if route == "direct":
            execution_metadata["retrieval_used"] = False

        return {
            "answer": answer,
            "verification_attempts": attempts,
            "execution_metadata": execution_metadata
        }
