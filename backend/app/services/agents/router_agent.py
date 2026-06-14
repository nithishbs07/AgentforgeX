import os
import time
import json
import requests
import logging
from typing import Dict, Any
from app.core.config import settings
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

class RouterAgent:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Routes queries to 'direct' or 'retrieval' path.
        """
        start_time = time.time()
        query = state.get("query", "")

        # 1. Load prompt template from file
        prompt_path = os.path.join(PROMPTS_DIR, "router_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except Exception as e:
            logger.error(f"Failed to read router prompt from file: {e}")
            prompt_template = "Classify if query needs retrieval. Query: {query}"

        prompt = prompt_template.format(query=query)

        # Defaults
        route = "direct"
        route_confidence = 0.5

        # 2. Primary: LLM classification using Factory
        try:
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            parsed_res = provider.generate_json(prompt)
            route = str(parsed_res.get("route", "direct")).strip().lower()
            route_confidence = float(parsed_res.get("route_confidence", 0.5))

            if route == "retrieval":
                route = "vector"
            if route not in ["direct", "vector", "graph", "hybrid"]:
                route = "direct"

        except Exception as e:
            logger.warning(f"Ollama route classification connection refused or failed: {e}. Falling back to heuristics.")
            # Fallback heuristics
            query_lower = query.lower()
            if any(word in query_lower for word in ["relationship", "connects", "depends", "uses", "belongs", "structure", "graph", "traversal"]):
                route = "graph"
                route_confidence = 0.90
            elif any(word in query_lower for word in ["both", "compare", "relationship between", "and its relationship"]):
                route = "hybrid"
                route_confidence = 0.88
            elif any(word in query_lower for word in ["chapter", "document", "pdf", "uploaded", "summarize", "file", "ingest", "read"]):
                route = "vector"
                route_confidence = 0.90
            else:
                route = "direct"
                route_confidence = 0.80

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Update metadata dictionary
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["router_time_ms"] = elapsed_ms
        execution_metadata["selected_route"] = route
        execution_metadata["route_confidence"] = route_confidence

        return {
            "route": route,
            "route_confidence": route_confidence,
            "execution_metadata": execution_metadata
        }
