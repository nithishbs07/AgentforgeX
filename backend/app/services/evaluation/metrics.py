import logging
import re
import requests
import json
from typing import List, Dict, Any
from app.core.config import settings
from app.services.embedding_service import is_ollama_online

logger = logging.getLogger(__name__)

class RAGEvaluator:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL

    def _call_ollama_json(self, prompt: str) -> Dict[str, Any]:
        """
        Calls the LLM provider asking for a JSON response.
        """
        try:
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            return provider.generate_json(prompt)
        except Exception as e:
            logger.warning(f"LLM metric evaluation failed: {e}")
            return {}

    def calculate_faithfulness(self, answer: str, context_chunks: List[Dict[str, Any]]) -> float:
        """
        Evaluates whether the generated answer only contains information supported by the retrieved chunks.
        """
        if not answer:
            return 0.0
        if not context_chunks:
            return 0.0

        context_str = "\n".join([c.get("chunk_text", "") for c in context_chunks])

        prompt = f"""
        Analyze the generated answer and the context provided below.
        Evaluate if each statement in the answer is fully supported by the context.
        Return a JSON object with a single key "score" between 0.0 and 1.0 (where 1.0 means all statements in the answer are supported by the context, and 0.0 means none are supported).

        Context:
        {context_str}

        Answer:
        {answer}

        JSON Output format:
        {{
          "score": 0.85
        }}
        """
        res = self._call_ollama_json(prompt)
        if "score" in res:
            try:
                return max(0.0, min(1.0, float(res["score"])))
            except (ValueError, TypeError):
                pass

        # Fallback: Rule-based keyword/entity overlap check
        def get_words(text: str) -> set:
            return set(re.findall(r"\w{4,}", text.lower()))

        words_answer = get_words(answer)
        words_context = get_words(context_str)

        if not words_answer:
            return 1.0

        overlap = words_answer.intersection(words_context)
        score = len(overlap) / len(words_answer)
        return round(max(0.0, min(1.0, score)), 4)

    def calculate_answer_relevancy(self, query: str, answer: str) -> float:
        """
        Evaluates how relevant the generated answer is to the user query.
        """
        if not query or not answer:
            return 0.0

        prompt = f"""
        Analyze the user query and the generated answer.
        Evaluate if the answer directly and fully addresses the query.
        Return a JSON object with a single key "score" between 0.0 and 1.0 (where 1.0 means the answer perfectly addresses the query, and 0.0 means it is completely irrelevant).

        Query: {query}
        Answer: {answer}

        JSON Output format:
        {{
          "score": 0.9
        }}
        """
        res = self._call_ollama_json(prompt)
        if "score" in res:
            try:
                return max(0.0, min(1.0, float(res["score"])))
            except (ValueError, TypeError):
                pass

        # Fallback: Word overlap between query and answer
        def get_words(text: str) -> set:
            return set(re.findall(r"\w{3,}", text.lower()))

        words_query = get_words(query)
        words_answer = get_words(answer)

        if not words_query:
            return 1.0

        overlap = words_query.intersection(words_answer)
        score = len(overlap) / len(words_query)
        return round(max(0.0, min(1.0, score)), 4)

    def calculate_context_precision(self, query: str, context_chunks: List[Dict[str, Any]]) -> float:
        """
        Evaluates whether retrieved chunks relevant to the query are ranked higher.
        Precision = (True Positives at k) / k. Average Precision is computed across all chunks.
        """
        if not query or not context_chunks:
            return 0.0

        # We need to determine if each chunk is relevant.
        # If Ollama is online, we can score relevance.
        # Otherwise we use keyword overlap as a heuristic.
        relevance_vector = []
        for chunk in context_chunks:
            chunk_text = chunk.get("chunk_text", "")
            
            # Use quick rule-based check first or if offline
            def is_relevant_heuristic(q: str, c: str) -> bool:
                q_words = set(re.findall(r"\w{4,}", q.lower()))
                if not q_words:
                    return True
                c_words = set(re.findall(r"\w{4,}", c.lower()))
                overlap = q_words.intersection(c_words)
                # If at least 15% of query words are in the chunk, we consider it relevant
                return (len(overlap) / len(q_words)) >= 0.15

            is_rel = is_relevant_heuristic(query, chunk_text)
            relevance_vector.append(1 if is_rel else 0)

        # Compute Average Precision (AP)
        ap = 0.0
        relevant_count = 0
        for idx, rel in enumerate(relevance_vector):
            if rel == 1:
                relevant_count += 1
                precision_at_k = relevant_count / (idx + 1)
                ap += precision_at_k

        if relevant_count == 0:
            return 0.0

        return round(ap / len(context_chunks), 4)

    def calculate_context_recall(self, query: str, context_chunks: List[Dict[str, Any]]) -> float:
        """
        Evaluates if the retrieved context chunks cover all necessary info to answer the query.
        """
        if not query:
            return 1.0
        if not context_chunks:
            return 0.0

        context_str = "\n".join([c.get("chunk_text", "") for c in context_chunks])

        prompt = f"""
        Analyze the user query and the retrieved context.
        Evaluate if all information needed to answer the query is present in the context.
        Return a JSON object with a key "score" between 0.0 and 1.0 (where 1.0 means all needed facts are present, and 0.0 means none are present).

        Query: {query}
        Context: {context_str}

        JSON Output format:
        {{
          "score": 0.8
        }}
        """
        res = self._call_ollama_json(prompt)
        if "score" in res:
            try:
                return max(0.0, min(1.0, float(res["score"])))
            except (ValueError, TypeError):
                pass

        # Fallback: Query keyword coverage check in the context
        q_words = set(re.findall(r"\w{4,}", query.lower()))
        if not q_words:
            return 1.0

        c_words = set(re.findall(r"\w{4,}", context_str.lower()))
        overlap = q_words.intersection(c_words)
        score = len(overlap) / len(q_words)
        return round(max(0.0, min(1.0, score)), 4)

    def calculate_grounding_score(self, answer: str, context_chunks: List[Dict[str, Any]], query: str = None, route: str = "retrieval") -> float:
        """
        Calculates rule-based grounding score (overlap * 0.5) + (coverage * 0.5)
        """
        if not answer:
            return 0.0
            
        def get_keywords(text: str) -> set:
            stop_words = {"the", "a", "is", "of", "and", "in", "to", "it", "that", "on", "for", "with", "as", "at", "by", "an", "be", "this", "are"}
            words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
            return {w for w in words if w not in stop_words and len(w) > 2}

        words_answer = get_keywords(answer)
        
        if route == "direct":
            if not query:
                return 1.0
            words_query = get_keywords(query)
            if words_query and words_answer:
                keyword_overlap = len(words_answer.intersection(words_query)) / len(words_query)
            else:
                keyword_overlap = 0.5
            evidence_coverage = 1.0
        else:
            words_chunks = set()
            for chunk in context_chunks:
                words_chunks.update(get_keywords(chunk.get("chunk_text", "")))

            if words_answer:
                keyword_overlap = len(words_answer.intersection(words_chunks)) / len(words_answer)
            else:
                keyword_overlap = 0.0

            sentences = [s.strip() for s in answer.split(".") if s.strip()]
            covered = 0
            for s in sentences:
                s_words = get_keywords(s)
                if not s_words:
                    covered += 1
                elif words_chunks and len(s_words.intersection(words_chunks)) / len(s_words) >= 0.2:
                    covered += 1
            evidence_coverage = covered / len(sentences) if sentences else 0.0

        score = (keyword_overlap * 0.5) + (evidence_coverage * 0.5)
        return round(max(0.0, min(1.0, score)), 4)

    def calculate_verification_score(self, query: str, answer: str, context_chunks: List[Dict[str, Any]], route: str = "retrieval") -> float:
        """
        Calculates a combined verification score: (rule_score * 0.4) + (llm_score * 0.6)
        """
        if not answer:
            return 0.0
            
        # 1. Compute rule score
        def get_keywords(text: str) -> set:
            stop_words = {"the", "a", "is", "of", "and", "in", "to", "it", "that", "on", "for", "with", "as", "at", "by", "an", "be", "this", "are"}
            words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
            return {w for w in words if w not in stop_words and len(w) > 2}

        words_answer = get_keywords(answer)
        
        if route == "direct":
            if query:
                words_query = get_keywords(query)
                if words_query and words_answer:
                    keyword_overlap = len(words_answer.intersection(words_query)) / len(words_query)
                else:
                    keyword_overlap = 0.5
            else:
                keyword_overlap = 0.5
            citation_presence = 1.0
            evidence_coverage = 1.0
        else:
            words_chunks = set()
            for chunk in context_chunks:
                words_chunks.update(get_keywords(chunk.get("chunk_text", "")))

            if words_answer:
                keyword_overlap = len(words_answer.intersection(words_chunks)) / len(words_answer)
            else:
                keyword_overlap = 0.0

            citation_presence = 1.0 if context_chunks else 0.0

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

        # 2. Compute LLM score
        context_str = "\n".join([c.get("chunk_text", "") for c in context_chunks])
        prompt = f"""
        Determine whether the generated answer is supported by the provided context.
        Return a JSON object with a single key "score" between 0.0 and 1.0.

        Query: {query}
        Context: {context_str}
        Answer: {answer}

        JSON Output format:
        {{
          "score": 0.85
        }}
        """
        res = self._call_ollama_json(prompt)
        llm_score = rule_score
        if "score" in res:
            try:
                llm_score = max(0.0, min(1.0, float(res["score"])))
            except (ValueError, TypeError):
                pass

        score = (rule_score * 0.4) + (llm_score * 0.6)
        return round(max(0.0, min(1.0, score)), 4)

    def calculate_retrieval_quality(self, query: str, context_chunks: List[Dict[str, Any]]) -> float:
        """
        Calculates retrieval quality (average of context precision and context recall)
        """
        precision = self.calculate_context_precision(query, context_chunks)
        recall = self.calculate_context_recall(query, context_chunks)
        return round((precision + recall) / 2.0, 4)

    def calculate_research_quality(self, query: str, answer: str, context_chunks: List[Dict[str, Any]]) -> float:
        """
        Calculates research quality (average of faithfulness and answer relevancy)
        """
        faithfulness = self.calculate_faithfulness(answer, context_chunks)
        relevancy = self.calculate_answer_relevancy(query, answer)
        return round((faithfulness + relevancy) / 2.0, 4)
