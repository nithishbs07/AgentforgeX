import pytest
from app.services.agents.evidence_aggregator import EvidenceAggregator

def test_evidence_aggregator_dedup_and_rank():
    aggregator = EvidenceAggregator()
    
    # Input state with duplicate chunks in sub_questions_results
    state = {
        "evidence_package": {
            "sub_questions_results": {
                "q1": {
                    "chunks": [
                        {"chunk_text": "This is duplicate chunk.", "document_id": "doc1", "filename": "doc.pdf", "page_number": 1, "similarity_score": 0.80},
                        {"chunk_text": "Unique chunk A.", "document_id": "doc1", "filename": "doc.pdf", "page_number": 2, "similarity_score": 0.75}
                    ],
                    "graph_entities": [{"name": "TCP"}],
                    "graph_relationships": [{"source": "TCP", "type": "USES", "target": "AIMD"}]
                },
                "q2": {
                    "chunks": [
                        # Duplicate chunk with higher score
                        {"chunk_text": "This is duplicate chunk.", "document_id": "doc1", "filename": "doc.pdf", "page_number": 1, "similarity_score": 0.90},
                        {"chunk_text": "Unique chunk B.", "document_id": "doc1", "filename": "doc.pdf", "page_number": 3, "similarity_score": 0.70}
                    ],
                    "graph_entities": [{"name": "TCP"}, {"name": "UDP"}],
                    "graph_relationships": [{"source": "TCP", "type": "USES", "target": "AIMD"}]
                }
            }
        },
        "execution_metadata": {}
    }

    result = aggregator.run(state)
    
    # Assert retrieved_chunks are updated
    retrieved_chunks = result["retrieved_chunks"]
    assert len(retrieved_chunks) == 3  # "This is duplicate chunk", "Unique chunk A", "Unique chunk B"
    
    # Assert it kept the duplicate with the higher similarity score (0.90)
    dup_chunk = next(c for c in retrieved_chunks if "duplicate" in c["chunk_text"])
    assert dup_chunk["similarity_score"] == 0.90
    
    # Assert it is ranked by similarity score descending (0.90, 0.75, 0.70)
    assert retrieved_chunks[0]["similarity_score"] == 0.90
    assert retrieved_chunks[1]["similarity_score"] == 0.75
    assert retrieved_chunks[2]["similarity_score"] == 0.70

    # Assert graph entities deduplication (TCP and UDP only, no duplicates)
    assert len(result["graph_entities"]) == 2
    entity_names = [e["name"] for e in result["graph_entities"]]
    assert "TCP" in entity_names
    assert "UDP" in entity_names

    # Assert quality score calculation
    # (0.90 + 0.75 + 0.70) / 3 = 0.7833
    assert result["evidence_package"]["quality_score"] == 0.7833
