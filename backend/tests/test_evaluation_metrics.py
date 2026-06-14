import pytest
from unittest.mock import patch, MagicMock
from app.services.evaluation.metrics import RAGEvaluator

def test_evaluation_metrics_online():
    evaluator = RAGEvaluator()
    
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"response": '{"score": 0.92}'}
    mock_post_resp.raise_for_status = MagicMock()

    with patch("app.services.embedding_service.is_ollama_online", return_value=True):
        with patch("requests.post", return_value=mock_post_resp):
            faithfulness = evaluator.calculate_faithfulness("Answer text", [{"chunk_text": "Context text"}])
            relevancy = evaluator.calculate_answer_relevancy("Query text", "Answer text")
            recall = evaluator.calculate_context_recall("Query text", [{"chunk_text": "Context text"}])
            
            assert faithfulness == 0.92
            assert relevancy == 0.92
            assert recall == 0.92

def test_evaluation_metrics_offline_fallback():
    evaluator = RAGEvaluator()
    
    with patch("app.services.embedding_service.is_ollama_online", return_value=False):
        # Faithfulness fallback (overlap between answer and context)
        # "congestion control algorithm" in both answer and context
        context = [{"chunk_text": "This discusses the Congestion Control Algorithm TCP uses."}]
        answer = "We implement a Congestion Control Algorithm."
        faithfulness = evaluator.calculate_faithfulness(answer, context)
        
        # Answer Relevancy fallback (overlap between query and answer)
        query = "Explain Congestion Control."
        relevancy = evaluator.calculate_answer_relevancy(query, answer)
        
        # Context Precision (Average Precision of relevant chunks)
        # Check that it returns a value between 0.0 and 1.0
        precision = evaluator.calculate_context_precision(query, context)
        
        # Context Recall (Query keyword coverage in context)
        recall = evaluator.calculate_context_recall(query, context)
        
        assert 0.0 <= faithfulness <= 1.0
        assert 0.0 <= relevancy <= 1.0
        assert 0.0 <= precision <= 1.0
        assert 0.0 <= recall <= 1.0
        
        # Check actual score calculations
        assert faithfulness > 0.0
        assert relevancy > 0.0
        assert precision > 0.0
        assert recall > 0.0
