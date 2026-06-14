import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from neo4j import GraphDatabase
from app.core.config import settings
from app.services.graph.ids import make_entity_id, make_page_id

logger = logging.getLogger(__name__)

SCHEMA_STATEMENTS = [
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
    "CREATE INDEX entity_doc IF NOT EXISTS FOR (e:Entity) ON (e.doc_id)",
]


class Neo4jService:
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.driver = None
        self.is_online = False
        self._schema_initialized = False
        self._last_connect_time = 0.0

        self.connect()

    def connect(self) -> None:
        """Attempts to establish connection to Neo4j database."""
        if time.time() - self._last_connect_time < 60.0:
            return
        self._last_connect_time = time.time()
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password), connection_timeout=2.0)
            self.driver.verify_connectivity()
            self.is_online = True
            logger.info("Successfully connected to Neo4j graph database.")
            self.ensure_schema()
        except Exception as e:
            logger.warning(f"Neo4j driver initialization failed: {e}. falling back to offline mode.")
            self.driver = None
            self.is_online = False

    def health_check(self) -> bool:
        """Verifies if Neo4j is online and responding."""
        if not self.is_online or not self.driver:
            self.connect()

        if not self.is_online or not self.driver:
            return False

        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            self.is_online = False
            return False

    def ensure_schema(self) -> None:
        """Idempotently creates constraints and indexes."""
        if self._schema_initialized or not self.health_check() or not self.driver:
            return

        for statement in SCHEMA_STATEMENTS:
            try:
                with self.driver.session() as session:
                    session.run(statement)
            except Exception as e:
                logger.warning(f"Schema statement failed (may already exist): {e}")

        self._schema_initialized = True
        logger.info("Neo4j schema constraints and indexes verified.")

    def query_graph(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a cypher query on the graph database and returns list of dict records."""
        if not self.health_check() or not self.driver:
            logger.debug("Neo4j offline. Skipping cypher query execution.")
            return []

        parameters = parameters or {}
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.warning(f"Failed to execute Cypher query: {e}")
            return []

    def create_entity(
        self,
        name: str,
        entity_type: str,
        confidence: float,
        doc_id: str,
        page_num: Optional[int] = None,
    ) -> None:
        """
        Creates a document-scoped entity node.
        Entity id = {doc_id}:{name} to prevent cross-document contamination.
        """
        if not self.health_check() or not doc_id:
            return

        created_at = datetime.now(timezone.utc).isoformat()
        entity_id = make_entity_id(doc_id, name)
        conf = min(float(confidence), 1.0)

        cypher_entity = """
        MERGE (e:Entity {id: $entity_id})
        ON CREATE SET
            e.name = $name,
            e.type = $type,
            e.doc_id = $doc_id,
            e.confidence = $confidence,
            e.created_at = $created_at
        ON MATCH SET
            e.confidence = CASE WHEN $confidence > e.confidence THEN $confidence ELSE e.confidence END
        """
        self.query_graph(cypher_entity, {
            "entity_id": entity_id,
            "name": name,
            "type": entity_type,
            "doc_id": doc_id,
            "confidence": conf,
            "created_at": created_at,
        })

        cypher_doc = """
        MERGE (d:Document {id: $doc_id})
        ON CREATE SET d.created_at = $created_at
        """
        self.query_graph(cypher_doc, {"doc_id": doc_id, "created_at": created_at})

        cypher_doc_link = """
        MATCH (d:Document {id: $doc_id}), (e:Entity {id: $entity_id})
        MERGE (d)-[r:CONTAINS]->(e)
        ON CREATE SET r.created_at = $created_at
        """
        self.query_graph(cypher_doc_link, {
            "doc_id": doc_id,
            "entity_id": entity_id,
            "created_at": created_at,
        })

        if page_num is not None:
            page_id = make_page_id(doc_id, page_num)
            cypher_page = """
            MERGE (p:Page {id: $page_id})
            SET p.page_number = $page_num, p.doc_id = $doc_id
            """
            self.query_graph(cypher_page, {
                "page_id": page_id,
                "page_num": page_num,
                "doc_id": doc_id,
            })

            cypher_doc_page = """
            MATCH (d:Document {id: $doc_id}), (p:Page {id: $page_id})
            MERGE (d)-[r:HAS_PAGE]->(p)
            """
            self.query_graph(cypher_doc_page, {"doc_id": doc_id, "page_id": page_id})

            cypher_page_link = """
            MATCH (p:Page {id: $page_id}), (e:Entity {id: $entity_id})
            MERGE (p)-[r:CONTAINS]->(e)
            ON CREATE SET r.created_at = $created_at
            """
            self.query_graph(cypher_page_link, {
                "page_id": page_id,
                "entity_id": entity_id,
                "created_at": created_at,
            })

    def link_chunk_mentions(self, chunk_id: str, doc_id: str, entity_name: str, confidence: float) -> None:
        """Links Chunk -[:MENTIONS {confidence}]-> Entity within the same document."""
        if not self.health_check():
            return

        entity_id = make_entity_id(doc_id, entity_name)
        mention_conf = min(float(confidence), 1.0)

        cypher_mentions = """
        MATCH (c:Chunk {id: $chunk_id}), (e:Entity {id: $entity_id})
        MERGE (c)-[r:MENTIONS]->(e)
        ON CREATE SET r.confidence = $confidence
        ON MATCH SET
            r.confidence = CASE WHEN $confidence > r.confidence THEN $confidence ELSE r.confidence END
        """
        self.query_graph(cypher_mentions, {
            "chunk_id": chunk_id,
            "entity_id": entity_id,
            "confidence": mention_conf,
        })

    def create_relationship(
        self,
        doc_id: str,
        source_name: str,
        rel_type: str,
        target_name: str,
        confidence: float,
    ) -> None:
        """Creates a directed relationship between document-scoped entities."""
        if not self.health_check() or not doc_id:
            return

        allowed_types = [
            "USES", "IMPLEMENTS", "BELONGS_TO", "CONNECTS_TO",
            "DEPENDS_ON", "RELATED_TO", "PART_OF",
        ]
        if rel_type not in allowed_types:
            logger.warning(f"Custom relationship type {rel_type} not in allowed schema. Normalizing to RELATED_TO.")
            rel_type = "RELATED_TO"

        created_at = datetime.now(timezone.utc).isoformat()
        source_id = make_entity_id(doc_id, source_name)
        target_id = make_entity_id(doc_id, target_name)
        conf = min(float(confidence), 1.0)

        cypher_rel = f"""
        MATCH (source:Entity {{id: $source_id}}), (target:Entity {{id: $target_id}})
        WHERE source.doc_id = $doc_id AND target.doc_id = $doc_id
        MERGE (source)-[r:{rel_type}]->(target)
        ON CREATE SET
            r.confidence = $confidence,
            r.created_at = $created_at
        ON MATCH SET
            r.confidence = CASE WHEN $confidence > r.confidence THEN $confidence ELSE r.confidence END
        """
        self.query_graph(cypher_rel, {
            "source_id": source_id,
            "target_id": target_id,
            "doc_id": doc_id,
            "confidence": conf,
            "created_at": created_at,
        })

    def delete_document_graph(self, document_id: str) -> None:
        """Deletes Document, Pages, Chunks, and all document-scoped entities/relationships."""
        if not self.health_check():
            return

        logger.info(f"Deleting Neo4j sub-graph entries for document_id: {document_id}")

        delete_chunks_and_pages = """
        MATCH (d:Document {id: $doc_id})
        OPTIONAL MATCH (d)-[:HAS_PAGE]->(p:Page)
        OPTIONAL MATCH (p)-[:HAS_CHUNK]->(c:Chunk)
        DETACH DELETE c, p
        """
        self.query_graph(delete_chunks_and_pages, {"doc_id": document_id})

        delete_entities = """
        MATCH (e:Entity {doc_id: $doc_id})
        DETACH DELETE e
        """
        self.query_graph(delete_entities, {"doc_id": document_id})

        delete_document = """
        MATCH (d:Document {id: $doc_id})
        DETACH DELETE d
        """
        self.query_graph(delete_document, {"doc_id": document_id})

    def close(self) -> None:
        """Closes the active connection driver."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j driver connection.")
