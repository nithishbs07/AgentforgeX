import time
import logging
from typing import Dict, Any
from app.services.retrieval import BaseRetriever, ChromaRetriever
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)

class AdaptiveRetriever:
    def __init__(self, retriever: BaseRetriever = None):
        self.retriever = retriever or ChromaRetriever()

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Runs adaptive retrieval: queries the database with expanded top-k,
        merges new evidence safely, and computes expansion factor metrics.
        """
        start_time = time.time()
        query = state.get("query", "")
        initial_chunks = state.get("retrieved_chunks", [])
        
        initial_top_k = len(initial_chunks)
        if initial_top_k == 0:
            initial_top_k = 5  # default baseline if previous search yielded zero

        # Dynamic Top-K Strategy: min(initial_top_k * 2, 20)
        adaptive_top_k = min(initial_top_k * 2, 20)
        
        logger.info(f"AdaptiveRetriever expanding search for '{query}' with top_k={adaptive_top_k}")
        new_chunks = self.retriever.retrieve(query, top_k=adaptive_top_k)
        
        # Merge chunks safely avoiding duplicate text entries
        seen_texts = set()
        merged_chunks = []
        
        for chunk in initial_chunks + new_chunks:
            txt = chunk.get("chunk_text", "").strip()
            if txt and txt not in seen_texts:
                seen_texts.add(txt)
                merged_chunks.append(chunk)

        initial_retrieved_count = initial_top_k
        final_retrieved_count = len(merged_chunks)
        
        # Evidence Expansion Factor calculation
        if initial_retrieved_count > 0:
            evidence_expansion_factor = float(final_retrieved_count / initial_retrieved_count)
        else:
            evidence_expansion_factor = 1.0

        # Extract citations
        citations = []
        for chunk in merged_chunks:
            citations.append({
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "page_number": chunk.get("page_number"),
                "snippet": chunk.get("chunk_text", "")
            })

        # Compute average similarity score for confidence
        scores = [chunk["similarity_score"] for chunk in merged_chunks]
        avg_score = float(sum(scores) / len(scores)) if scores else 0.0
        confidence_score = round(avg_score, 4)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Update execution metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["retriever_time_ms"] = execution_metadata.get("retriever_time_ms", 0) + elapsed_ms
        execution_metadata["adaptive_retrieval_used"] = True
        execution_metadata["retrieval_attempts"] = 2
        execution_metadata["initial_retrieved_count"] = initial_retrieved_count
        execution_metadata["final_retrieved_count"] = final_retrieved_count
        execution_metadata["evidence_expansion_factor"] = round(evidence_expansion_factor, 4)

        return {
            "retrieved_chunks": merged_chunks,
            "citations": citations,
            "confidence_score": confidence_score,
            "adaptive_retrieval_used": True,
            "retrieval_attempts": 2,
            "initial_retrieved_count": initial_retrieved_count,
            "final_retrieved_count": final_retrieved_count,
            "evidence_expansion_factor": round(evidence_expansion_factor, 4),
            "execution_metadata": execution_metadata
        }
