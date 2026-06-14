import time
import logging
from typing import Dict, Any
from app.services.retrieval import BaseRetriever, ChromaRetriever
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.graph_retriever import GraphRetriever
from app.services.graph.hybrid_retriever import HybridRetriever as ActualHybridRetriever
from app.services.agents.state import AgentState

logger = logging.getLogger(__name__)

class RetrieverAgent:
    def __init__(self, retriever: BaseRetriever = None):
        self.vector_retriever = retriever or ChromaRetriever()
        self.neo4j_service = Neo4jService()
        self.graph_retriever = GraphRetriever(self.neo4j_service)
        self.hybrid_retriever = ActualHybridRetriever(self.vector_retriever, self.graph_retriever)

    def run(self, state: AgentState) -> Dict[str, Any]:
        """
        Executes query retrieval based on target route (VECTOR, GRAPH, HYBRID).
        Automatically falls back to VECTOR if Neo4j is offline.
        """
        start_time = time.time()
        query = state.get("query", "")
        route = state.get("route", "vector")
        
        # Normalize legacy routing
        if route == "retrieval":
            route = "vector"
            
        retrieval_mode = route
        neo4j_online = self.neo4j_service.health_check()
        
        # Graceful fallback to Vector Retrieval if Neo4j is unavailable
        if (route == "graph" or route == "hybrid") and not neo4j_online:
            logger.warning(f"Neo4j is offline/unavailable. Falling back from '{route}' route to 'vector'.")
            retrieval_mode = "vector"

        retrieved_chunks = []
        graph_entities = []
        graph_relationships = []
        graph_results = []
        graph_confidence = 0.0
        graph_hit_count = 0
        hybrid_used = False
        
        graph_retrieval_latency = 0
        hybrid_retrieval_latency = 0

        logger.info(f"RetrieverAgent executing retrieval mode '{retrieval_mode}' for query: {query}")

        # 1. Route dispatch
        if retrieval_mode == "graph":
            t0 = time.time()
            graph_res = self.graph_retriever.retrieve(query, top_k=5)
            graph_retrieval_latency = int((time.time() - t0) * 1000)
            
            retrieved_chunks = graph_res.get("retrieved_chunks", [])
            graph_entities = graph_res.get("entities", [])
            graph_relationships = graph_res.get("relationships", [])
            graph_confidence = graph_res.get("confidence", 0.0)
            graph_hit_count = graph_res.get("hit_count", 0)
            
        elif retrieval_mode == "hybrid":
            t0 = time.time()
            hybrid_res = self.hybrid_retriever.retrieve(query, top_k=5)
            hybrid_retrieval_latency = int((time.time() - t0) * 1000)
            
            retrieved_chunks = hybrid_res.get("retrieved_chunks", [])
            graph_entities = hybrid_res.get("entities", [])
            graph_relationships = hybrid_res.get("relationships", [])
            graph_confidence = hybrid_res.get("graph_confidence", 0.0)
            graph_hit_count = hybrid_res.get("graph_hit_count", 0)
            hybrid_used = True
            
        else: # vector RAG
            retrieved_chunks = self.vector_retriever.retrieve(query, top_k=5)

        # 2. Extract citations
        citations = []
        for chunk in retrieved_chunks:
            citations.append({
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "page_number": chunk.get("page_number"),
                "snippet": chunk.get("chunk_text", "")
            })

        # 3. Compute RAG confidence score
        scores = [chunk.get("similarity_score", 0.0) for chunk in retrieved_chunks]
        avg_score = float(sum(scores) / len(scores)) if scores else 0.0
        confidence_score = round(avg_score, 4)

        elapsed_ms = int((time.time() - start_time) * 1000)
        initial_count = len(retrieved_chunks)

        # 4. Observability totals
        entity_count = 0
        relationship_count = 0
        if neo4j_online:
            try:
                # Count nodes
                e_res = self.neo4j_service.query_graph("MATCH (n:Entity) RETURN count(n) AS count")
                entity_count = e_res[0]["count"] if e_res else 0
                
                # Count semantic relations (excluding structural document pages/chunks linking)
                r_res = self.neo4j_service.query_graph("MATCH ()-[r]->() WHERE NOT type(r) IN ['CONTAINS', 'HAS_PAGE', 'HAS_CHUNK', 'MENTIONS'] RETURN count(r) AS count")
                relationship_count = r_res[0]["count"] if r_res else 0
            except Exception:
                pass

        # 5. Populate and extend execution metadata
        execution_metadata = dict(state.get("execution_metadata", {}))
        execution_metadata["retriever_time_ms"] = elapsed_ms
        execution_metadata["retrieval_used"] = True
        
        # Knowledge Graph observability
        execution_metadata["retrieval_mode"] = retrieval_mode
        execution_metadata["graph_queries"] = 1 if retrieval_mode == "graph" else 0
        execution_metadata["graph_hits"] = graph_hit_count
        execution_metadata["hybrid_queries"] = 1 if retrieval_mode == "hybrid" else 0
        execution_metadata["entity_count"] = entity_count
        execution_metadata["relationship_count"] = relationship_count
        execution_metadata["graph_retrieval_latency"] = graph_retrieval_latency
        execution_metadata["hybrid_retrieval_latency"] = hybrid_retrieval_latency
        
        # Verifier fallbacks default to null
        execution_metadata["graph_verification_score"] = 0.0
        execution_metadata["hybrid_verification_score"] = 0.0
        execution_metadata["graph_grounding_score"] = 0.0
        execution_metadata["hybrid_grounding_score"] = 0.0

        return {
            "retrieved_chunks": retrieved_chunks,
            "citations": citations,
            "confidence_score": confidence_score,
            "retrieval_mode": retrieval_mode,
            "graph_entities": graph_entities,
            "graph_relationships": graph_relationships,
            "graph_results": graph_results,
            "hybrid_used": hybrid_used,
            "graph_confidence": graph_confidence,
            "graph_hit_count": graph_hit_count,
            "execution_metadata": execution_metadata
        }
