import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import get_evaluation_repo
from app.repositories.evaluation_repository import EvaluationRepository
from app.models.models import EvaluationLog

logger = logging.getLogger(__name__)
router = APIRouter()

def get_filtered_logs(repo: EvaluationRepository, time_range: str) -> List[EvaluationLog]:
    stmt = select(EvaluationLog)
    if time_range != "all":
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if time_range == "24h":
            cutoff = now - timedelta(hours=24)
        elif time_range == "7d":
            cutoff = now - timedelta(days=7)
        elif time_range == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = None
            
        if cutoff:
            stmt = stmt.where(EvaluationLog.timestamp >= cutoff)
            
    stmt = stmt.order_by(EvaluationLog.timestamp.desc())
    results = repo.db.execute(stmt).scalars().all()
    return list(results)

def parse_metadata(log: EvaluationLog) -> Dict[str, Any]:
    if not log.execution_metadata:
        return {}
    try:
        return json.loads(log.execution_metadata)
    except Exception:
        return {}

@router.get("/overview")
def get_overview(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    total_queries = len(logs)
    
    if total_queries == 0:
        return {
            "total_queries": 0,
            "supported_percentage": 0.0,
            "partially_supported_percentage": 0.0,
            "unsupported_percentage": 0.0,
            "adaptive_retrieval_trigger_rate": 0.0,
            "avg_verification_score": 0.0,
            "avg_grounding_score": 0.0,
            "avg_verification_improvement": 0.0
        }

    supported_count = 0
    partially_supported_count = 0
    unsupported_count = 0
    adaptive_triggered_count = 0
    
    v_scores = []
    g_scores = []
    v_improvements = []
    
    for log in logs:
        # Status
        status = (log.verification_status or "UNSUPPORTED").upper()
        if status == "SUPPORTED":
            supported_count += 1
        elif status == "PARTIALLY_SUPPORTED":
            partially_supported_count += 1
        else:
            unsupported_count += 1
            
        # Adaptive retrieval
        if log.adaptive_retrieval_used:
            adaptive_triggered_count += 1
            if log.verification_improvement is not None:
                v_improvements.append(log.verification_improvement)
                
        if log.verification_score is not None:
            v_scores.append(log.verification_score)
            
        if log.grounding_score is not None:
            g_scores.append(log.grounding_score)

    return {
        "total_queries": total_queries,
        "supported_percentage": round((supported_count / total_queries) * 100.0, 2),
        "partially_supported_percentage": round((partially_supported_count / total_queries) * 100.0, 2),
        "unsupported_percentage": round((unsupported_count / total_queries) * 100.0, 2),
        "adaptive_retrieval_trigger_rate": round((adaptive_triggered_count / total_queries) * 100.0, 2),
        "avg_verification_score": round(sum(v_scores) / len(v_scores), 4) if v_scores else 0.0,
        "avg_grounding_score": round(sum(g_scores) / len(g_scores), 4) if g_scores else 0.0,
        "avg_verification_improvement": round(sum(v_improvements) / len(v_improvements), 4) if v_improvements else 0.0
    }

@router.get("/verification")
def get_verification_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    
    # Initialize buckets
    v_distribution = {
        "0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0
    }
    g_distribution = {
        "0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0
    }
    imp_distribution = {
        "< 0.0": 0, "0.0": 0, "0.0-0.1": 0, "0.1-0.2": 0, "0.2-0.4": 0, "> 0.4": 0
    }
    
    timeline = []
    
    # We iterate chronologically for timeline (reverse logs)
    for log in reversed(logs):
        v_val = log.verification_score or 0.0
        g_val = log.grounding_score or 0.0
        imp_val = log.verification_improvement or 0.0
        
        # Verify Score Bucket
        if v_val <= 0.2: v_distribution["0.0-0.2"] += 1
        elif v_val <= 0.4: v_distribution["0.2-0.4"] += 1
        elif v_val <= 0.6: v_distribution["0.4-0.6"] += 1
        elif v_val <= 0.8: v_distribution["0.6-0.8"] += 1
        else: v_distribution["0.8-1.0"] += 1
        
        # Grounding Score Bucket
        if g_val <= 0.2: g_distribution["0.0-0.2"] += 1
        elif g_val <= 0.4: g_distribution["0.2-0.4"] += 1
        elif g_val <= 0.6: g_distribution["0.4-0.6"] += 1
        elif g_val <= 0.8: g_distribution["0.6-0.8"] += 1
        else: g_distribution["0.8-1.0"] += 1
        
        # Improvement Bucket
        if imp_val < 0: imp_distribution["< 0.0"] += 1
        elif imp_val == 0: imp_distribution["0.0"] += 1
        elif imp_val <= 0.1: imp_distribution["0.0-0.1"] += 1
        elif imp_val <= 0.2: imp_distribution["0.1-0.2"] += 1
        elif imp_val <= 0.4: imp_distribution["0.2-0.4"] += 1
        else: imp_distribution["> 0.4"] += 1
        
        timeline.append({
            "timestamp": log.timestamp.isoformat(),
            "verification_score": v_val,
            "grounding_score": g_val,
            "verification_improvement": imp_val
        })
        
    return {
        "verification_distribution": [{"range": k, "count": v} for k, v in v_distribution.items()],
        "grounding_distribution": [{"range": k, "count": v} for k, v in g_distribution.items()],
        "improvement_distribution": [{"range": k, "count": v} for k, v in imp_distribution.items()],
        "timeline": timeline
    }

@router.get("/routing")
def get_routing_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    total = len(logs)
    
    direct_count = 0
    retrieval_count = 0
    
    conf_distribution = {
        "0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0
    }
    
    timeline = []
    
    for log in reversed(logs):
        meta = parse_metadata(log)
        route = meta.get("selected_route", "retrieval" if log.retrieved_count > 0 else "direct")
        confidence = meta.get("route_confidence", 0.0)
        
        if route == "direct":
            direct_count += 1
        else:
            retrieval_count += 1
            
        if confidence <= 0.2: conf_distribution["0.0-0.2"] += 1
        elif confidence <= 0.4: conf_distribution["0.2-0.4"] += 1
        elif confidence <= 0.6: conf_distribution["0.4-0.6"] += 1
        elif confidence <= 0.8: conf_distribution["0.6-0.8"] += 1
        else: conf_distribution["0.8-1.0"] += 1
        
        timeline.append({
            "timestamp": log.timestamp.isoformat(),
            "route": route,
            "confidence": confidence
        })
        
    return {
        "direct_route_count": direct_count,
        "retrieval_route_count": retrieval_count,
        "direct_route_percentage": round((direct_count / total) * 100.0, 2) if total else 0.0,
        "retrieval_route_percentage": round((retrieval_count / total) * 100.0, 2) if total else 0.0,
        "confidence_distribution": [{"range": k, "count": v} for k, v in conf_distribution.items()],
        "timeline": timeline
    }

@router.get("/retrieval")
def get_retrieval_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    
    # Filter only logs where retrieval was used
    retrieval_logs = []
    for log in logs:
        meta = parse_metadata(log)
        if meta.get("retrieval_used", log.retrieved_count > 0):
            retrieval_logs.append((log, meta))
            
    total_retrieval = len(retrieval_logs)
    
    if total_retrieval == 0:
        return {
            "total_retrieval_queries": 0,
            "adaptive_retrieval_count": 0,
            "adaptive_retrieval_percentage": 0.0,
            "retrieval_attempts_distribution": [{"attempts": 1, "count": 0}, {"attempts": 2, "count": 0}],
            "avg_evidence_expansion_factor": 1.0,
            "expansion_factor_distribution": [],
            "timeline": []
        }
        
    adaptive_count = 0
    expansion_factors = []
    attempts_distribution = {1: 0, 2: 0}
    
    exp_distribution = {
        "1.0": 0, "1.0-1.5": 0, "1.5-2.0": 0, "2.0-3.0": 0, "> 3.0": 0
    }
    
    timeline = []
    
    for log, meta in reversed(retrieval_logs):
        adaptive_used = bool(log.adaptive_retrieval_used)
        attempts = log.retrieval_attempts or 1
        exp_factor = log.evidence_expansion_factor or 1.0
        
        if adaptive_used:
            adaptive_count += 1
            
        attempts_distribution[attempts] = attempts_distribution.get(attempts, 0) + 1
        expansion_factors.append(exp_factor)
        
        # Expansion Factor Buckets
        if exp_factor <= 1.0: exp_distribution["1.0"] += 1
        elif exp_factor <= 1.5: exp_distribution["1.0-1.5"] += 1
        elif exp_factor <= 2.0: exp_distribution["1.5-2.0"] += 1
        elif exp_factor <= 3.0: exp_distribution["2.0-3.0"] += 1
        else: exp_distribution["> 3.0"] += 1
        
        timeline.append({
            "timestamp": log.timestamp.isoformat(),
            "adaptive_retrieval_used": adaptive_used,
            "retrieval_attempts": attempts,
            "evidence_expansion_factor": exp_factor
        })
        
    return {
        "total_retrieval_queries": total_retrieval,
        "adaptive_retrieval_count": adaptive_count,
        "adaptive_retrieval_percentage": round((adaptive_count / total_retrieval) * 100.0, 2),
        "retrieval_attempts_distribution": [{"attempts": k, "count": v} for k, v in attempts_distribution.items()],
        "avg_evidence_expansion_factor": round(sum(expansion_factors) / len(expansion_factors), 2),
        "expansion_factor_distribution": [{"range": k, "count": v} for k, v in exp_distribution.items()],
        "timeline": timeline
    }

@router.get("/latency")
def get_latency_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    total = len(logs)
    
    if total == 0:
        return {
            "avg_router_time_ms": 0.0,
            "avg_retriever_time_ms": 0.0,
            "avg_generator_time_ms": 0.0,
            "avg_verifier_time_ms": 0.0,
            "avg_total_time_ms": 0.0,
            "timeline": []
        }
        
    router_times = []
    retriever_times = []
    generator_times = []
    verifier_times = []
    total_times = []
    
    timeline = []
    
    for log in reversed(logs):
        meta = parse_metadata(log)
        
        router_t = float(meta.get("router_time_ms", 0))
        retriever_t = float(meta.get("retriever_time_ms", 0))
        generator_t = float(meta.get("generator_time_ms", 0))
        verifier_t = float(meta.get("verifier_time_ms", 0))
        
        total_t = router_t + retriever_t + generator_t + verifier_t
        
        router_times.append(router_t)
        retriever_times.append(retriever_t)
        generator_times.append(generator_t)
        verifier_times.append(verifier_t)
        total_times.append(total_t)
        
        timeline.append({
            "timestamp": log.timestamp.isoformat(),
            "router_time_ms": router_t,
            "retriever_time_ms": retriever_t,
            "generator_time_ms": generator_t,
            "verifier_time_ms": verifier_t,
            "total_time_ms": total_t
        })
        
    return {
        "avg_router_time_ms": round(sum(router_times) / total, 2),
        "avg_retriever_time_ms": round(sum(retriever_times) / total, 2),
        "avg_generator_time_ms": round(sum(generator_times) / total, 2),
        "avg_verifier_time_ms": round(sum(verifier_times) / total, 2),
        "avg_total_time_ms": round(sum(total_times) / total, 2),
        "timeline": timeline
    }

@router.get("/history")
def get_query_history(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> List[Dict[str, Any]]:
    logs = get_filtered_logs(repo, time_range)
    history_items = []
    
    for log in logs:
        meta = parse_metadata(log)
        route = meta.get("selected_route", "retrieval" if log.retrieved_count > 0 else "direct")
        
        history_items.append({
            "id": log.id,
            "query": log.query,
            "route": route,
            "verification_score": log.verification_score,
            "grounding_score": log.grounding_score,
            "adaptive_retrieval_used": bool(log.adaptive_retrieval_used),
            "timestamp": log.timestamp.isoformat()
        })
        
    return history_items

@router.get("/graph")
def get_graph_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    
    # 1. Scan SQLite logs
    graph_queries = 0
    hybrid_queries = 0
    graph_hits = 0
    total_graph_hits_queries = 0
    
    graph_v_scores = []
    graph_g_scores = []
    hybrid_v_scores = []
    hybrid_g_scores = []
    
    for log in logs:
        meta = parse_metadata(log)
        mode = meta.get("retrieval_mode", "vector")
        
        g_q = int(meta.get("graph_queries", 0))
        h_q = int(meta.get("hybrid_queries", 0))
        
        graph_queries += g_q
        hybrid_queries += h_q
        
        if mode == "graph":
            total_graph_hits_queries += 1
            if int(meta.get("graph_hits", 0)) > 0:
                graph_hits += 1
            v_sc = meta.get("graph_verification_score")
            g_sc = meta.get("graph_grounding_score")
            if v_sc is not None: graph_v_scores.append(float(v_sc))
            if g_sc is not None: graph_g_scores.append(float(g_sc))
        elif mode == "hybrid":
            v_sc = meta.get("hybrid_verification_score")
            g_sc = meta.get("hybrid_grounding_score")
            if v_sc is not None: hybrid_v_scores.append(float(v_sc))
            if g_sc is not None: hybrid_g_scores.append(float(g_sc))

    graph_hit_rate = round((graph_hits / total_graph_hits_queries) * 100.0, 2) if total_graph_hits_queries else 0.0

    # 2. Query Neo4j
    from app.services.graph.neo4j_service import Neo4jService
    neo4j = Neo4jService()
    
    neo4j_online = neo4j.health_check()
    entity_count = 0
    relationship_count = 0
    entity_growth = []
    relationship_growth = []

    if neo4j_online:
        try:
            e_res = neo4j.query_graph("MATCH (n:Entity) RETURN count(n) AS count")
            r_res = neo4j.query_graph(
                "MATCH ()-[r]->() WHERE NOT type(r) IN "
                "['CONTAINS', 'HAS_PAGE', 'HAS_CHUNK', 'MENTIONS'] RETURN count(r) AS count"
            )

            entity_count = e_res[0]["count"] if e_res else 0
            relationship_count = r_res[0]["count"] if r_res else 0

            e_growth = neo4j.query_graph("""
                MATCH (e:Entity)
                WHERE e.created_at IS NOT NULL
                RETURN substring(e.created_at, 0, 10) AS date, count(e) AS count
                ORDER BY date ASC
            """)
            r_growth = neo4j.query_graph("""
                MATCH ()-[r]->()
                WHERE r.created_at IS NOT NULL
                  AND NOT type(r) IN ['CONTAINS', 'HAS_PAGE', 'HAS_CHUNK', 'MENTIONS']
                RETURN substring(r.created_at, 0, 10) AS date, count(r) AS count
                ORDER BY date ASC
            """)

            cum_e = 0
            for item in e_growth:
                cum_e += item["count"]
                entity_growth.append({"range": item["date"], "count": cum_e})

            cum_r = 0
            for item in r_growth:
                cum_r += item["count"]
                relationship_growth.append({"range": item["date"], "count": cum_r})
        except Exception as ex:
            logger.warning(f"Error querying Neo4j growth metrics: {ex}")

    return {
        "neo4j_online": neo4j_online,
        "entity_count": entity_count,
        "relationship_count": relationship_count,
        "graph_queries": graph_queries,
        "hybrid_queries": hybrid_queries,
        "graph_hit_rate": graph_hit_rate,
        "verification_metrics": {
            "avg_graph_verification_score": round(sum(graph_v_scores) / len(graph_v_scores), 4) if graph_v_scores else 0.0,
            "avg_graph_grounding_score": round(sum(graph_g_scores) / len(graph_g_scores), 4) if graph_g_scores else 0.0,
            "avg_hybrid_verification_score": round(sum(hybrid_v_scores) / len(hybrid_v_scores), 4) if hybrid_v_scores else 0.0,
            "avg_hybrid_grounding_score": round(sum(hybrid_g_scores) / len(hybrid_g_scores), 4) if hybrid_g_scores else 0.0
        },
        "entity_growth": entity_growth,
        "relationship_growth": relationship_growth
    }

@router.get("/research")
def get_research_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    logs = get_filtered_logs(repo, time_range)
    total = len(logs)

    if total == 0:
        return {
            "avg_sub_questions": 0.0,
            "avg_evidence_count": 0.0,
            "avg_faithfulness": 0.0,
            "avg_answer_relevancy": 0.0,
            "avg_grounding": 0.0,
            "avg_verification": 0.0,
            "avg_planner_latency_ms": 0.0,
            "avg_research_latency_ms": 0.0,
            "avg_aggregation_latency_ms": 0.0,
            "timeline": []
        }

    sub_q_counts = []
    evidence_counts = []
    faithfulness_scores = []
    relevancy_scores = []
    grounding_scores = []
    verification_scores = []
    planner_latencies = []
    research_latencies = []
    aggregation_latencies = []

    timeline = []

    for log in reversed(logs):
        # Read column values. If None, default to metadata or default to 0.0/0
        meta = parse_metadata(log)
        
        sq_count = log.sub_question_count if log.sub_question_count is not None else int(meta.get("sub_question_count", 0))
        ev_count = log.evidence_count if log.evidence_count is not None else int(meta.get("evidence_count", log.retrieved_count or 0))
        
        # Latencies (saved in seconds, convert to ms)
        p_lat = (log.planner_latency if log.planner_latency is not None else float(meta.get("planner_time_ms", 0)) / 1000.0) * 1000.0
        r_lat = (log.research_latency if log.research_latency is not None else float(meta.get("retriever_time_ms", 0)) / 1000.0) * 1000.0
        a_lat = (log.aggregation_latency if log.aggregation_latency is not None else float(meta.get("aggregation_time_ms", 0)) / 1000.0) * 1000.0
        
        # Scores
        faith = log.faithfulness_score if log.faithfulness_score is not None else float(meta.get("faithfulness", 0.0))
        rel = log.answer_relevancy_score if log.answer_relevancy_score is not None else float(meta.get("answer_relevancy", 0.0))
        ground = log.grounding_score if log.grounding_score is not None else 0.0
        verif = log.verification_score if log.verification_score is not None else 0.0

        sub_q_counts.append(sq_count)
        evidence_counts.append(ev_count)
        faithfulness_scores.append(faith)
        relevancy_scores.append(rel)
        grounding_scores.append(ground)
        verification_scores.append(verif)
        planner_latencies.append(p_lat)
        research_latencies.append(r_lat)
        aggregation_latencies.append(a_lat)

        timeline.append({
            "timestamp": log.timestamp.isoformat(),
            "sub_question_count": sq_count,
            "evidence_count": ev_count,
            "faithfulness": faith,
            "answer_relevancy": rel,
            "grounding": ground,
            "verification": verif,
            "planner_latency": p_lat,
            "research_latency": r_lat,
            "aggregation_latency": a_lat
        })

    return {
        "avg_sub_questions": round(sum(sub_q_counts) / total, 2),
        "avg_evidence_count": round(sum(evidence_counts) / total, 2),
        "avg_faithfulness": round(sum(faithfulness_scores) / total, 4),
        "avg_answer_relevancy": round(sum(relevancy_scores) / total, 4),
        "avg_grounding": round(sum(grounding_scores) / total, 4),
        "avg_verification": round(sum(verification_scores) / total, 4),
        "avg_planner_latency_ms": round(sum(planner_latencies) / total, 2),
        "avg_research_latency_ms": round(sum(research_latencies) / total, 2),
        "avg_aggregation_latency_ms": round(sum(aggregation_latencies) / total, 2),
        "timeline": timeline
    }

@router.get("/deployment")
def get_deployment_analytics(
    time_range: str = Query("all", enum=["24h", "7d", "30d", "all"]),
    repo: EvaluationRepository = Depends(get_evaluation_repo)
) -> Dict[str, Any]:
    """Retrieves system deployment uptime, request volume, average latency, and RAG usage metrics."""
    logs = get_filtered_logs(repo, time_range)
    total_db_queries = len(logs)
    
    retrieval_modes = {"vector": 0, "graph": 0, "hybrid": 0}
    verification_stats = {"supported": 0, "partially_supported": 0, "unsupported": 0}
    deep_research_count = 0
    graph_usage_count = 0
    
    for log in logs:
        meta = parse_metadata(log)
        mode = meta.get("retrieval_mode", "vector")
        if mode in retrieval_modes:
            retrieval_modes[mode] += 1
            
        if mode in ["graph", "hybrid"] or int(meta.get("graph_queries", 0)) > 0 or int(meta.get("hybrid_queries", 0)) > 0:
            graph_usage_count += 1
            
        if log.research_depth is not None or meta.get("selected_route") == "deep_research":
            deep_research_count += 1
            
        status = (log.verification_status or "UNSUPPORTED").lower()
        if "partially" in status:
            verification_stats["partially_supported"] += 1
        elif "supported" in status:
            verification_stats["supported"] += 1
        else:
            verification_stats["unsupported"] += 1
            
    from app.monitoring.metrics_registry import metrics_registry
    summary = metrics_registry.get_metrics_summary()
    
    return {
        "uptime": round(summary["uptime_seconds"], 2),
        "request_count": summary["request_count"],
        "avg_latency": summary["average_latency_ms"],
        "retrieval_distribution": [
            {"name": "Vector RAG", "count": retrieval_modes["vector"]},
            {"name": "Graph RAG", "count": retrieval_modes["graph"]},
            {"name": "Hybrid RAG", "count": retrieval_modes["hybrid"]}
        ],
        "verification_distribution": [
            {"name": "Supported", "count": verification_stats["supported"]},
            {"name": "Partially Supported", "count": verification_stats["partially_supported"]},
            {"name": "Unsupported", "count": verification_stats["unsupported"]}
        ],
        "graph_usage": graph_usage_count,
        "deep_research_usage": deep_research_count,
        "total_queries": total_db_queries
    }

