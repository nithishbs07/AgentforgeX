import os
import time
import json
import requests
import logging
from typing import Dict, Any
from app.core.config import settings
from app.services.agents.state import AgentState
from app.services.embedding_service import is_ollama_online

logger = logging.getLogger(__name__)
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

class VerifierAgent:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes two-stage verification (Rule-based + LLM evaluation).
        Updates state with verification scores, status, and status reason.
        """
        start_time = time.time()
        query = state.get("query", "")
        answer = state.get("answer", "")
        retrieved_chunks = state.get("retrieved_chunks", [])
        citations = state.get("citations", [])
        route = state.get("route", "direct")

        # 1. Stage 1: Rule-Based Verification
        rule_score, grounding_score, evidence_coverage = self._calculate_rule_metrics(query, answer, retrieved_chunks, citations, route)

        # 2. Stage 2: LLM Verification using Ollama
        llm_score, verification_status, verification_reason = self._execute_llm_verification(query, answer, retrieved_chunks, route, rule_score)

        # 3. Combine Scores
        # Formula: verification_score = (rule_score * 0.4) + (llm_score * 0.6)
        verification_score = round(float((rule_score * 0.4) + (llm_score * 0.6)), 4)
        verification_score = max(0.0, min(1.0, verification_score))

        # 4. Status Mapping (Overwrite based on final verification score threshold)
        if verification_score > 0.80:
            verification_status = "SUPPORTED"
        elif 0.50 <= verification_score <= 0.80:
            verification_status = "PARTIALLY_SUPPORTED"
        else:
            verification_status = "UNSUPPORTED"

        verified = verification_score >= 0.60

        # Determine adaptive retrieval trigger reason if applicable
        adaptive_retrieval_reason = ""
        citations_count = len(citations)
        if verification_score < 0.60:
            adaptive_retrieval_reason = "Low Verification Score"
        elif grounding_score < 0.50:
            adaptive_retrieval_reason = "Low Grounding Score"
        elif route != "direct" and citations_count == 0:
            adaptive_retrieval_reason = "Insufficient Citations"
        elif route != "direct" and evidence_coverage < 0.50:
            adaptive_retrieval_reason = "Low Evidence Coverage"

        retrieval_attempts = state.get("retrieval_attempts", 1)
        if retrieval_attempts == 1:
            verification_score_before_adaptation = verification_score
            verification_score_after_adaptation = 0.0
            verification_improvement = 0.0
            grounding_score_before_adaptation = grounding_score
            grounding_score_after_adaptation = 0.0
            grounding_score_improvement = 0.0
        else:
            verification_score_before_adaptation = state.get("verification_score_before_adaptation", 0.0)
            verification_score_after_adaptation = verification_score
            verification_improvement = round(verification_score_after_adaptation - verification_score_before_adaptation, 4)
            prev_metadata = state.get("execution_metadata", {})
            grounding_score_before_adaptation = prev_metadata.get("grounding_score_before_adaptation", 0.0) if prev_metadata else 0.0
            grounding_score_after_adaptation = grounding_score
            grounding_score_improvement = round(grounding_score_after_adaptation - grounding_score_before_adaptation, 4)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Update metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["verifier_time_ms"] = elapsed_ms
        execution_metadata["grounding_score"] = grounding_score
        execution_metadata["verification_score"] = verification_score
        execution_metadata["verification_status"] = verification_status
        
        # Track triggers and before/after improvements
        if retrieval_attempts == 1:
            execution_metadata["adaptive_retrieval_reason"] = adaptive_retrieval_reason
        else:
            adaptive_retrieval_reason = state.get("adaptive_retrieval_reason", "")
            execution_metadata["adaptive_retrieval_reason"] = adaptive_retrieval_reason

        execution_metadata["verification_score_before_adaptation"] = verification_score_before_adaptation
        execution_metadata["verification_score_after_adaptation"] = verification_score_after_adaptation
        execution_metadata["verification_improvement"] = verification_improvement
        execution_metadata["grounding_score_before_adaptation"] = grounding_score_before_adaptation
        execution_metadata["grounding_score_after_adaptation"] = grounding_score_after_adaptation
        execution_metadata["grounding_score_improvement"] = grounding_score_improvement

        # Track verification metrics for graph and hybrid routes
        retrieval_mode = execution_metadata.get("retrieval_mode", state.get("retrieval_mode", route))
        if retrieval_mode == "graph":
            execution_metadata["graph_verification_score"] = verification_score
            execution_metadata["graph_grounding_score"] = grounding_score
        elif retrieval_mode == "hybrid":
            execution_metadata["hybrid_verification_score"] = verification_score
            execution_metadata["hybrid_grounding_score"] = grounding_score

        return {
            "verification_score": verification_score,
            "grounding_score": grounding_score,
            "verification_status": verification_status,
            "verification_reason": verification_reason,
            "verified": verified,
            "adaptive_retrieval_reason": adaptive_retrieval_reason,
            "verification_score_before_adaptation": verification_score_before_adaptation,
            "verification_score_after_adaptation": verification_score_after_adaptation,
            "verification_improvement": verification_improvement,
            "execution_metadata": execution_metadata
        }

    def _calculate_rule_metrics(self, query: str, answer: str, chunks: list, citations: list, route: str) -> tuple:
        """
        Computes rule-based score and grounding score.
        """
        def get_keywords(text: str) -> set:
            stop_words = {"the", "a", "is", "of", "and", "in", "to", "it", "that", "on", "for", "with", "as", "at", "by", "an", "be", "this", "are"}
            words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
            return {w for w in words if w not in stop_words and len(w) > 2}

        words_answer = get_keywords(answer)
        
        if route == "direct":
            # Direct route checks overlap with query keywords
            words_query = get_keywords(query)
            if words_query and words_answer:
                keyword_overlap = len(words_answer.intersection(words_query)) / len(words_query)
            else:
                keyword_overlap = 0.5
            
            # Citation presence: not expected for direct, give default full score
            citation_presence = 1.0
            
            # Evidence coverage: proxy by answer length and richness
            sentences = [s.strip() for s in answer.split(".") if s.strip()]
            if len(sentences) >= 2 or len(words_answer) >= 15:
                evidence_coverage = 1.0
            else:
                evidence_coverage = 0.5
        else:
            # Retrieval route: checks overlap with retrieved chunks
            words_chunks = set()
            for chunk in chunks:
                words_chunks.update(get_keywords(chunk.get("chunk_text", "")))

            if words_answer:
                keyword_overlap = len(words_answer.intersection(words_chunks)) / len(words_answer)
            else:
                keyword_overlap = 0.0

            # Citation presence
            citation_presence = 1.0 if citations else 0.0

            # Evidence coverage
            sentences = [s.strip() for s in answer.split(".") if s.strip()]
            covered = 0
            for s in sentences:
                s_words = get_keywords(s)
                if not s_words:
                    covered += 1
                elif words_chunks and len(s_words.intersection(words_chunks)) / len(s_words) >= 0.2:
                    covered += 1
            evidence_coverage = covered / len(sentences) if sentences else 0.0

        rule_score = (keyword_overlap * 0.4) + (citation_presence * 0.3) + (evidence_coverage * 0.3)
        grounding_score = (keyword_overlap * 0.5) + (evidence_coverage * 0.5)

        return round(rule_score, 4), round(grounding_score, 4), round(evidence_coverage, 4)

    def _execute_llm_verification(self, query: str, answer: str, chunks: list, route: str, rule_score: float) -> tuple:
        """
        Executes LLM verification step by querying Ollama.
        """
        # Load prompt template from file
        prompt_path = os.path.join(PROMPTS_DIR, "verifier_prompt.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except Exception as e:
            logger.error(f"Failed to read verifier prompt from file: {e}")
            prompt_template = "Verify if answer matches evidence. Query: {query} Evidence: {evidence} Answer: {answer}"

        if route == "direct":
            evidence = "No retrieved document evidence (direct-route query). Verify the answer's correctness and alignment with the query."
        else:
            evidence = ""
            for idx, chunk in enumerate(chunks):
                filename = chunk.get("filename", "unknown")
                page = chunk.get("page_number", "unknown")
                text = chunk.get("chunk_text", "")
                evidence += f"\n--- Source {idx+1}: {filename} (Page {page}) ---\n{text}\n"

        prompt = prompt_template.format(query=query, evidence=evidence, answer=answer)

        # Fallback values
        llm_score = rule_score
        status = "SUPPORTED" if rule_score > 0.8 else ("PARTIALLY_SUPPORTED" if rule_score >= 0.5 else "UNSUPPORTED")
        reason = "Fallback validation using rule-based scoring (Ollama offline/error)."

        try:
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            parsed = provider.generate_json(prompt)
            llm_score = float(parsed.get("score", rule_score))
            status = str(parsed.get("status", status)).strip().upper()
            reason = str(parsed.get("reason", reason)).strip()
        except Exception as e:
            logger.warning(f"LLM verifier execution failed: {e}. Falling back to rule metrics.")

        return llm_score, status, reason
