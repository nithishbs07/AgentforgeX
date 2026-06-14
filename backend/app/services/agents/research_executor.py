import time
import logging
from typing import Dict, Any, List
from app.services.retrieval import BaseRetriever, ChromaRetriever
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.graph_retriever import GraphRetriever
from app.services.graph.hybrid_retriever import HybridRetriever as ActualHybridRetriever
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)

class ResearchExecutor:
    def __init__(self, retriever: BaseRetriever = None):
        self.vector_retriever = retriever or ChromaRetriever()
        self.neo4j_service = Neo4jService()
        self.graph_retriever = GraphRetriever(self.neo4j_service)
        self.hybrid_retriever = ActualHybridRetriever(self.vector_retriever, self.graph_retriever)

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes query retrieval for each sub-question using vector, graph, or hybrid search.
        """
        start_time = time.time()
        sub_questions = state.get("sub_questions", [])
        retrieval_modes = state.get("retrieval_modes", [])

        # If sub_questions is empty, use the main query
        if not sub_questions:
            sub_questions = [state.get("query", "")]
            retrieval_modes = ["vector"]

        neo4j_online = self.neo4j_service.health_check()
        sub_questions_results = {}

        # Observability counters
        total_graph_queries = 0
        total_hybrid_queries = 0
        total_graph_hits = 0
        total_chunks_retrieved = 0

        for i, sub_q in enumerate(sub_questions):
            # Select retrieval mode, default to vector
            mode = retrieval_modes[i] if i < len(retrieval_modes) else "vector"
            if mode not in ["vector", "graph", "hybrid"]:
                mode = "vector"

            # Graceful fallback to Vector if Neo4j is offline
            actual_mode = mode
            if (mode == "graph" or mode == "hybrid") and not neo4j_online:
                logger.warning(f"Neo4j is offline. Falling back from '{mode}' to 'vector' for sub-question: '{sub_q}'")
                actual_mode = "vector"

            retrieved_chunks = []
            graph_entities = []
            graph_relationships = []
            graph_confidence = 0.0
            graph_hit_count = 0
            hybrid_used = False

            if actual_mode == "graph":
                total_graph_queries += 1
                graph_res = self.graph_retriever.retrieve(sub_q, top_k=5)
                retrieved_chunks = graph_res.get("retrieved_chunks", [])
                graph_entities = graph_res.get("entities", [])
                graph_relationships = graph_res.get("relationships", [])
                graph_confidence = graph_res.get("confidence", 0.0)
                graph_hit_count = graph_res.get("hit_count", 0)
                total_graph_hits += graph_hit_count

            elif actual_mode == "hybrid":
                total_hybrid_queries += 1
                hybrid_res = self.hybrid_retriever.retrieve(sub_q, top_k=5)
                retrieved_chunks = hybrid_res.get("retrieved_chunks", [])
                graph_entities = hybrid_res.get("entities", [])
                graph_relationships = hybrid_res.get("relationships", [])
                graph_confidence = hybrid_res.get("graph_confidence", 0.0)
                graph_hit_count = hybrid_res.get("graph_hit_count", 0)
                hybrid_used = True
                total_graph_hits += graph_hit_count

            else:  # vector RAG
                retrieved_chunks = self.vector_retriever.retrieve(sub_q, top_k=5)

            total_chunks_retrieved += len(retrieved_chunks)

            # Map citations
            citations = []
            for chunk in retrieved_chunks:
                citations.append({
                    "document_id": chunk.get("document_id"),
                    "filename": chunk.get("filename"),
                    "page_number": chunk.get("page_number"),
                    "snippet": chunk.get("chunk_text", "")
                })

            # Calculate confidence score for the sub-question
            scores = [chunk.get("similarity_score", 0.0) for chunk in retrieved_chunks]
            avg_score = float(sum(scores) / len(scores)) if scores else 0.0
            confidence = round(avg_score, 4)

            # Store result
            sub_questions_results[sub_q] = {
                "chunks": retrieved_chunks,
                "graph_entities": graph_entities,
                "graph_relationships": graph_relationships,
                "citations": citations,
                "confidence": confidence,
                "mode": mode,
                "actual_mode": actual_mode,
                "graph_hit_count": graph_hit_count,
                "hybrid_used": hybrid_used
            }

        elapsed_sec = time.time() - start_time
        elapsed_ms = int(elapsed_sec * 1000)

        # Update metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["retriever_time_ms"] = elapsed_ms
        execution_metadata["retrieval_used"] = True
        execution_metadata["graph_queries"] = execution_metadata.get("graph_queries", 0) + total_graph_queries
        execution_metadata["graph_hits"] = execution_metadata.get("graph_hits", 0) + total_graph_hits
        execution_metadata["hybrid_queries"] = execution_metadata.get("hybrid_queries", 0) + total_hybrid_queries
        execution_metadata["evidence_count"] = total_chunks_retrieved

        # Retrieve Neo4j overall growth stats for observability
        entity_count = 0
        relationship_count = 0
        if neo4j_online:
            try:
                e_res = self.neo4j_service.query_graph("MATCH (n:Entity) RETURN count(n) AS count")
                entity_count = e_res[0]["count"] if e_res else 0
                r_res = self.neo4j_service.query_graph("MATCH ()-[r]->() WHERE NOT type(r) IN ['CONTAINS', 'HAS_PAGE', 'HAS_CHUNK', 'MENTIONS'] RETURN count(r) AS count")
                relationship_count = r_res[0]["count"] if r_res else 0
            except Exception:
                pass
        execution_metadata["entity_count"] = entity_count
        execution_metadata["relationship_count"] = relationship_count

        evidence_package = {
            "sub_questions_results": sub_questions_results,
            "total_chunks_retrieved": total_chunks_retrieved
        }

        return {
            "evidence_package": evidence_package,
            "research_latency": elapsed_sec,
            "execution_metadata": execution_metadata
        }
