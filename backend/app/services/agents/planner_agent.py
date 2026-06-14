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

class PlannerAgent:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Decomposes the user query into sub-questions, estimates depth, and sets retrieval strategies.
        """
        start_time = time.time()
        query = state.get("query", "")

        # 1. Load prompt template
        prompt_path = os.path.join(PROMPTS_DIR, "planner_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except Exception as e:
            logger.error(f"Failed to read planner prompt template: {e}")
            prompt_template = "Decompose this query into sub-questions: {query}"

        prompt = prompt_template.format(query=query)

        # Defaults
        main_query = query
        sub_questions = []
        research_depth = "shallow"
        retrieval_modes = []

        # 2. Call LLM Provider
        try:
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            parsed_res = provider.generate_json(prompt)
            main_query = parsed_res.get("main_query", query)
            sub_questions = parsed_res.get("sub_questions", [])
            research_depth = parsed_res.get("research_depth", "shallow")
            retrieval_modes = parsed_res.get("retrieval_modes", [])

        except Exception as e:
            logger.warning(f"LLM planner request failed: {e}. Using heuristics fallback.")
            sub_questions = []

        # Heuristic fallbacks if sub_questions list is empty or invalid
        if not sub_questions:
            query_lower = query.lower()
            if any(word in query_lower for word in ["relationship", "connects", "depends", "uses", "belongs", "structure", "graph", "traversal"]):
                sub_questions = [
                    f"Structural connections and relationships for {query}",
                    f"Core definition and role of concepts in {query}"
                ]
                retrieval_modes = ["graph", "vector"]
                research_depth = "medium"
            elif any(word in query_lower for word in ["compare", "difference", "versus", "vs", "both"]):
                sub_questions = [
                    f"Detailing concepts in {query}",
                    f"Direct comparison of terms in {query}"
                ]
                retrieval_modes = ["hybrid", "hybrid"]
                research_depth = "deep"
            else:
                sub_questions = [
                    query,
                    f"Key background details on {query}"
                ]
                retrieval_modes = ["vector", "vector"]
                research_depth = "shallow"

        # Post-process to respect constraints
        # Constraint: Never produce more than 5 sub-questions
        if len(sub_questions) > 5:
            logger.info("Truncating sub-questions to maximum limit of 5.")
            sub_questions = sub_questions[:5]
        
        # Avoid redundant sub-questions (deduplicate case-insensitive and whitespace-stripped)
        seen = set()
        deduped_questions = []
        deduped_modes = []
        for i, sq in enumerate(sub_questions):
            norm = sq.strip().lower().rstrip("?")
            if norm and norm not in seen:
                seen.add(norm)
                deduped_questions.append(sq)
                # Map matching mode or default to vector
                mode = retrieval_modes[i] if i < len(retrieval_modes) else "vector"
                if mode not in ["vector", "graph", "hybrid"]:
                    mode = "vector"
                deduped_modes.append(mode)
        
        # Ensure we have at least one valid question
        if not deduped_questions:
            deduped_questions = [query]
            deduped_modes = ["vector"]

        sub_questions = deduped_questions
        retrieval_modes = deduped_modes

        # Enforce valid research depth values
        if research_depth not in ["shallow", "medium", "deep"]:
            research_depth = "shallow"

        elapsed_sec = time.time() - start_time
        elapsed_ms = int(elapsed_sec * 1000)

        # Update metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["planner_time_ms"] = elapsed_ms
        execution_metadata["research_depth"] = research_depth
        execution_metadata["sub_question_count"] = len(sub_questions)

        return {
            "sub_questions": sub_questions,
            "research_depth": research_depth,
            "retrieval_modes": retrieval_modes,
            "planner_latency": elapsed_sec,
            "execution_metadata": execution_metadata
        }
