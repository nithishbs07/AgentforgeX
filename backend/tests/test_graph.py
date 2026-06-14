import pytest
from unittest.mock import MagicMock
from app.services.agents.graph import create_agent_graph
from langgraph.graph import END

def test_graph_direct_path():
    mock_router = MagicMock()
    mock_router.run.return_value = {
        "route": "direct",
        "route_confidence": 0.95,
        "execution_metadata": {"selected_route": "direct", "route_confidence": 0.95}
    }
    
    mock_retriever = MagicMock()
    mock_retriever.run.return_value = {}  # Should NOT be called
    
    mock_generator = MagicMock()
    mock_generator.run.return_value = {
        "answer": "Direct answer output.",
        "verification_attempts": 0,
        "execution_metadata": {"selected_route": "direct", "route_confidence": 0.95, "generator_time_ms": 10, "retrieval_used": False}
    }

    mock_verifier = MagicMock()
    mock_verifier.run.return_value = {
        "verification_score": 0.90,
        "grounding_score": 0.85,
        "verification_status": "SUPPORTED",
        "verification_reason": "Correct direct response.",
        "verified": True,
        "adaptive_retrieval_reason": "",
        "execution_metadata": {"selected_route": "direct", "verifier_time_ms": 5, "verification_score": 0.90}
    }

    mock_adaptive_retriever = MagicMock()

    graph = create_agent_graph(
        router=mock_router,
        retriever=mock_retriever,
        generator=mock_generator,
        verifier=mock_verifier,
        adaptive_retriever=mock_adaptive_retriever
    )
    
    initial_state = {
        "query": "What is Python?",
        "session_id": "session_123",
        "route": "direct",
        "route_confidence": 0.0,
        "retrieved_chunks": [],
        "citations": [],
        "answer": "",
        "confidence_score": 0.0,
        "verification_score": 0.0,
        "grounding_score": 0.0,
        "verification_status": "UNSUPPORTED",
        "verification_attempts": 0,
        "adaptive_retrieval_used": False,
        "retrieval_attempts": 1,
        "execution_metadata": {}
    }
    
    final_state = graph.invoke(initial_state)

    assert final_state["route"] == "direct"
    assert final_state["answer"] == "Direct answer output."
    assert final_state["verification_score"] == 0.90
    assert final_state["verification_status"] == "SUPPORTED"
    
    # Assert retriever and adaptive retriever were bypassed
    mock_retriever.run.assert_not_called()
    mock_adaptive_retriever.run.assert_not_called()
    mock_router.run.assert_called_once()
    mock_generator.run.assert_called_once()
    mock_verifier.run.assert_called_once()

def test_graph_retrieval_path():
    mock_router = MagicMock()
    mock_router.run.return_value = {
        "route": "retrieval",
        "route_confidence": 0.88,
        "execution_metadata": {"selected_route": "retrieval", "route_confidence": 0.88}
    }
    
    mock_retriever = MagicMock()
    mock_retriever.run.return_value = {
        "retrieved_chunks": [{"chunk_text": "TCP header details...", "similarity_score": 0.90}],
        "citations": [{"filename": "doc.pdf", "page_number": 2, "snippet": "TCP header details..."}],
        "confidence_score": 0.90,
        "execution_metadata": {"selected_route": "retrieval", "route_confidence": 0.88, "retriever_time_ms": 15, "retrieval_used": True}
    }
    
    mock_generator = MagicMock()
    mock_generator.run.return_value = {
        "answer": "Answer based on TCP header.",
        "verification_attempts": 0,
        "execution_metadata": {"selected_route": "retrieval", "route_confidence": 0.88, "retriever_time_ms": 15, "generator_time_ms": 25, "retrieval_used": True}
    }

    mock_verifier = MagicMock()
    mock_verifier.run.return_value = {
        "verification_score": 0.85,
        "grounding_score": 0.80,
        "verification_status": "SUPPORTED",
        "verification_reason": "Answer matches chunks.",
        "verified": True,
        "adaptive_retrieval_reason": "",
        "execution_metadata": {
            "selected_route": "retrieval",
            "verifier_time_ms": 8,
            "verification_score": 0.85,
            "retriever_time_ms": 15,
            "generator_time_ms": 25,
            "retrieval_used": True
        }
    }

    mock_adaptive_retriever = MagicMock()

    graph = create_agent_graph(
        router=mock_router,
        retriever=mock_retriever,
        generator=mock_generator,
        verifier=mock_verifier,
        adaptive_retriever=mock_adaptive_retriever
    )
    
    initial_state = {
        "query": "What does PDF say about TCP?",
        "session_id": "session_123",
        "route": "direct",
        "route_confidence": 0.0,
        "retrieved_chunks": [],
        "citations": [],
        "answer": "",
        "confidence_score": 0.0,
        "verification_score": 0.0,
        "grounding_score": 0.0,
        "verification_status": "UNSUPPORTED",
        "verification_attempts": 0,
        "adaptive_retrieval_used": False,
        "retrieval_attempts": 1,
        "execution_metadata": {}
    }
    
    final_state = graph.invoke(initial_state)

    assert final_state["route"] == "retrieval"
    assert final_state["answer"] == "Answer based on TCP header."
    assert final_state["confidence_score"] == 0.90
    assert final_state["verification_score"] == 0.85
    assert len(final_state["citations"]) == 1
    assert final_state["execution_metadata"]["retrieval_used"] is True
    
    # Assert retriever was called, adaptive retriever bypassed
    mock_retriever.run.assert_called_once()
    mock_adaptive_retriever.run.assert_not_called()
    mock_router.run.assert_called_once()
    mock_generator.run.assert_called_once()
    mock_verifier.run.assert_called_once()

def test_graph_adaptive_retrieval_loop():
    mock_router = MagicMock()
    mock_router.run.return_value = {
        "route": "retrieval",
        "route_confidence": 0.90,
        "execution_metadata": {"selected_route": "retrieval"}
    }
    
    mock_retriever = MagicMock()
    mock_retriever.run.return_value = {
        "retrieved_chunks": [{"chunk_text": "Initial context text"}],
        "citations": [],
        "confidence_score": 0.50,
        "adaptive_retrieval_used": False,
        "retrieval_attempts": 1
    }
    
    # Mock generator returning different values on subsequent runs
    mock_generator = MagicMock()
    mock_generator.run.side_effect = [
        # First Run: returns weak answer
        {
            "answer": "Weak answer",
            "verification_attempts": 0,
            "execution_metadata": {"generator_time_ms": 10}
        },
        # Second Run: returns regenerated/stronger answer
        {
            "answer": "Regenerated strong answer",
            "verification_attempts": 1,
            "execution_metadata": {"generator_time_ms": 15, "regenerated": True}
        }
    ]

    # Mock verifier returning failing score first time (with trigger reason), passing score second time
    mock_verifier = MagicMock()
    mock_verifier.run.side_effect = [
        # First Run: score is 0.40 (failing, triggers adaptive retrieval)
        {
            "verification_score": 0.40,
            "grounding_score": 0.30,
            "verification_status": "UNSUPPORTED",
            "verification_reason": "Low overlap",
            "verified": False,
            "adaptive_retrieval_reason": "Low Verification Score",
            "verification_score_before_adaptation": 0.40,
            "execution_metadata": {"verification_score": 0.40, "adaptive_retrieval_reason": "Low Verification Score"}
        },
        # Second Run: score is 0.85 (passing)
        {
            "verification_score": 0.85,
            "grounding_score": 0.80,
            "verification_status": "SUPPORTED",
            "verification_reason": "Regenerated answer has high overlap",
            "verified": True,
            "adaptive_retrieval_reason": "Low Verification Score",
            "verification_score_before_adaptation": 0.40,
            "verification_score_after_adaptation": 0.85,
            "verification_improvement": 0.45,
            "execution_metadata": {
                "verification_score": 0.85,
                "regenerated": True,
                "adaptive_retrieval_used": True,
                "retrieval_attempts": 2,
                "verification_improvement": 0.45
            }
        }
    ]

    # Mock adaptive retriever expanding top_k and updating count metrics
    mock_adaptive_retriever = MagicMock()
    mock_adaptive_retriever.run.return_value = {
        "retrieved_chunks": [{"chunk_text": "Initial context text"}, {"chunk_text": "Expanded context text"}],
        "citations": [],
        "confidence_score": 0.65,
        "adaptive_retrieval_used": True,
        "retrieval_attempts": 2,
        "initial_retrieved_count": 1,
        "final_retrieved_count": 2,
        "evidence_expansion_factor": 2.0,
        "execution_metadata": {
            "adaptive_retrieval_used": True,
            "retrieval_attempts": 2,
            "initial_retrieved_count": 1,
            "final_retrieved_count": 2,
            "evidence_expansion_factor": 2.0
        }
    }

    graph = create_agent_graph(
        router=mock_router,
        retriever=mock_retriever,
        generator=mock_generator,
        verifier=mock_verifier,
        adaptive_retriever=mock_adaptive_retriever
    )
    
    initial_state = {
        "query": "Verify adaptive retrieval loop",
        "session_id": "session_456",
        "route": "direct",
        "route_confidence": 0.0,
        "retrieved_chunks": [],
        "citations": [],
        "answer": "",
        "confidence_score": 0.0,
        "verification_score": 0.0,
        "grounding_score": 0.0,
        "verification_status": "UNSUPPORTED",
        "verification_attempts": 0,
        "adaptive_retrieval_used": False,
        "retrieval_attempts": 1,
        "initial_retrieved_count": 0,
        "final_retrieved_count": 0,
        "evidence_expansion_factor": 1.0,
        "adaptive_retrieval_reason": "",
        "verification_score_before_adaptation": 0.0,
        "verification_score_after_adaptation": 0.0,
        "verification_improvement": 0.0,
        "execution_metadata": {}
    }
    
    final_state = graph.invoke(initial_state)
    
    # Assert retriever run once
    mock_retriever.run.assert_called_once()
    # Assert adaptive retriever run once
    mock_adaptive_retriever.run.assert_called_once()
    # Assert generator run twice (first run + adaptive regeneration)
    assert mock_generator.run.call_count == 2
    # Assert verifier run twice
    assert mock_verifier.run.call_count == 2
    
    # Assert final results are correct
    assert final_state["answer"] == "Regenerated strong answer"
    assert final_state["verification_score"] == 0.85
    assert final_state["verification_status"] == "SUPPORTED"
    assert final_state["retrieval_attempts"] == 2
    assert final_state["adaptive_retrieval_used"] is True
    assert final_state["evidence_expansion_factor"] == 2.0
    assert final_state["verification_improvement"] == 0.45
