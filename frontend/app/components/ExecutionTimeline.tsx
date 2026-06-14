import React from "react";
import { CheckCircle2, Clock, Activity, Zap, ShieldCheck } from "lucide-react";

interface ExecutionTimelineProps {
  activeQueryResponse?: any;
}

export default function ExecutionTimeline({ activeQueryResponse }: ExecutionTimelineProps) {
  if (!activeQueryResponse) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center select-none text-subtext/60">
        <Clock className="w-12 h-12 text-subtext/40 mb-3 animate-pulse" />
        <h4 className="text-sm font-semibold font-outfit text-subtext/80">No Active Execution</h4>
        <p className="text-[11px] mt-1 max-w-[200px]">
          Query metrics and agent timings will be visualized here.
        </p>
      </div>
    );
  }

  const meta = activeQueryResponse.execution_metadata || {};
  const isDeep = activeQueryResponse.research_depth === "deep" || meta.selected_route === "deep_research";
  
  // Latencies in ms
  const routerTime = meta.router_time_ms || 0;
  const plannerTime = meta.planner_time_ms || 0;
  const retrieverTime = meta.retriever_time_ms || 0;
  const aggregatorTime = meta.aggregation_time_ms || 0;
  const generatorTime = meta.generator_time_ms || 0;
  const verifierTime = meta.verifier_time_ms || 0;
  const totalTime = routerTime + plannerTime + retrieverTime + aggregatorTime + generatorTime + verifierTime;
  const modelName = meta.model_name || "gemini-2.5-flash";

  const steps = [
    {
      title: "1. Query Analysis & Routing",
      desc: `Analyzed incoming prompt. Selected route: "${meta.selected_route || "deep_research"}" (Confidence: ${((meta.route_confidence || 1.0) * 100).toFixed(0)}%)`,
      time: routerTime,
      active: true,
      success: routerTime > 0
    },
    ...(isDeep ? [{
      title: "2. Query Decomposing & Planning",
      desc: `Decomposed prompt into ${meta.sub_question_count || 0} sub-questions. Assigned search modes and research depth: ${meta.research_depth || "shallow"}.`,
      time: plannerTime,
      active: true,
      success: plannerTime > 0
    }] : []),
    {
      title: isDeep ? "3. Parallel Context Retrieval" : "2. Context Retrieval",
      desc: `Queried ChromaDB (Vector) and Neo4j (Graph) for relevant sources. Retrieved ${meta.retrieved_count || meta.evidence_count || 0} content chunks.`,
      time: retrieverTime,
      active: true,
      success: retrieverTime > 0
    },
    ...(isDeep ? [{
      title: "4. Evidence Synthesis & Aggregation",
      desc: "Deduplicated and merged retrieved source fragments into a unified evidence package.",
      time: aggregatorTime,
      active: true,
      success: aggregatorTime > 0
    }] : []),
    {
      title: isDeep ? "5. Answer Generation" : "3. Answer Generation",
      desc: `Invoked "${modelName}" model to synthesize a fact-grounded response using the aggregated sources.`,
      time: generatorTime,
      active: true,
      success: generatorTime > 0
    },
    {
      title: isDeep ? "6. Claim Verification" : "4. Claim Verification",
      desc: `Double-checked generated statements against context evidence. Score: ${((activeQueryResponse.verification_score || 0) * 100).toFixed(0)}%. Status: ${activeQueryResponse.verification_status || "SUPPORTED"}`,
      time: verifierTime,
      active: true,
      success: verifierTime > 0
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-white/5 select-none">
        <h3 className="text-xs font-bold text-primary uppercase tracking-widest font-outfit">
          Execution Trace & Timeline
        </h3>
      </div>

      {/* Timeline List */}
      <div className="relative pl-6 space-y-6 select-none before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-white/5">
        {steps.map((step, idx) => (
          <div key={idx} className="relative flex flex-col gap-1">
            {/* Dot connector */}
            <div className={`absolute -left-[20px] top-1.5 w-3 h-3 rounded-full flex items-center justify-center border-2 transition-all ${
              step.success
                ? "bg-success border-success shadow-[0_0_8px_#10b981]"
                : "bg-background border-white/10"
            }`}>
              {step.success && <div className="w-1 h-1 bg-white rounded-full" />}
            </div>

            {/* Header */}
            <div className="flex items-center justify-between gap-2">
              <span className={`text-[11px] font-bold font-outfit ${step.success ? "text-text" : "text-subtext/65"}`}>
                {step.title}
              </span>
              {step.time > 0 && (
                <span className="text-[9px] font-bold text-primary bg-primary/10 border border-primary/20 px-1.5 py-0.5 rounded-md">
                  {step.time} ms
                </span>
              )}
            </div>

            {/* Description */}
            <p className="text-[10px] text-subtext leading-relaxed font-medium">
              {step.desc}
            </p>
          </div>
        ))}
      </div>

      {totalTime > 0 && (
        <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-bold text-subtext/80 select-none">
          <span className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-primary" />
            Total Latency
          </span>
          <span className="text-primary">
            {(totalTime / 1000).toFixed(2)} seconds
          </span>
        </div>
      )}
    </div>
  );
}
