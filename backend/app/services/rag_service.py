import time
import json
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
from app.core.config import settings
from app.repositories.session_repository import SessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.evaluation_repository import EvaluationRepository
from app.services.retrieval import BaseRetriever, ChromaRetriever
from app.services.generation_service import OllamaGenerationService
from app.models.models import Citation

# Import LangGraph Agent files
from app.services.agents.graph import create_agent_graph
from app.services.agents.planner_agent import PlannerAgent
from app.services.agents.research_executor import ResearchExecutor
from app.services.agents.evidence_aggregator import EvidenceAggregator
from app.services.agents.generator_agent import GeneratorAgent
from app.services.agents.verifier_agent import VerifierAgent
from app.services.evaluation.metrics import RAGEvaluator

# Import legacy agents
from app.services.agents.router_agent import RouterAgent
from app.services.agents.retriever_agent import RetrieverAgent
from app.services.agents.adaptive_retriever import AdaptiveRetriever

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(
        self,
        session_repo: SessionRepository,
        message_repo: MessageRepository,
        evaluation_repo: EvaluationRepository,
        retriever: BaseRetriever = None,
        generation_service: OllamaGenerationService = None
    ):
        self.session_repo = session_repo
        self.message_repo = message_repo
        self.evaluation_repo = evaluation_repo

        # Initialize the deep research agents
        self.planner_agent = PlannerAgent()
        self.research_executor = ResearchExecutor(retriever)
        self.evidence_aggregator = EvidenceAggregator()
        self.generator_agent = GeneratorAgent()
        self.verifier_agent = VerifierAgent()
        self.rag_evaluator = RAGEvaluator()

        # Initialize legacy agents for backward compatibility
        self.router_agent = RouterAgent()
        self.retriever_agent = RetrieverAgent(retriever)
        self.adaptive_retriever_agent = AdaptiveRetriever(retriever)

        # Propagate custom settings to all LLM-based agents if generation_service is custom
        if generation_service:
            for agent in [self.planner_agent, self.generator_agent, self.verifier_agent, self.rag_evaluator, self.router_agent]:
                if hasattr(agent, "base_url") and generation_service.base_url:
                    agent.base_url = generation_service.base_url
                if hasattr(agent, "model") and generation_service.model:
                    agent.model = generation_service.model

        # Compile BOTH workflows
        self.graph = create_agent_graph(
            planner=self.planner_agent,
            research_executor=self.research_executor,
            evidence_aggregator=self.evidence_aggregator,
            generator=self.generator_agent,
            verifier=self.verifier_agent
        )

        self.legacy_graph = create_agent_graph(
            router=self.router_agent,
            retriever=self.retriever_agent,
            generator=self.generator_agent,
            verifier=self.verifier_agent,
            adaptive_retriever=self.adaptive_retriever_agent
        )

        # Configuration flag
        self.use_deep_research = settings.USE_DEEP_RESEARCH

    def query_rag(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Invokes either the Deep Research pipeline or the Legacy Adaptive pipeline
        depending on settings.USE_DEEP_RESEARCH / self.use_deep_research.
        """
        session = self.session_repo.get(session_id)
        if not session:
            logger.error(f"RAG query failed: Session {session_id} not found.")
            raise ValueError(f"Session with ID {session_id} not found.")

        if not self.use_deep_research:
            # Setup initial AgentState structure for Legacy RAG
            initial_state = {
                "query": query,
                "session_id": session_id,
                "route": "direct",
                "route_confidence": 0.0,
                "retrieved_chunks": [],
                "citations": [],
                "answer": "",
                "confidence_score": 0.0,
                "verification_score": 0.0,
                "grounding_score": 0.0,
                "verification_status": "UNSUPPORTED",
                "verification_reason": "",
                "verified": False,
                "verification_attempts": 0,
                "adaptive_retrieval_used": False,
                "retrieval_attempts": 1,
                "initial_retrieved_count": 0,
                "final_retrieved_count": 0,
                "evidence_expansion_factor": 1.0,
                "adaptive_retrieval_reason": "",
                "verification_score_before_adaptation": 0.0,
                "verification_score_after_adaptation": 0.0,
                "verification_improvement": 0.0,
                "retrieval_mode": "vector",
                "graph_entities": [],
                "graph_relationships": [],
                "graph_results": [],
                "hybrid_used": False,
                "graph_confidence": 0.0,
                "graph_hit_count": 0,
                "execution_metadata": {
                    "selected_route": "direct",
                    "route_confidence": 0.0,
                    "retrieval_used": False,
                    "router_time_ms": 0,
                    "retriever_time_ms": 0,
                    "generator_time_ms": 0,
                    "verifier_time_ms": 0,
                    "grounding_score": 0.0,
                    "verification_score": 0.0,
                    "verification_status": "UNSUPPORTED",
                    "verification_attempts": 0,
                    "regenerated": False,
                    "adaptive_retrieval_used": False,
                    "adaptive_retrieval_reason": "",
                    "retrieval_attempts": 1,
                    "initial_retrieved_count": 0,
                    "final_retrieved_count": 0,
                    "evidence_expansion_factor": 1.0,
                    "verification_score_before_adaptation": 0.0,
                    "verification_score_after_adaptation": 0.0,
                    "verification_improvement": 0.0,
                    "retrieval_mode": "vector",
                    "graph_queries": 0,
                    "graph_hits": 0,
                    "hybrid_queries": 0,
                    "entity_count": 0,
                    "relationship_count": 0,
                    "graph_retrieval_latency": 0,
                    "hybrid_retrieval_latency": 0,
                    "graph_verification_score": 0.0,
                    "hybrid_verification_score": 0.0,
                    "graph_grounding_score": 0.0,
                    "hybrid_grounding_score": 0.0
                }
            }

            try:
                final_state = self.legacy_graph.invoke(initial_state)
            except Exception as e:
                logger.error(f"Legacy Agent Graph execution failed: {e}")
                raise e

            # Extract results
            answer = final_state.get("answer", "")
            confidence_score = final_state.get("confidence_score", 0.0)
            citations_resp = final_state.get("citations", [])
            retrieved_chunks = final_state.get("retrieved_chunks", [])
            exec_meta = final_state.get("execution_metadata", {})
            verification_score = final_state.get("verification_score", 0.0)
            grounding_score = final_state.get("grounding_score", 0.0)
            verification_status = final_state.get("verification_status", "UNSUPPORTED")
            adaptive_retrieval_used = final_state.get("adaptive_retrieval_used", False)
            retrieval_attempts = final_state.get("retrieval_attempts", 1)
            evidence_expansion_factor = final_state.get("evidence_expansion_factor", 1.0)
            verification_improvement = final_state.get("verification_improvement", 0.0)

            # Calculate online metrics
            faithfulness = self.rag_evaluator.calculate_faithfulness(answer, retrieved_chunks)
            relevancy = self.rag_evaluator.calculate_answer_relevancy(query, answer)
            context_precision = self.rag_evaluator.calculate_context_precision(query, retrieved_chunks)
            context_recall = self.rag_evaluator.calculate_context_recall(query, retrieved_chunks)
            retrieval_quality = self.rag_evaluator.calculate_retrieval_quality(query, retrieved_chunks)
            research_quality = self.rag_evaluator.calculate_research_quality(query, answer, retrieved_chunks)

            exec_meta["faithfulness"] = faithfulness
            exec_meta["answer_relevancy"] = relevancy
            exec_meta["context_precision"] = context_precision
            exec_meta["context_recall"] = context_recall
            exec_meta["retrieval_quality"] = retrieval_quality
            exec_meta["research_quality"] = research_quality

            # Compute stats
            scores = [chunk["similarity_score"] for chunk in retrieved_chunks]
            top_score = float(max(scores)) if scores else 0.0
            avg_score = float(sum(scores) / len(scores)) if scores else 0.0

            # Save Messages
            self.message_repo.create({"session_id": session_id, "role": "user", "content": query})
            assistant_msg = self.message_repo.create({"session_id": session_id, "role": "assistant", "content": answer})

            for chunk in retrieved_chunks:
                doc_id = chunk.get("document_id")
                page_num = chunk.get("page_number")
                citation_db = Citation(
                    message_id=assistant_msg.id,
                    document_id=doc_id if doc_id and doc_id.strip() else None,
                    page_number=page_num if page_num and page_num > 0 else None,
                    snippet=chunk.get("chunk_text", "")
                )
                self.message_repo.db.add(citation_db)
            self.message_repo.db.commit()

            session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.session_repo.db.add(session)
            self.session_repo.db.commit()

            retrieval_time = float(exec_meta.get("retriever_time_ms", 0)) / 1000.0
            generation_time = float(exec_meta.get("generator_time_ms", 0)) / 1000.0

            try:
                self.evaluation_repo.create({
                    "query": query,
                    "retrieved_chunks": json.dumps(retrieved_chunks),
                    "retrieved_count": len(retrieved_chunks),
                    "top_score": round(top_score, 4),
                    "avg_score": round(avg_score, 4),
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "execution_metadata": json.dumps(exec_meta),
                    "verification_score": verification_score,
                    "verification_status": verification_status,
                    "grounding_score": grounding_score,
                    "adaptive_retrieval_used": adaptive_retrieval_used,
                    "retrieval_attempts": retrieval_attempts,
                    "evidence_expansion_factor": evidence_expansion_factor,
                    "verification_improvement": verification_improvement
                })
            except Exception as eval_err:
                logger.error(f"Failed to write metrics to SQLite: {eval_err}")

            # Increment in-memory monitoring metrics
            try:
                from app.monitoring.metrics_registry import metrics_registry
                metrics_registry.increment_rag_metric(
                    retrieval=len(retrieved_chunks) > 0,
                    graph=final_state.get("retrieval_mode") in ["graph", "hybrid"],
                    verification=verification_score is not None,
                    deep_research=False
                )
            except Exception as e:
                logger.warning(f"Failed to increment legacy RAG metrics: {e}")

            return {
                "answer": answer,
                "confidence_score": confidence_score,
                "grounding_score": grounding_score,
                "verification_score": verification_score,
                "verification_status": verification_status,
                "adaptive_retrieval_used": adaptive_retrieval_used,
                "verification_improvement": verification_improvement,
                "citations": citations_resp,
                "retrieval_mode": final_state.get("retrieval_mode", "vector"),
                "graph_entities": final_state.get("graph_entities", []),
                "graph_relationships": final_state.get("graph_relationships", []),
                "hybrid_used": final_state.get("hybrid_used", False)
            }

        else:
            # Deep Research workflow
            initial_state = {
                "query": query,
                "session_id": session_id,
                "route": "deep_research",
                "route_confidence": 1.0,
                "retrieved_chunks": [],
                "citations": [],
                "answer": "",
                "confidence_score": 0.0,
                "verification_score": 0.0,
                "grounding_score": 0.0,
                "verification_status": "UNSUPPORTED",
                "verification_reason": "",
                "verified": False,
                "verification_attempts": 0,
                "adaptive_retrieval_used": False,
                "retrieval_attempts": 1,
                "initial_retrieved_count": 0,
                "final_retrieved_count": 0,
                "evidence_expansion_factor": 1.0,
                "adaptive_retrieval_reason": "",
                "verification_score_before_adaptation": 0.0,
                "verification_score_after_adaptation": 0.0,
                "verification_improvement": 0.0,
                "retrieval_mode": "hybrid",
                "graph_entities": [],
                "graph_relationships": [],
                "graph_results": [],
                "hybrid_used": True,
                "graph_confidence": 0.0,
                "graph_hit_count": 0,
                
                # Phase 8 state variables
                "sub_questions": [],
                "research_depth": "shallow",
                "retrieval_modes": [],
                "evidence_package": {},
                "planner_latency": 0.0,
                "research_latency": 0.0,
                "aggregation_latency": 0.0,
                "faithfulness_score": 0.0,
                "answer_relevancy_score": 0.0,

                "execution_metadata": {
                    "selected_route": "deep_research",
                    "route_confidence": 1.0,
                    "retrieval_used": True,
                    "planner_time_ms": 0,
                    "retriever_time_ms": 0,
                    "aggregation_time_ms": 0,
                    "generator_time_ms": 0,
                    "verifier_time_ms": 0,
                    "grounding_score": 0.0,
                    "verification_score": 0.0,
                    "verification_status": "UNSUPPORTED",
                    "verification_attempts": 0,
                    "retrieval_mode": "hybrid",
                    "graph_queries": 0,
                    "graph_hits": 0,
                    "hybrid_queries": 0,
                    "entity_count": 0,
                    "relationship_count": 0,
                    "evidence_count": 0,
                    "sub_question_count": 0,
                    "research_depth": "shallow"
                }
            }

            try:
                final_state = self.graph.invoke(initial_state)
            except Exception as e:
                logger.error(f"Agent Graph execution failed: {e}")
                raise e

            # Extract results
            answer = final_state.get("answer", "")
            confidence_score = final_state.get("confidence_score", 0.0)
            citations_resp = final_state.get("citations", [])
            retrieved_chunks = final_state.get("retrieved_chunks", [])
            exec_meta = final_state.get("execution_metadata", {})
            verification_score = final_state.get("verification_score", 0.0)
            grounding_score = final_state.get("grounding_score", 0.0)
            verification_status = final_state.get("verification_status", "UNSUPPORTED")
            
            # Calculate online metrics
            faithfulness = self.rag_evaluator.calculate_faithfulness(answer, retrieved_chunks)
            relevancy = self.rag_evaluator.calculate_answer_relevancy(query, answer)
            context_precision = self.rag_evaluator.calculate_context_precision(query, retrieved_chunks)
            context_recall = self.rag_evaluator.calculate_context_recall(query, retrieved_chunks)
            retrieval_quality = self.rag_evaluator.calculate_retrieval_quality(query, retrieved_chunks)
            research_quality = self.rag_evaluator.calculate_research_quality(query, answer, retrieved_chunks)

            exec_meta["faithfulness"] = faithfulness
            exec_meta["answer_relevancy"] = relevancy
            exec_meta["context_precision"] = context_precision
            exec_meta["context_recall"] = context_recall
            exec_meta["retrieval_quality"] = retrieval_quality
            exec_meta["research_quality"] = research_quality

            scores = [chunk["similarity_score"] for chunk in retrieved_chunks]
            top_score = float(max(scores)) if scores else 0.0
            avg_score = float(sum(scores) / len(scores)) if scores else 0.0

            # Save Messages
            self.message_repo.create({"session_id": session_id, "role": "user", "content": query})
            assistant_msg = self.message_repo.create({"session_id": session_id, "role": "assistant", "content": answer})

            for chunk in retrieved_chunks:
                doc_id = chunk.get("document_id")
                page_num = chunk.get("page_number")
                citation_db = Citation(
                    message_id=assistant_msg.id,
                    document_id=doc_id if doc_id and doc_id.strip() else None,
                    page_number=page_num if page_num and page_num > 0 else None,
                    snippet=chunk.get("chunk_text", "")
                )
                self.message_repo.db.add(citation_db)
            self.message_repo.db.commit()

            session.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.session_repo.db.add(session)
            self.session_repo.db.commit()

            retrieval_time = float(exec_meta.get("retriever_time_ms", 0) + exec_meta.get("aggregation_time_ms", 0)) / 1000.0
            generation_time = float(exec_meta.get("generator_time_ms", 0)) / 1000.0

            try:
                self.evaluation_repo.create({
                    "query": query,
                    "retrieved_chunks": json.dumps(retrieved_chunks),
                    "retrieved_count": len(retrieved_chunks),
                    "top_score": round(top_score, 4),
                    "avg_score": round(avg_score, 4),
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "execution_metadata": json.dumps(exec_meta),
                    "verification_score": verification_score,
                    "verification_status": verification_status,
                    "grounding_score": grounding_score,
                    "adaptive_retrieval_used": False,
                    "retrieval_attempts": 1,
                    "evidence_expansion_factor": 1.0,
                    "verification_improvement": 0.0,
                    
                    # Phase 8 columns
                    "planner_latency": final_state.get("planner_latency", 0.0),
                    "research_latency": final_state.get("research_latency", 0.0),
                    "aggregation_latency": final_state.get("aggregation_latency", 0.0),
                    "sub_question_count": len(final_state.get("sub_questions", [])),
                    "evidence_count": len(retrieved_chunks),
                    "research_depth": final_state.get("research_depth", "shallow"),
                    "faithfulness_score": faithfulness,
                    "answer_relevancy_score": relevancy
                })
            except Exception as eval_err:
                logger.error(f"Failed to write metrics to SQLite: {eval_err}")

            # Increment in-memory monitoring metrics
            try:
                from app.monitoring.metrics_registry import metrics_registry
                metrics_registry.increment_rag_metric(
                    retrieval=len(retrieved_chunks) > 0,
                    graph=any(mode in ["graph", "hybrid"] for mode in final_state.get("retrieval_modes", [])) or final_state.get("retrieval_mode") == "hybrid",
                    verification=verification_score is not None,
                    deep_research=True
                )
            except Exception as e:
                logger.warning(f"Failed to increment deep research metrics: {e}")

            return {
                "answer": answer,
                "confidence_score": confidence_score,
                "grounding_score": grounding_score,
                "verification_score": verification_score,
                "verification_status": verification_status,
                "adaptive_retrieval_used": False,
                "verification_improvement": 0.0,
                "citations": citations_resp,
                "retrieval_mode": final_state.get("retrieval_mode", "hybrid"),
                "graph_entities": final_state.get("graph_entities", []),
                "graph_relationships": final_state.get("graph_relationships", []),
                "hybrid_used": True,
                
                # Phase 8 keys
                "sub_questions": final_state.get("sub_questions", []),
                "research_depth": final_state.get("research_depth", "shallow"),
                "retrieval_modes": final_state.get("retrieval_modes", []),
                "faithfulness_score": faithfulness,
                "answer_relevancy_score": relevancy
            }
