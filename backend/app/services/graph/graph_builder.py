import time
import logging
from typing import List, Dict, Any
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.entity_extractor import EntityExtractor
from app.services.graph.relationship_extractor import RelationshipExtractor
from app.services.graph.ids import make_chunk_id, make_page_id

logger = logging.getLogger(__name__)


class GraphBuilder:
    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j_service = neo4j_service
        self.entity_extractor = EntityExtractor()
        self.relationship_extractor = RelationshipExtractor()

    def build_document_graph(
        self, doc_id: str, filename: str, chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Builds the Document-Aware Knowledge Graph in Neo4j from document chunks.
        Returns construction metrics for observability.
        """
        start_time = time.time()
        metrics: Dict[str, Any] = {
            "entities_created": 0,
            "relationships_created": 0,
            "chunks_processed": 0,
            "latency_ms": 0,
            "neo4j_online": False,
            "neo4j_calls": 0,
        }

        if not self.neo4j_service.health_check():
            logger.warning("Neo4j is offline. Skipping Knowledge Graph construction.")
            metrics["latency_ms"] = int((time.time() - start_time) * 1000)
            return metrics

        metrics["neo4j_online"] = True
        self.neo4j_service.ensure_schema()

        logger.info(f"Starting Knowledge Graph construction for document: {filename} ({doc_id})")

        cypher_doc = """
        MERGE (d:Document {id: $doc_id})
        SET d.filename = $filename
        """
        self.neo4j_service.query_graph(cypher_doc, {"doc_id": doc_id, "filename": filename})
        metrics["neo4j_calls"] += 1

        seen_entities: set[str] = set()
        seen_relationships: set[tuple[str, str, str]] = set()

        for idx, chunk in enumerate(chunks):
            page_num = chunk.get("page_number", 1)
            text = chunk.get("text", "")

            page_id = make_page_id(doc_id, page_num)
            chunk_id = make_chunk_id(doc_id, idx)

            cypher_page = """
            MERGE (p:Page {id: $page_id})
            SET p.page_number = $page_num, p.doc_id = $doc_id
            WITH p
            MATCH (d:Document {id: $doc_id})
            MERGE (d)-[:HAS_PAGE]->(p)
            """
            self.neo4j_service.query_graph(cypher_page, {
                "page_id": page_id,
                "page_num": page_num,
                "doc_id": doc_id,
            })
            metrics["neo4j_calls"] += 1

            cypher_chunk = """
            MERGE (c:Chunk {id: $chunk_id})
            SET c.text = $text, c.doc_id = $doc_id, c.page_number = $page_num
            WITH c
            MATCH (p:Page {id: $page_id})
            MERGE (p)-[:HAS_CHUNK]->(c)
            """
            self.neo4j_service.query_graph(cypher_chunk, {
                "chunk_id": chunk_id,
                "text": text,
                "page_id": page_id,
                "doc_id": doc_id,
                "page_num": page_num,
            })
            metrics["neo4j_calls"] += 1
            metrics["chunks_processed"] += 1

            entities = self.entity_extractor.extract_entities(text, doc_id=doc_id)
            logger.debug(
                f"Chunk {chunk_id}: extracted {len(entities)} entities from page {page_num}"
            )

            for entity in entities:
                name = entity["name"]
                ent_type = entity["type"]
                conf = entity["confidence"]
                entity_key = entity.get("entity_id", f"{doc_id}:{name}")

                if entity_key not in seen_entities:
                    seen_entities.add(entity_key)
                    metrics["entities_created"] += 1

                self.neo4j_service.create_entity(name, ent_type, conf, doc_id, page_num)
                metrics["neo4j_calls"] += 1

                self.neo4j_service.link_chunk_mentions(chunk_id, doc_id, name, conf)
                metrics["neo4j_calls"] += 1

            relationships = self.relationship_extractor.extract_relationships(text, entities)
            logger.debug(
                f"Chunk {chunk_id}: storing {len(relationships)} validated relationships"
            )

            for rel in relationships:
                src = rel["source"]
                tgt = rel["target"]
                rel_type = rel["type"]
                conf = rel["confidence"]
                rel_key = (src.lower(), tgt.lower(), rel_type)

                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    metrics["relationships_created"] += 1

                self.neo4j_service.create_relationship(doc_id, src, rel_type, tgt, conf)
                metrics["neo4j_calls"] += 1

        metrics["latency_ms"] = int((time.time() - start_time) * 1000)

        logger.info(
            f"Knowledge Graph built for {filename}: "
            f"{metrics['chunks_processed']} chunks, "
            f"{metrics['entities_created']} entities, "
            f"{metrics['relationships_created']} relationships, "
            f"{metrics['latency_ms']}ms, "
            f"{metrics['neo4j_calls']} Neo4j calls"
        )
        return metrics
