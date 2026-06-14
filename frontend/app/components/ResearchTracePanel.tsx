import React from "react";
import { Message } from "../../lib/api";
import { motion } from "framer-motion";
import {
  Shield,
  FileText,
  Clock,
  Sparkles,
  HelpCircle,
  TrendingUp,
  BrainCircuit,
  Search,
  Database,
  Layers
} from "lucide-react";

interface ResearchTracePanelProps {
  message: Message | null;
  activeQueryResponse?: any; // Contains the raw RAG response metadata for the active query
}

export default function ResearchTracePanel({ message, activeQueryResponse }: ResearchTracePanelProps) {
  if (!message) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center select-none text-subtext/60">
        <BrainCircuit className="w-12 h-12 text-subtext/40 mb-3 animate-pulse" />
        <h4 className="text-sm font-semibold font-outfit text-subtext/80">No Message Selected</h4>
        <p className="text-[11px] mt-1 max-w-[200px]">
          Click on any assistant response bubble to display its deep research trace.
        </p>
      </div>
    );
  }

  // Use values from activeQueryResponse if it matches this message content, else use defaults
  const data = activeQueryResponse || {};
  
  const subQuestions = data.sub_questions || [];
  const retrievalModes = data.retrieval_modes || [];
  const verificationScore = data.verification_score !== undefined ? data.verification_score : 0.0;
  const groundingScore = data.grounding_score !== undefined ? data.grounding_score : 0.0;
  const faithfulnessScore = data.faithfulness_score !== undefined ? data.faithfulness_score : 0.0;
  const answerRelevancyScore = data.answer_relevancy_score !== undefined ? data.answer_relevancy_score : 0.0;
  const verificationStatus = data.verification_status || "UNKNOWN";
  const researchDepth = data.research_depth || "shallow";
  const retrievalMode = data.retrieval_mode || "vector";
  const adaptiveUsed = data.adaptive_retrieval_used ? "Yes" : "No";

  // Summarize latencies
  const meta = data.execution_metadata || {};
  const totalTime = (meta.router_time_ms || 0) + (meta.planner_time_ms || 0) + 
                    (meta.retriever_time_ms || 0) + (meta.aggregation_time_ms || 0) + 
                    (meta.generator_time_ms || 0) + (meta.verifier_time_ms || 0);

  const getStatusBadge = (status: string) => {
    const s = (status || "").toUpperCase();
    if (s === "SUPPORTED") {
      return (
        <span className="text-[10px] font-bold bg-success/10 border border-success/20 text-success px-2 py-0.5 rounded-lg select-none">
          SUPPORTED
        </span>
      );
    }
    if (s === "PARTIALLY_SUPPORTED") {
      return (
        <span className="text-[10px] font-bold bg-warning/10 border border-warning/20 text-warning px-2 py-0.5 rounded-lg select-none">
          PARTIAL
        </span>
      );
    }
    return (
      <span className="text-[10px] font-bold bg-error/10 border border-error/20 text-error px-2 py-0.5 rounded-lg select-none">
        UNSUPPORTED
      </span>
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-success";
    if (score >= 0.5) return "text-warning";
    return "text-error";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-white/5 select-none">
        <h3 className="text-xs font-bold text-primary uppercase tracking-widest font-outfit">
          Multi-Agent Research Trace
        </h3>
        {totalTime > 0 && (
          <span className="flex items-center gap-1 text-[10px] text-subtext font-semibold">
            <Clock className="w-3.5 h-3.5 text-primary" />
            {(totalTime / 1000).toFixed(2)}s Latency
          </span>
        )}
      </div>

      <div className="space-y-4">
        {/* Verification Metrics Card */}
        <div className="bg-card border border-white/5 rounded-xl p-4 shadow-md glass-panel">
          <div className="flex items-center gap-2 text-[10px] font-bold text-subtext/60 uppercase tracking-wider mb-3 select-none">
            <Shield className="w-3.5 h-3.5 text-primary" />
            Verifier Agent Grounding Evaluation
          </div>

          <div className="space-y-2.5">
            {/* Verification Status */}
            <div className="flex justify-between items-center text-xs py-1 border-b border-white/5">
              <span className="text-subtext font-medium">Verifier Status</span>
              {getStatusBadge(verificationStatus)}
            </div>

            {/* Verification Score */}
            <div className="flex justify-between items-center text-xs py-1 border-b border-white/5">
              <span className="text-subtext font-medium">Verification Score</span>
              <span className={`font-bold ${getScoreColor(verificationScore)}`}>
                {(verificationScore * 100).toFixed(1)}%
              </span>
            </div>

            {/* Context Grounding */}
            <div className="flex justify-between items-center text-xs py-1 border-b border-white/5">
              <span className="text-subtext font-medium">Context Grounding</span>
              <span className="font-semibold text-text">
                {(groundingScore * 100).toFixed(1)}%
              </span>
            </div>

            {/* Faithfulness */}
            <div className="flex justify-between items-center text-xs py-1 border-b border-white/5">
              <span className="text-subtext font-medium">Faithfulness (Factuality)</span>
              <span className="font-semibold text-text">
                {(faithfulnessScore * 100).toFixed(1)}%
              </span>
            </div>

            {/* Answer Relevancy */}
            <div className="flex justify-between items-center text-xs py-1">
              <span className="text-subtext font-medium">Answer Relevancy</span>
              <span className="font-semibold text-text">
                {(answerRelevancyScore * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Planner Sub-Questions Card */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-[10px] font-bold text-subtext/60 uppercase tracking-wider px-1 select-none">
            <HelpCircle className="w-3.5 h-3.5 text-primary" />
            Planner Decomposed Sub-Questions ({subQuestions.length})
          </div>

          {subQuestions.length === 0 ? (
            <div className="text-xs text-subtext/60 italic px-2 py-3 bg-white/5 rounded-xl border border-white/5 text-center font-medium">
              No planning sub-questions recorded. Adaptive RAG was routed.
            </div>
          ) : (
            <div className="space-y-2">
              {subQuestions.map((q: string, idx: number) => {
                const mode = retrievalModes[idx] || "vector";
                return (
                  <div
                    key={idx}
                    className="p-3 bg-slate-900/40 border border-white/5 rounded-xl flex flex-col gap-1.5"
                  >
                    <div className="text-xs font-semibold text-text leading-relaxed font-outfit">
                      {q}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[8px] font-bold text-subtext/50 uppercase">Search Engine:</span>
                      <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded-md ${
                        mode === "hybrid"
                          ? "bg-primary/10 text-primary border border-primary/20"
                          : mode === "graph"
                          ? "bg-success/10 text-success border border-success/20"
                          : "bg-slate-800 text-slate-300"
                      }`}>
                        {mode}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Execution Metadata Card */}
        <div className="bg-card border border-white/5 rounded-xl p-4 shadow-md glass-panel">
          <div className="flex items-center gap-2 text-[10px] font-bold text-subtext/60 uppercase tracking-wider mb-3 select-none">
            <Layers className="w-3.5 h-3.5 text-primary" />
            System Retrieval Strategy
          </div>

          <div className="space-y-2.5">
            <div className="flex justify-between items-center text-xs py-1 border-b border-white/5">
              <span className="text-subtext font-medium">Research Depth</span>
              <span className="font-semibold text-text capitalize select-none">{researchDepth}</span>
            </div>

            <div className="flex justify-between items-center text-xs py-1 border-b border-white/5">
              <span className="text-subtext font-medium">Primary RAG Mode</span>
              <span className="font-semibold text-text uppercase select-none">{retrievalMode}</span>
            </div>

            <div className="flex justify-between items-center text-xs py-1">
              <span className="text-subtext font-medium">Adaptive Expansion</span>
              <span className="font-semibold text-text select-none">{adaptiveUsed}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
