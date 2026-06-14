import pytest
from app.services.graph.relationship_extractor import RelationshipExtractor

def test_heuristic_relationship_extraction():
    extractor = RelationshipExtractor()
    text = "We evaluate TCP. TCP relies on Congestion Control and is part of the transport layer."
    
    entities = [
        {"name": "TCP", "type": "Protocols", "confidence": 0.95},
        {"name": "Congestion Control", "type": "Networking Terms", "confidence": 0.95},
        {"name": "Transport Layer", "type": "Networking Terms", "confidence": 0.95}
    ]
    
    rels = extractor.extract_relationships(text, entities)
    
    # Assert extracted relations
    assert len(rels) >= 2
    
    uses_rel = next((r for r in rels if r["source"] == "TCP" and r["target"] == "Congestion Control"), None)
    assert uses_rel is not None
    assert uses_rel["type"] == "USES"
    assert uses_rel["confidence"] == 0.92
    
    belongs_rel = next((r for r in rels if r["source"] == "TCP" and r["target"] == "Transport Layer"), None)
    assert belongs_rel is not None
    assert belongs_rel["type"] == "BELONGS_TO"
    assert belongs_rel["confidence"] == 0.95


def test_relationship_validation_drops_invalid_entities():
    extractor = RelationshipExtractor()
    entities = [
        {"name": "TCP", "type": "Protocols", "confidence": 0.95},
        {"name": "Congestion Control", "type": "Networking Terms", "confidence": 0.95},
    ]

    raw_rels = [
        {"source": "TCP", "target": "Congestion Control", "type": "USES", "confidence": 0.9},
        {"source": "TCP", "target": "Unknown Entity", "type": "USES", "confidence": 0.9},
        {"source": "Ghost", "target": "TCP", "type": "RELATED_TO", "confidence": 0.8},
    ]

    valid = extractor._validate_against_entities(raw_rels, entities)
    assert len(valid) == 1
    assert valid[0]["target"] == "Congestion Control"
