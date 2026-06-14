from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    query: str
    session_id: str
    route: str
    route_confidence: float
    retrieved_chunks: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    answer: str
    confidence_score: float
    verification_score: float
    grounding_score: float
    verification_status: str
    verification_reason: str
    verified: bool
    verification_attempts: int
    adaptive_retrieval_used: bool
    retrieval_attempts: int
    initial_retrieved_count: int
    final_retrieved_count: int
    evidence_expansion_factor: float
    adaptive_retrieval_reason: str
    verification_score_before_adaptation: float
    verification_score_after_adaptation: float
    verification_improvement: float
    retrieval_mode: str
    graph_entities: List[Dict[str, Any]]
    graph_relationships: List[Dict[str, Any]]
    graph_results: List[Dict[str, Any]]
    hybrid_used: bool
    graph_confidence: float
    graph_hit_count: int
    execution_metadata: Dict[str, Any]
    sub_questions: List[str]
    research_depth: str
    retrieval_modes: List[str]
    evidence_package: Dict[str, Any]
    planner_latency: float
    research_latency: float
    aggregation_latency: float
    faithfulness_score: float
    answer_relevancy_score: float

