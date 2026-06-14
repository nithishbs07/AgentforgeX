import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class HybridReranker:
    @staticmethod
    def rerank(
        vector_chunks: List[Dict[str, Any]], 
        graph_chunks: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Deduplicates, scores, and reranks combined vector and graph chunks.
        Applies a boost if a chunk is returned by BOTH Vector and Graph retrievers.
        Crops output size to top_k to prevent prompt context flooding.
        """
        merged_chunks = {}
        
        # 1. Process Vector Chunks
        for idx, chunk in enumerate(vector_chunks):
            text = chunk["chunk_text"]
            key = text[:120].strip().lower() # Deduping key
            
            merged_chunks[key] = {
                "chunk_text": text,
                "similarity_score": chunk.get("similarity_score", 0.70),
                "document_id": chunk.get("document_id"),
                "page_number": chunk.get("page_number", 1),
                "filename": chunk.get("filename", "unknown.pdf"),
                "retrieved_via_vector": True,
                "retrieved_via_graph": False
            }

        # 2. Process Graph Chunks
        for chunk in graph_chunks:
            text = chunk["chunk_text"]
            key = text[:120].strip().lower()
            
            if key in merged_chunks:
                # Chunk exists in both vector and graph! Boost score and toggle flag
                existing = merged_chunks[key]
                existing["retrieved_via_graph"] = True
                
                v_score = existing["similarity_score"]
                g_score = chunk.get("similarity_score", 0.70)
                
                # Formula: Max score + 15% boost for reciprocal hit
                boosted_score = min(max(v_score, g_score) + 0.15, 1.0)
                existing["similarity_score"] = round(boosted_score, 4)
            else:
                # Only found in graph
                merged_chunks[key] = {
                    "chunk_text": text,
                    "similarity_score": chunk.get("similarity_score", 0.70),
                    "document_id": chunk.get("document_id"),
                    "page_number": chunk.get("page_number", 1),
                    "filename": chunk.get("filename", "unknown.pdf"),
                    "retrieved_via_vector": False,
                    "retrieved_via_graph": True
                }

        # 3. Sort by similarity score descending
        reranked = list(merged_chunks.values())
        reranked.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # 4. Limit to top_k to prevent context flooding
        final_list = reranked[:top_k]
        
        logger.info(f"Hybrid Reranker: merged {len(vector_chunks)} vector & {len(graph_chunks)} graph chunks down to {len(final_list)} output chunks (top_k={top_k})")
        return final_list
