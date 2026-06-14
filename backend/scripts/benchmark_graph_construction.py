#!/usr/bin/env python3
"""
Benchmark graph construction throughput for AgentForge-X Phase 7A.
Run from backend/: python scripts/benchmark_graph_construction.py
"""
import os
import sys
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.graph.graph_builder import GraphBuilder


SAMPLE_TEXT = (
    "TCP is a transport protocol that uses Congestion Control. "
    "AIMD implements additive increase and multiplicative decrease. "
    "HTTP depends on TCP at the application layer."
)


def make_chunks(count: int):
    return [
        {"text": f"{SAMPLE_TEXT} Chunk index {i}.", "page_number": (i % 5) + 1}
        for i in range(count)
    ]


def run_benchmark(chunk_count: int) -> dict:
    mock_neo4j = MagicMock()
    mock_neo4j.health_check.return_value = True
    mock_neo4j.query_graph.return_value = []
    mock_neo4j.ensure_schema.return_value = None

    builder = GraphBuilder(mock_neo4j)
    chunks = make_chunks(chunk_count)

    t0 = time.time()
    metrics = builder.build_document_graph(
        doc_id=f"bench-doc-{chunk_count}",
        filename=f"benchmark_{chunk_count}.pdf",
        chunks=chunks,
    )
    elapsed = time.time() - t0

    entities_per_chunk = (
        metrics["entities_created"] / metrics["chunks_processed"]
        if metrics["chunks_processed"]
        else 0.0
    )
    rels_per_chunk = (
        metrics["relationships_created"] / metrics["chunks_processed"]
        if metrics["chunks_processed"]
        else 0.0
    )

    return {
        "chunk_count": chunk_count,
        "total_latency_ms": metrics["latency_ms"],
        "wall_clock_ms": int(elapsed * 1000),
        "entities_created": metrics["entities_created"],
        "relationships_created": metrics["relationships_created"],
        "neo4j_calls": metrics["neo4j_calls"],
        "entities_per_chunk": round(entities_per_chunk, 2),
        "relationships_per_chunk": round(rels_per_chunk, 2),
    }


def write_report(results: list[dict], output_path: str) -> None:
    lines = [
        "# AgentForge-X Phase 7A: Graph Construction Benchmark",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Benchmark uses mocked Neo4j to measure graph builder orchestration overhead "
        "(entity extraction, relationship validation, Cypher call volume).",
        "",
        "## Results",
        "",
        "| Chunks | Latency (ms) | Entities | Relationships | Neo4j Calls | Entities/Chunk | Rels/Chunk |",
        "|--------|--------------|----------|---------------|-------------|----------------|------------|",
    ]

    for row in results:
        lines.append(
            f"| {row['chunk_count']} | {row['total_latency_ms']} | "
            f"{row['entities_created']} | {row['relationships_created']} | "
            f"{row['neo4j_calls']} | {row['entities_per_chunk']} | "
            f"{row['relationships_per_chunk']} |"
        )

    lines.extend([
        "",
        "## Notes",
        "",
        "- Chunk IDs use `{document_id}_{index}` aligned with ChromaDB.",
        "- Entities are document-scoped: `{document_id}:{entity_name}`.",
        "- MENTIONS edges store entity confidence.",
        "- Neo4j offline skips graph construction without failing ingestion.",
        "",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    sizes = [10, 50, 100, 500]
    results = [run_benchmark(n) for n in sizes]

    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "graph_benchmark_report.md",
    )
    write_report(results, report_path)

    print("Graph construction benchmark complete.")
    for row in results:
        print(
            f"  {row['chunk_count']:>3} chunks -> "
            f"{row['total_latency_ms']}ms, "
            f"{row['entities_created']} entities, "
            f"{row['neo4j_calls']} neo4j calls"
        )
    print(f"\nReport written to: {report_path}")


if __name__ == "__main__":
    main()
