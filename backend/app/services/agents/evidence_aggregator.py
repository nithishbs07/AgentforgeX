import time
import logging
from typing import Dict, Any, List
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)

class EvidenceAggregator:
    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Merges, deduplicates, and ranks retrieved evidence from all sub-questions.
        Updates state with aggregated chunks, citations, and quality score.
        """
        start_time = time.time()
        evidence_package = state.get("evidence_package", {})
        sub_questions_results = evidence_package.get("sub_questions_results", {})

        merged_chunks = []
        merged_entities = []
        merged_relationships = []
        
        # 1. Gather all chunks, entities, and relationships
        for sub_q, res in sub_questions_results.items():
            merged_chunks.extend(res.get("chunks", []))
            merged_entities.extend(res.get("graph_entities", []))
            merged_relationships.extend(res.get("graph_relationships", []))

        # 2. Deduplicate chunks
        # We identify duplicates by chunk_text content (normalized whitespace and lowercase)
        # If there are duplicates, we keep the one with the highest similarity score
        seen_chunks = {}
        for chunk in merged_chunks:
            text = chunk.get("chunk_text", "").strip().lower()
            if not text:
                continue
            
            score = chunk.get("similarity_score", 0.0)
            if text not in seen_chunks or score > seen_chunks[text].get("similarity_score", 0.0):
                seen_chunks[text] = chunk

        deduped_chunks = list(seen_chunks.values())

        # 3. Deduplicate graph entities and relationships
        seen_entities = {}
        for entity in merged_entities:
            name = entity.get("name", "").strip().lower()
            if name and name not in seen_entities:
                seen_entities[name] = entity
        deduped_entities = list(seen_entities.values())

        seen_relationships = {}
        for rel in merged_relationships:
            key = (
                rel.get("source", "").strip().lower(),
                rel.get("type", "").strip().lower(),
                rel.get("target", "").strip().lower()
            )
            if any(key) and key not in seen_relationships:
                seen_relationships[key] = rel
        deduped_relationships = list(seen_relationships.values())

        # 4. Rank deduplicated chunks by similarity score desc
        deduped_chunks.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        # Truncate to top_k to avoid context window overflow (e.g. top 8 chunks overall)
        # Standard RAG uses 5, let's keep up to 8 for deep research to give richer context
        final_chunks = deduped_chunks[:8]

        # 5. Build final citations
        citations = []
        for chunk in final_chunks:
            citations.append({
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "page_number": chunk.get("page_number"),
                "snippet": chunk.get("chunk_text", "")
            })

        # 6. Calculate evidence quality score
        # Formula: average similarity score of deduplicated chunks
        scores = [chunk.get("similarity_score", 0.0) for chunk in final_chunks]
        quality_score = round(sum(scores) / len(scores), 4) if scores else 0.0

        elapsed_sec = time.time() - start_time
        elapsed_ms = int(elapsed_sec * 1000)

        # Update metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["aggregation_time_ms"] = elapsed_ms
        execution_metadata["evidence_count"] = len(final_chunks)

        # Construct updated package
        updated_evidence_package = {
            "sub_questions_results": sub_questions_results,
            "ranked_evidence": final_chunks,
            "evidence_count": len(final_chunks),
            "quality_score": quality_score
        }

        return {
            "retrieved_chunks": final_chunks,
            "citations": citations,
            "graph_entities": deduped_entities,
            "graph_relationships": deduped_relationships,
            "evidence_package": updated_evidence_package,
            "aggregation_latency": elapsed_sec,
            "execution_metadata": execution_metadata
        }
