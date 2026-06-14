import pytest
from unittest.mock import MagicMock
from app.services.agents.adaptive_retriever import AdaptiveRetriever

def test_adaptive_retriever_expansion():
    # Mock ChromaRetriever
    mock_retriever = MagicMock()
    # Mock retrieve to return 10 chunks
    mock_retriever.retrieve.return_value = [
        {"chunk_text": f"Chunk text {i}", "document_id": "doc1", "filename": "test.pdf", "page_number": i, "similarity_score": 0.80}
        for i in range(10)
    ]
    
    adaptive_retriever = AdaptiveRetriever(retriever=mock_retriever)
    
    initial_chunks = [
        {"chunk_text": "Chunk text 0", "document_id": "doc1", "filename": "test.pdf", "page_number": 0, "similarity_score": 0.80},
        {"chunk_text": "Chunk text 1", "document_id": "doc1", "filename": "test.pdf", "page_number": 1, "similarity_score": 0.80}
    ]
    
    state = {
        "query": "Test query",
        "retrieved_chunks": initial_chunks,
        "retrieval_attempts": 1,
        "execution_metadata": {"retriever_time_ms": 10}
    }
    
    res = adaptive_retriever.run(state)
    
    # 2 initial chunks -> top_k = min(2 * 2, 20) = 4
    mock_retriever.retrieve.assert_called_once_with("Test query", top_k=4)
    
    assert res["adaptive_retrieval_used"] is True
    assert res["retrieval_attempts"] == 2
    assert res["initial_retrieved_count"] == 2
    # Chunks are merged safely (duplicates removed). We had 10 new chunks (0 to 9),
    # 2 initial chunks (0 and 1) are duplicates of the first two new chunks,
    # so final count should be 10 unique chunks.
    assert res["final_retrieved_count"] == 10
    assert res["evidence_expansion_factor"] == 5.0  # 10 / 2
    assert len(res["citations"]) == 10
    assert res["confidence_score"] == pytest.approx(0.80)
