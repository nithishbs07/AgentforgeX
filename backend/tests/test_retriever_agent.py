import pytest
from unittest.mock import MagicMock
from app.services.agents.retriever_agent import RetrieverAgent

def test_retriever_agent_run():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        {
            "chunk_text": "Sample text chunk.",
            "document_id": "doc_id_123",
            "filename": "test.pdf",
            "page_number": 1,
            "similarity_score": 0.92
        }
    ]

    agent = RetrieverAgent(retriever=mock_retriever)
    state = {"query": "test query"}
    res = agent.run(state)

    assert len(res["retrieved_chunks"]) == 1
    assert res["citations"][0]["document_id"] == "doc_id_123"
    assert res["citations"][0]["snippet"] == "Sample text chunk."
    assert res["confidence_score"] == 0.92
    assert res["execution_metadata"]["retrieval_used"] is True
    assert "retriever_time_ms" in res["execution_metadata"]
