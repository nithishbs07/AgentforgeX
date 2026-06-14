import pytest
from app.services.graph.hybrid_reranker import HybridReranker

def test_hybrid_reranker_deduplication_and_boosting():
    # 1. Chunks from Vector DB (Chroma)
    vector_chunks = [
        {"chunk_text": "TCP is a reliable transport protocol.", "similarity_score": 0.82, "filename": "spec.pdf", "page_number": 1},
        {"chunk_text": "IP handles routing at the network layer.", "similarity_score": 0.78, "filename": "spec.pdf", "page_number": 2}
    ]
    
    # 2. Chunks from Knowledge Graph (Neo4j)
    graph_chunks = [
        {"chunk_text": "TCP is a reliable transport protocol.", "similarity_score": 0.80, "filename": "spec.pdf", "page_number": 1}, # Overlapping chunk
        {"chunk_text": "AIMD is an increase/decrease algorithm.", "similarity_score": 0.85, "filename": "spec.pdf", "page_number": 3}
    ]
    
    reranker = HybridReranker()
    final_chunks = reranker.rerank(vector_chunks, graph_chunks, top_k=2)
    
    # Check that duplication was handled and size limited to top_k=2
    assert len(final_chunks) == 2
    
    # TCP chunk was present in both, check if it got a score boost: max(0.82, 0.80) + 0.15 = 0.97
    tcp_chunk = next(c for c in final_chunks if "tcp" in c["chunk_text"].lower())
    assert tcp_chunk["similarity_score"] == 0.97
    assert tcp_chunk["retrieved_via_vector"] is True
    assert tcp_chunk["retrieved_via_graph"] is True
    
    # Check sorting order: TCP (0.97) should be first, AIMD (0.85) second
    assert "tcp" in final_chunks[0]["chunk_text"].lower()
    assert "aimd" in final_chunks[1]["chunk_text"].lower()
