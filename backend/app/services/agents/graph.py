from langgraph.graph import StateGraph, END
from app.services.agents.state import AgentState

def create_agent_graph(
    router = None,
    retriever = None,
    generator = None,
    verifier = None,
    adaptive_retriever = None,
    planner = None,
    research_executor = None,
    evidence_aggregator = None
):
    """
    Constructs the AgentForge-X graph.
    If router or adaptive_retriever is passed (or if planner and research_executor are both None),
    compiles the legacy routing-based workflow to maintain backward compatibility.
    Otherwise, compiles the new linear Deep Research workflow:
    START -> Planner -> Research Executor -> Evidence Aggregator -> Generator -> Verifier -> END
    """
    # Detect if legacy graph setup is requested
    is_legacy = (
        router is not None 
        or adaptive_retriever is not None 
        or (planner is None and research_executor is None)
    )

    if is_legacy:
        from app.services.agents.router_agent import RouterAgent
        from app.services.agents.retriever_agent import RetrieverAgent
        from app.services.agents.generator_agent import GeneratorAgent
        from app.services.agents.verifier_agent import VerifierAgent
        from app.services.agents.adaptive_retriever import AdaptiveRetriever

        router_agent = router or RouterAgent()
        retriever_agent = retriever or RetrieverAgent()
        generator_agent = generator or GeneratorAgent()
        verifier_agent = verifier or VerifierAgent()
        adaptive_retriever_agent = adaptive_retriever or AdaptiveRetriever()

        workflow = StateGraph(AgentState)

        # Register nodes
        workflow.add_node("router", router_agent.run)
        workflow.add_node("retriever", retriever_agent.run)
        workflow.add_node("generator", generator_agent.run)
        workflow.add_node("verifier", verifier_agent.run)
        workflow.add_node("adaptive_retriever", adaptive_retriever_agent.run)

        # Set entry
        workflow.set_entry_point("router")

        # Define legacy routing
        def select_route(state: AgentState) -> str:
            return state.get("route", "direct")

        workflow.add_conditional_edges(
            "router",
            select_route,
            {
                "direct": "generator",
                "vector": "retriever",
                "graph": "retriever",
                "hybrid": "retriever",
                "retrieval": "retriever"
            }
        )

        workflow.add_edge("retriever", "generator")
        workflow.add_edge("generator", "verifier")
        workflow.add_edge("adaptive_retriever", "generator")

        def check_verification(state: AgentState) -> str:
            reason = state.get("adaptive_retrieval_reason", "")
            attempts = state.get("retrieval_attempts", 1)
            if reason and attempts < 2 and state.get("route") != "direct":
                return "adaptive_retriever"
            return "end"

        workflow.add_conditional_edges(
            "verifier",
            check_verification,
            {
                "adaptive_retriever": "adaptive_retriever",
                "end": END
            }
        )

        return workflow.compile()

    else:
        # Build the new Deep Research workflow
        from app.services.agents.planner_agent import PlannerAgent
        from app.services.agents.research_executor import ResearchExecutor
        from app.services.agents.evidence_aggregator import EvidenceAggregator
        from app.services.agents.generator_agent import GeneratorAgent
        from app.services.agents.verifier_agent import VerifierAgent

        planner_agent = planner or PlannerAgent()
        executor_agent = research_executor or ResearchExecutor()
        aggregator_agent = evidence_aggregator or EvidenceAggregator()
        generator_agent = generator or GeneratorAgent()
        verifier_agent = verifier or VerifierAgent()

        workflow = StateGraph(AgentState)

        workflow.add_node("planner", planner_agent.run)
        workflow.add_node("research_executor", executor_agent.run)
        workflow.add_node("evidence_aggregator", aggregator_agent.run)
        workflow.add_node("generator", generator_agent.run)
        workflow.add_node("verifier", verifier_agent.run)

        workflow.set_entry_point("planner")

        workflow.add_edge("planner", "research_executor")
        workflow.add_edge("research_executor", "evidence_aggregator")
        workflow.add_edge("evidence_aggregator", "generator")
        workflow.add_edge("generator", "verifier")
        workflow.add_edge("verifier", END)

        return workflow.compile()

# Default compiled graph instance compiles the new Deep Research graph by default
from app.services.agents.planner_agent import PlannerAgent
from app.services.agents.research_executor import ResearchExecutor
from app.services.agents.evidence_aggregator import EvidenceAggregator
from app.services.agents.generator_agent import GeneratorAgent
from app.services.agents.verifier_agent import VerifierAgent

compiled_graph = create_agent_graph(
    planner=PlannerAgent(),
    research_executor=ResearchExecutor(),
    evidence_aggregator=EvidenceAggregator(),
    generator=GeneratorAgent(),
    verifier=VerifierAgent()
)
