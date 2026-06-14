import pytest
from unittest.mock import MagicMock
from app.services.graph.graph_retriever import GraphRetriever

def test_graph_retriever_query_traversal():
    mock_neo4j = MagicMock()
    mock_neo4j.health_check.return_value = True
    
    # Mock Cypher queries response:
    # 1. Neighbor entities and relations
    mock_neo4j.query_graph.side_effect = [
        [
            {
                "src_name": "TCP", "src_type": "Protocols", "src_conf": 0.95,
                "rel_type": "USES", "rel_conf": 0.92,
                "tgt_name": "Congestion Control", "tgt_type": "Networking Terms", "tgt_conf": 0.95
            }
        ],
        # 2. Source Chunks
        [
            {
                "text": "TCP is a protocol that uses Congestion Control.",
                "doc_id": "doc123",
                "page_num": 1,
                "filename": "tcp.pdf",
                "match_weight": 2
            }
        ]
    ]
    
    retriever = GraphRetriever(mock_neo4j)
    results = retriever.retrieve("Explain how TCP uses Congestion Control", top_k=5)
    
    # Assert traversal results
    assert len(results["entities"]) == 2
    assert results["entities"][0]["name"] in ["TCP", "Congestion Control"]
    assert len(results["relationships"]) == 1
    assert results["relationships"][0]["type"] == "USES"
    
    # Assert retrieved chunks formatting
    assert len(results["retrieved_chunks"]) == 1
    chunk = results["retrieved_chunks"][0]
    assert chunk["chunk_text"] == "TCP is a protocol that uses Congestion Control."
    assert chunk["similarity_score"] > 0.80
    assert chunk["filename"] == "tcp.pdf"
    assert results["hit_count"] == 1
    assert results["confidence"] == 0.95
