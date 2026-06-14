import time
import logging
from typing import List, Dict, Any
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

class GraphRetriever:
    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j_service = neo4j_service
        self.entity_extractor = EntityExtractor()

    def retrieve(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Retrieves Knowledge Graph paths, entities, relationships, and source chunks for a query.
        Process:
          1. Detect entities in user query.
          2. Query Neo4j to retrieve entities and their 2-hop neighbors.
          3. Fetch original source chunks that mention any of these entities.
          4. Return unified context dictionary.
        """
        start_time = time.time()
        
        results = {
            "entities": [],
            "relationships": [],
            "retrieved_chunks": [],
            "confidence": 0.0,
            "hit_count": 0,
            "latency_ms": 0
        }

        if not self.neo4j_service.health_check():
            logger.warning("Neo4j offline. Graph retriever returning empty results.")
            return results

        # 1. Extract query entities
        query_entities = self.entity_extractor.extract_entities(query)
        entity_names = [e["name"].lower() for e in query_entities]
        
        # If no explicit entities found, split query into words to find fuzzy keyword matches
        if not entity_names:
            words = [w.strip(",.?\"'()").lower() for w in query.split() if len(w.strip()) > 3]
            entity_names = words[:5] # Limit search keywords to prevent query bloat

        if not entity_names:
            return results

        # 2. Fetch seed nodes and 2-hop neighbors
        cypher_nodes_rels = """
        MATCH (e:Entity)
        WHERE toLower(e.name) IN $names OR any(name IN $names WHERE toLower(e.name) CONTAINS name)
        OPTIONAL MATCH (e)-[r]-(neighbor:Entity)
        RETURN e.name AS src_name, e.type AS src_type, e.confidence AS src_conf,
               type(r) AS rel_type, r.confidence AS rel_conf,
               neighbor.name AS tgt_name, neighbor.type AS tgt_type, neighbor.confidence AS tgt_conf
        LIMIT 25
        """
        records = self.neo4j_service.query_graph(cypher_nodes_rels, {"names": entity_names})
        
        entities_map = {}
        rels_set = set()
        
        for rec in records:
            src_name = rec.get("src_name")
            if src_name:
                entities_map[src_name.lower()] = {
                    "name": src_name,
                    "type": rec.get("src_type"),
                    "confidence": rec.get("src_conf", 0.90)
                }
                
            tgt_name = rec.get("tgt_name")
            if tgt_name:
                entities_map[tgt_name.lower()] = {
                    "name": tgt_name,
                    "type": rec.get("tgt_type"),
                    "confidence": rec.get("tgt_conf", 0.90)
                }
                
            rel_type = rec.get("rel_type")
            if src_name and tgt_name and rel_type:
                # Store relationship directional/non-directional deduped key
                rel_key = tuple(sorted([src_name.lower(), tgt_name.lower()])) + (rel_type,)
                if rel_key not in rels_set:
                    rels_set.add(rel_key)
                    results["relationships"].append({
                        "source": src_name,
                        "type": rel_type,
                        "target": tgt_name,
                        "confidence": rec.get("rel_conf", 0.80)
                    })

        results["entities"] = list(entities_map.values())
        
        # 3. Retrieve source chunks that mention any of these entities
        all_entity_names = list(entities_map.keys())
        if all_entity_names:
            # Query source document chunks
            cypher_chunks = """
            MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE toLower(e.name) IN $entity_names
            OPTIONAL MATCH (d:Document {id: c.doc_id})
            RETURN c.text AS text, c.doc_id AS doc_id, c.page_number AS page_num, d.filename AS filename, count(e) AS match_weight
            ORDER BY match_weight DESC
            LIMIT $limit
            """
            chunk_records = self.neo4j_service.query_graph(cypher_chunks, {
                "entity_names": all_entity_names,
                "limit": top_k
            })
            
            # Format chunks to match Chroma similarity result structure for downstream agents
            for rec in chunk_records:
                results["retrieved_chunks"].append({
                    "chunk_text": rec.get("text", ""),
                    "similarity_score": 0.80 + (0.04 * min(rec.get("match_weight", 1), 4)), # Synthesize score based on entity match weight
                    "document_id": rec.get("doc_id", ""),
                    "page_number": rec.get("page_num", 1),
                    "filename": rec.get("filename", "unknown_document.pdf")
                })
                
        # Calculate scores
        results["hit_count"] = len(results["retrieved_chunks"])
        if results["entities"]:
            results["confidence"] = sum(e["confidence"] for e in results["entities"]) / len(results["entities"])
            
        results["latency_ms"] = int((time.time() - start_time) * 1000)
        return results
