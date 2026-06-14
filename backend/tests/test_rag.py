import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.retrieval import ChromaRetriever
from app.services.generation_service import OllamaGenerationService
from app.services.rag_service import RAGService
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.evaluation_repository import EvaluationRepository

@pytest.fixture(autouse=True)
def disable_deep_research():
    with patch("app.core.config.settings.USE_DEEP_RESEARCH", False):
        yield


# 1. Retrieval Layer Tests
def test_chroma_retriever_retrieve():
    # Mock VectorStoreService
    mock_vector_store = MagicMock()
    mock_vector_store.query_similar.return_value = [
        {
            "id": "doc1_0",
            "text": "TCP congestion control operates by adjusting window size.",
            "metadata": {
                "document_id": "doc1",
                "filename": "tcp_spec.pdf",
                "page_number": 12
            },
            "score": 0.95
        }
    ]

    retriever = ChromaRetriever(vector_store=mock_vector_store)
    results = retriever.retrieve("TCP congestion control", top_k=1)

    assert len(results) == 1
    assert results[0]["chunk_text"] == "TCP congestion control operates by adjusting window size."
    assert results[0]["document_id"] == "doc1"
    assert results[0]["filename"] == "tcp_spec.pdf"
    assert results[0]["page_number"] == 12
    assert results[0]["similarity_score"] == 0.95
    mock_vector_store.query_similar.assert_called_once_with("TCP congestion control", top_k=1)

# 2. Generation Service Tests
@patch("requests.post")
def test_ollama_generation_service(mock_post):
    # Mock Ollama API response
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "TCP congestion control matches window transmission rates."}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    gen_service = OllamaGenerationService()
    context = [
        {
            "chunk_text": "TCP congestion control operates by adjusting window size.",
            "filename": "tcp_spec.pdf",
            "page_number": 12
        }
    ]

    answer = gen_service.generate_answer("What is TCP congestion control?", context)

    assert answer == "TCP congestion control matches window transmission rates."
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "api/generate" in args[0]
    assert kwargs["json"]["model"] == settings.OLLAMA_LLM_MODEL
    assert "TCP congestion control operates by adjusting window size." in kwargs["json"]["prompt"]

# 3. RAG Service Pipeline & Logic Tests
@patch("requests.post")
def test_rag_service_pipeline(mock_post, db_session):
    # Setup database repos
    session_repo = SessionRepository(db_session)
    message_repo = MessageRepository(db_session)
    evaluation_repo = EvaluationRepository(db_session)

    # Create session
    session = session_repo.create({"title": "RAG Test Session"})

    # Mock ChromaRetriever
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = [
        {
            "chunk_text": "Congestion avoidance uses AIMD controls.",
            "document_id": "doc2",
            "filename": "networks.pdf",
            "page_number": 88,
            "similarity_score": 0.90
        },
        {
            "chunk_text": "Slow start doubles window size per RTT.",
            "document_id": "doc2",
            "filename": "networks.pdf",
            "page_number": 89,
            "similarity_score": 0.80
        }
    ]

    # Mock Ollama responses:
    # 1. Router routes to retrieval
    # 2. Generator answers
    # 3. Verifier checks answer
    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {"response": '{"route": "vector", "route_confidence": 0.94}'},
        {"response": "TCP congestion avoidance relies on AIMD and slow start."},
        {"response": '{"score": 0.91, "status": "SUPPORTED", "reason": "Fully grounded."}'}
    ]
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    # Instantiate RAGService with mocks
    rag_service = RAGService(
        session_repo=session_repo,
        message_repo=message_repo,
        evaluation_repo=evaluation_repo,
        retriever=mock_retriever,
        generation_service=OllamaGenerationService()
    )

    response = rag_service.query_rag(session.id, "Summarize TCP congestion avoidance in the uploaded PDF document")

    # Verify RAG Pipeline Output
    assert response["answer"] == "TCP congestion avoidance relies on AIMD and slow start."
    assert response["confidence_score"] == pytest.approx(0.85)  # (0.90 + 0.80) / 2
    assert response["verification_score"] > 0.80
    assert response["grounding_score"] > 0.70
    assert response["verification_status"] == "SUPPORTED"
    assert len(response["citations"]) == 2
    assert response["citations"][0]["document_id"] == "doc2"
    assert response["citations"][0]["page_number"] == 88

    # Verify Database Persistence
    messages = message_repo.get_by_session_id(session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].content == "TCP congestion avoidance relies on AIMD and slow start."

    # Verify Citations DB Persistence
    assert len(messages[1].citations) == 2
    assert messages[1].citations[0].snippet == "Congestion avoidance uses AIMD controls."

    # Verify Evaluation Logging
    logs = evaluation_repo.get_multi()
    assert len(logs) == 1
    assert logs[0].query == "Summarize TCP congestion avoidance in the uploaded PDF document"
    assert logs[0].retrieved_count == 2
    assert logs[0].top_score == pytest.approx(0.90)
    assert logs[0].avg_score == pytest.approx(0.85)
    assert logs[0].verification_score == response["verification_score"]
    assert logs[0].verification_status == "SUPPORTED"
    assert logs[0].grounding_score == response["grounding_score"]

# 4. Chat Endpoint Router Test
@patch("requests.post")
def test_chat_api_endpoint(mock_post, client: TestClient, db_session):
    # Create test session
    session_repo = SessionRepository(db_session)
    session = session_repo.create({"title": "Endpoint Test Session"})

    # Setup mock generation output (1. router, 2. generator, 3. verifier)
    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {"response": '{"route": "vector", "route_confidence": 0.94}'},
        {"response": "Sample text chunk is generated."},
        {"response": '{"score": 0.92, "status": "SUPPORTED", "reason": "Looks good."}'}
    ]
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    # Patch ChromaRetriever retrieve method to return static values
    with patch("app.services.retrieval.ChromaRetriever.retrieve") as mock_retrieve:
        mock_retrieve.return_value = [
            {
                "chunk_text": "Sample text chunk.",
                "document_id": "doc_test",
                "filename": "test.pdf",
                "page_number": 1,
                "similarity_score": 0.92
            }
        ]

        payload = {
            "session_id": session.id,
            "message": "Summarize the uploaded PDF document"
        }
        
        response = client.post(f"{settings.API_V1_STR}/chat", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Sample text chunk is generated."
        assert data["confidence_score"] == 0.92
        assert data["grounding_score"] > 0.0
        assert data["verification_score"] > 0.80
        assert data["verification_status"] == "SUPPORTED"
        assert len(data["citations"]) == 1
        assert data["citations"][0]["filename"] == "test.pdf"
        assert data["citations"][0]["snippet"] == "Sample text chunk."


# 5. Adaptive Retrieval Pipeline Tests
@patch("requests.post")
def test_rag_service_adaptive_retrieval(mock_post, db_session):
    # Setup database repos
    session_repo = SessionRepository(db_session)
    message_repo = MessageRepository(db_session)
    evaluation_repo = EvaluationRepository(db_session)

    # Create session
    session = session_repo.create({"title": "RAG Adaptive Test Session"})

    # Mock ChromaRetriever returning different top_k values
    mock_retriever = MagicMock()
    def retrieve_side_effect(query, top_k=5):
        if top_k == 5:
            return [
                {
                    "chunk_text": "Initial context chunk.",
                    "document_id": "doc1",
                    "filename": "test.pdf",
                    "page_number": 1,
                    "similarity_score": 0.80
                }
            ]
        else:
            return [
                {
                    "chunk_text": "Initial context chunk.",
                    "document_id": "doc1",
                    "filename": "test.pdf",
                    "page_number": 1,
                    "similarity_score": 0.80
                },
                {
                    "chunk_text": "Expanded context chunk.",
                    "document_id": "doc1",
                    "filename": "test.pdf",
                    "page_number": 2,
                    "similarity_score": 0.85
                }
            ]
    mock_retriever.retrieve.side_effect = retrieve_side_effect

    # Mock Ollama response sequence:
    # 1. Router routes to retrieval
    # 2. Generator first response (weak)
    # 3. Verifier first response (low score, triggers adaptation)
    # 4. Generator second response (stronger)
    # 5. Verifier second response (high score)
    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {"response": '{"route": "vector", "route_confidence": 0.90}'},
        {"response": "Initial weak response."},
        {"response": '{"score": 0.40, "status": "UNSUPPORTED", "reason": "Weak grounding"}'},
        {"response": "Regenerated response with expanded context."},
        {"response": '{"score": 0.85, "status": "SUPPORTED", "reason": "Good support"}'}
    ]
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    # Instantiate RAGService
    rag_service = RAGService(
        session_repo=session_repo,
        message_repo=message_repo,
        evaluation_repo=evaluation_repo,
        retriever=mock_retriever,
        generation_service=OllamaGenerationService()
    )

    response = rag_service.query_rag(session.id, "Explain TCP adaptation")

    # Verify Response Fields
    assert response["answer"] == "Regenerated response with expanded context."
    assert response["adaptive_retrieval_used"] is True
    assert response["verification_score"] > 0.80
    assert response["verification_improvement"] > 0.20
    assert response["verification_status"] == "SUPPORTED"
    assert len(response["citations"]) == 2
    assert response["citations"][0]["snippet"] == "Initial context chunk."
    assert response["citations"][1]["snippet"] == "Expanded context chunk."

    # Verify Evaluation Log Persistence
    logs = evaluation_repo.get_multi()
    assert len(logs) == 1
    assert logs[0].adaptive_retrieval_used is True
    assert logs[0].retrieval_attempts == 2
    assert logs[0].evidence_expansion_factor == 2.0
    assert logs[0].verification_improvement > 0.20


@patch("requests.post")
def test_chat_api_endpoint_adaptive_retrieval(mock_post, client: TestClient, db_session):
    session_repo = SessionRepository(db_session)
    session = session_repo.create({"title": "Endpoint Adaptive Test"})

    # Mock Ollama sequence
    mock_response = MagicMock()
    mock_response.json.side_effect = [
        {"response": '{"route": "vector", "route_confidence": 0.90}'},
        {"response": "Initial weak reply."},
        {"response": '{"score": 0.40, "status": "UNSUPPORTED", "reason": "Weak answer"}'},
        {"response": "Strong adaptive reply."},
        {"response": '{"score": 0.85, "status": "SUPPORTED", "reason": "Now supported"}'}
    ]
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    with patch("app.services.retrieval.ChromaRetriever.retrieve") as mock_retrieve:
        def retrieve_side_effect(query, top_k=5):
            if top_k == 5:
                return [
                    {
                        "chunk_text": "First chunk text.",
                        "document_id": "doc_adapt",
                        "filename": "adapt.pdf",
                        "page_number": 1,
                        "similarity_score": 0.75
                    }
                ]
            else:
                return [
                    {
                        "chunk_text": "First chunk text.",
                        "document_id": "doc_adapt",
                        "filename": "adapt.pdf",
                        "page_number": 1,
                        "similarity_score": 0.75
                    },
                    {
                        "chunk_text": "Second chunk text.",
                        "document_id": "doc_adapt",
                        "filename": "adapt.pdf",
                        "page_number": 2,
                        "similarity_score": 0.80
                    }
                ]
        mock_retrieve.side_effect = retrieve_side_effect

        payload = {
            "session_id": session.id,
            "message": "Run adaptive test"
        }

        response = client.post(f"{settings.API_V1_STR}/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Strong adaptive reply."
        assert data["adaptive_retrieval_used"] is True
        assert data["verification_improvement"] > 0.20
        assert len(data["citations"]) == 2
        assert data["citations"][0]["snippet"] == "First chunk text."
        assert data["citations"][1]["snippet"] == "Second chunk text."

