import pytest
from unittest.mock import MagicMock
from app.services.graph.hybrid_retriever import HybridRetriever

def test_hybrid_retriever_query_coordination():
    # Mock vector retriever
    mock_vector = MagicMock()
    mock_vector.retrieve.return_value = [
        {
            "chunk_text": "Vector chunk text.",
            "similarity_score": 0.85,
            "document_id": "doc1",
            "filename": "doc.pdf",
            "page_number": 1
        }
    ]
    
    # Mock graph retriever
    mock_graph = MagicMock()
    mock_graph.retrieve.return_value = {
        "entities": [{"name": "TCP", "type": "Protocols", "confidence": 0.95}],
        "relationships": [{"source": "TCP", "type": "USES", "target": "Congestion Control"}],
        "retrieved_chunks": [
            {
                "chunk_text": "Graph chunk text.",
                "similarity_score": 0.80,
                "document_id": "doc1",
                "page_number": 2,
                "filename": "doc.pdf"
            }
        ],
        "confidence": 0.95,
        "hit_count": 1
    }
    
    retriever = HybridRetriever(mock_vector, mock_graph)
    results = retriever.retrieve("Explain TCP in context", top_k=5)
    
    # Check that both retrievers were called
    mock_vector.retrieve.assert_called_once()
    mock_graph.retrieve.assert_called_once()
    
    # Assert merged response metrics
    assert len(results["retrieved_chunks"]) == 2
    assert len(results["entities"]) == 1
    assert results["entities"][0]["name"] == "TCP"
    assert len(results["relationships"]) == 1
    
    assert results["vector_chunks_count"] == 1
    assert results["graph_chunks_count"] == 1
    assert results["graph_confidence"] == 0.95
    assert results["graph_hit_count"] == 1
    assert results["confidence"] > 0.80
