import pytest
from unittest.mock import patch, MagicMock
from app.services.agents.generator_agent import GeneratorAgent

@patch("requests.post")
def test_generator_agent_direct(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Direct answers to questions."}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    agent = GeneratorAgent()
    state = {
        "query": "What is Python?",
        "route": "direct"
    }
    
    res = agent.run(state)
    assert res["answer"] == "Direct answers to questions."
    assert res["execution_metadata"]["retrieval_used"] is False
    assert "generator_time_ms" in res["execution_metadata"]

@patch("requests.post")
def test_generator_agent_retrieval(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Answers derived from document context."}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    agent = GeneratorAgent()
    state = {
        "query": "What is TCP?",
        "route": "retrieval",
        "retrieved_chunks": [
            {
                "chunk_text": "TCP is a core protocol.",
                "filename": "tcp.pdf",
                "page_number": 3
            }
        ]
    }
    
    res = agent.run(state)
    assert res["answer"] == "Answers derived from document context."
    assert "generator_time_ms" in res["execution_metadata"]
