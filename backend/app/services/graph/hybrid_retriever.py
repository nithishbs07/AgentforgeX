import time
import logging
from typing import List, Dict, Any
from app.services.retrieval import BaseRetriever
from app.services.graph.graph_retriever import GraphRetriever
from app.services.graph.hybrid_reranker import HybridReranker

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self, vector_retriever: BaseRetriever, graph_retriever: GraphRetriever):
        self.vector_retriever = vector_retriever
        self.graph_retriever = graph_retriever
        self.reranker = HybridReranker()

    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Coordinates hybrid retrieval:
          1. Query vector database (ChromaDB).
          2. Query knowledge graph (Neo4j).
          3. Merge and rerank context chunks to prevent flooding.
          4. Aggregate entity/relationship metadata and compute unified confidence.
        """
        start_time = time.time()
        
        # 1. Vector retrieval
        vector_chunks = []
        try:
            # chroma retriever returns structured chunks
            vector_chunks = self.vector_retriever.retrieve(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"Vector search failed during hybrid retrieval: {e}")
            
        # 2. Graph retrieval
        graph_res = {
            "entities": [],
            "relationships": [],
            "retrieved_chunks": [],
            "confidence": 0.0,
            "hit_count": 0
        }
        try:
            graph_res = self.graph_retriever.retrieve(query, top_k=top_k)
        except Exception as e:
            logger.warning(f"Graph search failed during hybrid retrieval: {e}")

        # 3. Hybrid reranking
        final_chunks = self.reranker.rerank(
            vector_chunks=vector_chunks,
            graph_chunks=graph_res.get("retrieved_chunks", []),
            top_k=top_k
        )

        # 4. Compile unified response metrics
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Unified confidence: average similarity of final chunks
        confidence = 0.0
        if final_chunks:
            confidence = sum(c["similarity_score"] for c in final_chunks) / len(final_chunks)
            
        return {
            "retrieved_chunks": final_chunks,
            "entities": graph_res.get("entities", []),
            "relationships": graph_res.get("relationships", []),
            "confidence": round(confidence, 4),
            "graph_confidence": round(graph_res.get("confidence", 0.0), 4),
            "graph_hit_count": graph_res.get("hit_count", 0),
            "vector_chunks_count": len(vector_chunks),
            "graph_chunks_count": len(graph_res.get("retrieved_chunks", [])),
            "latency_ms": elapsed_ms
        }
