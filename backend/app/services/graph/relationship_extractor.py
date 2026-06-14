import json
import logging
import requests
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class RelationshipExtractor:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL
        
        # Heuristic relationship definitions for matching network concepts when LLM is offline
        self.heuristic_rules = [
            {"src": "TCP", "tgt": "Congestion Control", "type": "USES", "conf": 0.92},
            {"src": "TCP", "tgt": "Transport Layer", "type": "BELONGS_TO", "conf": 0.95},
            {"src": "AIMD", "tgt": "Congestion Control", "type": "IMPLEMENTS", "conf": 0.90},
            {"src": "Slow Start", "tgt": "Congestion Control", "type": "IMPLEMENTS", "conf": 0.90},
            {"src": "Congestion Avoidance", "tgt": "Congestion Control", "type": "IMPLEMENTS", "conf": 0.90},
            {"src": "Fast Retransmit", "tgt": "Congestion Control", "type": "IMPLEMENTS", "conf": 0.90},
            {"src": "Fast Recovery", "tgt": "Congestion Control", "type": "IMPLEMENTS", "conf": 0.90},
            {"src": "TCP", "tgt": "IP", "type": "CONNECTS_TO", "conf": 0.90},
            {"src": "HTTP", "tgt": "TCP", "type": "DEPENDS_ON", "conf": 0.94},
            {"src": "Congestion Window", "tgt": "Congestion Control", "type": "PART_OF", "conf": 0.88},
            {"src": "AIMD", "tgt": "Multiplicative Decrease", "type": "USES", "conf": 0.90},
            {"src": "AIMD", "tgt": "Additive Increase", "type": "USES", "conf": 0.90},
            {"src": "Congestion Window", "tgt": "SSTHRESH", "type": "RELATED_TO", "conf": 0.85},
            {"src": "LangGraph", "tgt": "Multi-Agent RAG", "type": "USES", "conf": 0.90},
            {"src": "Neo4j", "tgt": "Graph RAG", "type": "USES", "conf": 0.95},
            {"src": "ChromaDB", "tgt": "Vector Retrieval", "type": "USES", "conf": 0.95}
        ]

    def extract_relationships(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts relationships between the provided list of entities found in the text chunk.
        Tries Ollama LLM extraction first, falling back to heuristic co-occurrence rules.
        """
        relationships = []
        if len(entities) < 2:
            return relationships
            
        # 1. Attempt LLM-based extraction
        try:
            entity_names = [e["name"] for e in entities]
            prompt = f"""
            Task: Identify directed relationships between the following list of entities in the text.
            Allowed Relationship Types: USES, IMPLEMENTS, BELONGS_TO, CONNECTS_TO, DEPENDS_ON, RELATED_TO, PART_OF.
            
            Text:
            "{text}"
            
            Entities List: {entity_names}
            
            Format: Respond ONLY with a valid JSON array of objects. Do not include markdown codeblocks or extra text.
            Schema:
            [
              {{
                "source": "TCP",
                "target": "Congestion Control",
                "relationship": "USES",
                "confidence": 0.88
              }}
            ]
            """
            
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            parsed = provider.generate_json(prompt)
            if isinstance(parsed, list):
                for item in parsed:
                    source = str(item.get("source", "")).strip()
                    target = str(item.get("target", "")).strip()
                    rel = str(item.get("relationship", "")).strip().upper()
                    conf = float(item.get("confidence", 0.80))
                    
                    if source and target and rel:
                        relationships.append({
                            "source": source,
                            "target": target,
                            "type": rel,
                            "confidence": conf
                        })

        except Exception as e:
            logger.debug(f"LLM relationship extraction failed/offline: {e}. Using heuristics.")

        # 2. Extract using heuristics fallback
        found_rels = {(r["source"].lower(), r["target"].lower()) for r in relationships}
        entity_map = {e["name"].lower(): e["name"] for e in entities}

        for rule in self.heuristic_rules:
            src_lower = rule["src"].lower()
            tgt_lower = rule["tgt"].lower()

            if src_lower in entity_map and tgt_lower in entity_map:
                if (src_lower, tgt_lower) not in found_rels:
                    rel_record = {
                        "source": entity_map[src_lower],
                        "target": entity_map[tgt_lower],
                        "type": rule["type"],
                        "confidence": rule["conf"]
                    }
                    relationships.append(rel_record)
                    found_rels.add((src_lower, tgt_lower))

        return self._validate_against_entities(relationships, entities)

    def _validate_against_entities(
        self, relationships: List[Dict[str, Any]], entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Drop relationships whose source or target is not in the extracted entity set."""
        entity_names = {e["name"].lower() for e in entities}
        valid: List[Dict[str, Any]] = []

        for rel in relationships:
            source = rel.get("source", "").lower()
            target = rel.get("target", "").lower()
            if source in entity_names and target in entity_names:
                valid.append(rel)
            else:
                logger.debug(
                    f"Dropping invalid relationship {rel.get('source')} -> {rel.get('target')}: "
                    "entity not in chunk extraction set"
                )

        return valid
