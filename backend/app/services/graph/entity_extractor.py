import re
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.graph.ids import make_entity_id

logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_LLM_MODEL
        
        # Predefined heuristic categories for fallback keyword extraction
        self.heuristic_keywords = {
            "Protocols": [
                "TCP", "UDP", "IP", "DNS", "HTTP", "FTP", "SMTP", "BGP", "ICMP", "ARP", "DHCP", "SSL", "TLS"
            ],
            "Algorithms": [
                "AIMD", "Slow Start", "Congestion Avoidance", "Fast Retransmit", "Fast Recovery", 
                "Dijkstra", "Bellman-Ford", "Raft", "Paxos", "Multiplicative Decrease", "Additive Increase"
            ],
            "Networking Terms": [
                "Congestion Control", "Flow Control", "Routing", "Switching", "Multiplexing", "Encapsulation",
                "RTT", "Throughput", "Bandwidth", "Packet Loss", "Congestion Window", "SSTHRESH"
            ],
            "Technologies": [
                "ChromaDB", "SQLite", "Neo4j", "PostgreSQL", "Docker", "Kubernetes", "Linux", "Git", "Wireshark"
            ],
            "Frameworks": [
                "FastAPI", "Next.js", "React", "LangGraph", "Pytest", "Pydantic", "SQLAlchemy", "Alembic"
            ],
            "AI Concepts": [
                "nomic-embed-text", "Llama 3", "Mistral", "GPT-4", "Ollama", "Vector Store", "Embeddings", 
                "Neural Network", "Transformer", "LLM", "Embedding Model"
            ],
            "Organizations": [
                "Google", "DeepMind", "Microsoft", "OpenAI", "IETF", "IEEE", "W3C"
            ],
            "People": [
                "Van Jacobson", "Tim Berners-Lee", "Vint Cerf", "Bob Kahn"
            ],
            "Datasets": [
                "Citations Dataset", "Evaluation Logs", "IMDb", "SST-2", "MMLU", "GSM8K"
            ],
            "Research Concepts": [
                "Multi-Agent RAG", "Vector Retrieval", "Retrieval-Augmented Generation", "Self-Correction", 
                "Evidence Expansion", "Graph RAG", "Hybrid Retrieval", "Factual Grounding", "Knowledge Graph"
            ]
        }

    @staticmethod
    def attach_document_scope(entities: List[Dict[str, Any]], doc_id: str) -> List[Dict[str, Any]]:
        """Adds document-scoped entity_id and doc_id to each extracted entity."""
        for entity in entities:
            entity["doc_id"] = doc_id
            entity["entity_id"] = make_entity_id(doc_id, entity["name"])
            entity["confidence"] = min(float(entity.get("confidence", 0.85)), 1.0)
        return entities

    def extract_entities(self, text: str, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts entities from the text chunk.
        Tries Ollama LLM extraction, falling back to heuristic regex keyword matching if offline or failed.
        When doc_id is provided, each entity receives a document-scoped entity_id.
        """
        entities = []
        
        # 1. Attempt LLM-based extraction
        try:
            prompt = f"""
            Task: Extract domain-specific entities from the following text chunk.
            Categories: People, Organizations, Technologies, Protocols, Algorithms, Frameworks, Datasets, Research Concepts, Networking Terms, AI Concepts.
            
            Text:
            "{text}"
            
            Format: Respond ONLY with a valid JSON array of objects. Do not include markdown codeblocks or extra text.
            Schema:
            [
              {{
                "name": "TCP",
                "type": "Protocols",
                "confidence": 0.95,
                "description": "Transmission Control Protocol"
              }}
            ]
            """
            
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            parsed = provider.generate_json(prompt)
            if isinstance(parsed, list):
                for item in parsed:
                    name = str(item.get("name", "")).strip()
                    ent_type = str(item.get("type", "")).strip()
                    conf = float(item.get("confidence", 0.85))
                    
                    if name and ent_type:
                        entities.append({
                            "name": name,
                            "type": ent_type,
                            "confidence": conf
                        })
                        
        except Exception as e:
            logger.debug(f"LLM entity extraction failed/offline: {e}. Using heuristics.")

        # 2. Extract using heuristics (merge and resolve duplicates)
        found_names = {e["name"].lower(): e for e in entities}
        
        for category, terms in self.heuristic_keywords.items():
            for term in terms:
                # Use word-boundary search, case-insensitive
                pattern = r'\b' + re.escape(term) + r'\b'
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Match actual case from the text if possible, else use dictionary key
                    matched_name = matches[0] if len(matches[0]) >= len(term) else term
                    
                    # Deduping check
                    if matched_name.lower() not in found_names:
                        entity_record = {
                            "name": matched_name,
                            "type": category,
                            "confidence": 0.95  # Static confidence for exact dictionary match
                        }
                        entities.append(entity_record)
                        found_names[matched_name.lower()] = entity_record

        if doc_id:
            return self.attach_document_scope(entities, doc_id)

        return entities
