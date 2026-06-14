import pytest
from unittest.mock import patch, MagicMock
from app.services.agents.verifier_agent import VerifierAgent

def test_verifier_agent_supported():
    verifier = VerifierAgent()
    
    # Setup state that matches retrieved chunks perfectly
    state = {
        "query": "What is Python?",
        "answer": "Python is a programming language.",
        "route": "retrieval",
        "retrieved_chunks": [
            {"chunk_text": "Python is a programming language."}
        ],
        "citations": [
            {"filename": "test.pdf", "page_number": 1, "snippet": "Python is a programming language."}
        ],
        "verification_attempts": 0,
        "execution_metadata": {}
    }
    
    with patch("requests.post") as mock_post:
        # Mock LLM returning SUPPORTED JSON response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"score": 0.95, "status": "SUPPORTED", "reason": "Ground truth matches evidence."}'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        res = verifier.run(state)
        
        assert res["verified"] is True
        assert res["verification_score"] > 0.80
        assert res["verification_status"] == "SUPPORTED"
        assert res["verification_reason"] == "Ground truth matches evidence."
        assert res["grounding_score"] == 1.0  # Perfect overlap + coverage

def test_verifier_agent_unsupported_fallback():
    verifier = VerifierAgent()
    
    # State with no citations and no word overlap
    state = {
        "query": "What is Python?",
        "answer": "Javascript is a scripting framework.",
        "route": "retrieval",
        "retrieved_chunks": [
            {"chunk_text": "Python is a programming language."}
        ],
        "citations": [],
        "verification_attempts": 0,
        "execution_metadata": {}
    }
    
    with patch("requests.post") as mock_post:
        # Simulate Ollama connection failure (to trigger rule-based fallback)
        mock_post.side_effect = Exception("Ollama connection timed out")

        res = verifier.run(state)
        
        assert res["verified"] is False
        assert res["verification_score"] < 0.50
        assert res["verification_status"] == "UNSUPPORTED"
        assert "Fallback validation" in res["verification_reason"]

def test_verifier_agent_direct_route():
    verifier = VerifierAgent()
    
    # Direct route queries check alignment against the query keywords
    state = {
        "query": "Explain quantum computing simply.",
        "answer": "Quantum computing uses superposition to perform complex math.",
        "route": "direct",
        "retrieved_chunks": [],
        "citations": [],
        "verification_attempts": 0,
        "execution_metadata": {}
    }
    
    with patch("requests.post") as mock_post:
        # Mock Ollama returning custom evaluation
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"score": 0.95, "status": "SUPPORTED", "reason": "Direct query answers check out."}'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        res = verifier.run(state)
        
        assert res["verified"] is True
        assert res["verification_score"] >= 0.80
        assert res["verification_status"] == "SUPPORTED"
