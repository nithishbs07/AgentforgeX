import pytest
from app.services.graph.entity_extractor import EntityExtractor

def test_heuristic_entity_extraction():
    extractor = EntityExtractor()
    text = "TCP is a protocol belonging to the transport layer. Van Jacobson designed congestion control algorithms like AIMD for it."

    entities = extractor.extract_entities(text)

    # Check that key entities were extracted via heuristics
    names = {e["name"].lower() for e in entities}
    assert "tcp" in names
    assert "aimd" in names
    assert "congestion control" in names
    assert "van jacobson" in names

    # Check that categories match
    tcp_entity = next(e for e in entities if e["name"].lower() == "tcp")
    assert tcp_entity["type"] == "Protocols"
    assert tcp_entity["confidence"] == 0.95

    aimd_entity = next(e for e in entities if e["name"].lower() == "aimd")
    assert aimd_entity["type"] == "Algorithms"

    van_entity = next(e for e in entities if e["name"].lower() == "van jacobson")
    assert van_entity["type"] == "People"


def test_document_scoped_entity_extraction():
    extractor = EntityExtractor()
    text = "TCP uses Congestion Control."

    entities = extractor.extract_entities(text, doc_id="doc-a")
    tcp = next(e for e in entities if e["name"].lower() == "tcp")

    assert tcp["entity_id"] == "doc-a:TCP"
    assert tcp["doc_id"] == "doc-a"

    entities_b = extractor.extract_entities(text, doc_id="doc-b")
    tcp_b = next(e for e in entities_b if e["name"].lower() == "tcp")
    assert tcp_b["entity_id"] == "doc-b:TCP"
    assert tcp_b["entity_id"] != tcp["entity_id"]
