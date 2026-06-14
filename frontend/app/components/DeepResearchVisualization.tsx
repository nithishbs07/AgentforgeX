import React from "react";
import { motion } from "framer-motion";
import {
  HelpCircle,
  GitCommit,
  Search,
  Database,
  PenTool,
  ShieldCheck,
  ArrowDown,
  Activity
} from "lucide-react";

interface DeepResearchVisualizationProps {
  activeQueryResponse?: any;
}

export default function DeepResearchVisualization({ activeQueryResponse }: DeepResearchVisualizationProps) {
  if (!activeQueryResponse) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center select-none text-subtext/60">
        <Activity className="w-12 h-12 text-subtext/40 mb-3 animate-pulse" />
        <h4 className="text-sm font-semibold font-outfit text-subtext/80">No Active Visualization</h4>
        <p className="text-[11px] mt-1 max-w-[200px]">
          LangGraph multi-agent RAG workflow diagram will be rendered here.
        </p>
      </div>
    );
  }

  const meta = activeQueryResponse.execution_metadata || {};
  const isDeep = activeQueryResponse.research_depth === "deep" || meta.selected_route === "deep_research";
  const route = meta.selected_route || "deep_research";
  const verificationStatus = activeQueryResponse.verification_status || "UNSUPPORTED";

  // Build the list of active workflow nodes
  const flowNodes = [
    {
      id: "input",
      icon: <HelpCircle className="w-4 h-4 text-indigo-400" />,
      title: "Input Query",
      desc: "Deconstructed user research intent",
      borderColor: "border-indigo-500/30 bg-indigo-500/5",
      titleColor: "text-indigo-300"
    },
    {
      id: "router",
      icon: <GitCommit className="w-4 h-4 text-violet-400" />,
      title: "Router Agent",
      desc: `Classification: "${route}"`,
      borderColor: "border-violet-500/30 bg-violet-500/5",
      titleColor: "text-violet-300"
    },
    ...(isDeep ? [
      {
        id: "planner",
        icon: <GitCommit className="w-4 h-4 text-pink-400" />,
        title: "Planner Agent",
        desc: `Split: ${meta.sub_question_count || 2} Sub-questions`,
        borderColor: "border-pink-500/30 bg-pink-500/5",
        titleColor: "text-pink-300"
      },
      {
        id: "retriever",
        icon: <Search className="w-4 h-4 text-emerald-400" />,
        title: "Research Executor",
        desc: "Vector + Graph parallel retrieval",
        borderColor: "border-emerald-500/30 bg-emerald-500/5",
        titleColor: "text-emerald-300"
      },
      {
        id: "evidence",
        icon: <Database className="w-4 h-4 text-amber-400" />,
        title: "Evidence Aggregator",
        desc: "Deduplicated context packages",
        borderColor: "border-amber-500/30 bg-amber-500/5",
        titleColor: "text-amber-300"
      }
    ] : [
      {
        id: "retriever",
        icon: <Search className="w-4 h-4 text-emerald-400" />,
        title: "Adaptive Retriever",
        desc: "Fast context database search",
        borderColor: "border-emerald-500/30 bg-emerald-500/5",
        titleColor: "text-emerald-300"
      }
    ]),
    {
      id: "generator",
      icon: <PenTool className="w-4 h-4 text-blue-400" />,
      title: "Generator Agent",
      desc: "Fact-grounded response synthesis",
      borderColor: "border-blue-500/30 bg-blue-500/5",
      titleColor: "text-blue-300"
    },
    {
      id: "verifier",
      icon: <ShieldCheck className="w-4 h-4 text-rose-400" />,
      title: "Verifier Agent",
      desc: `Status: ${verificationStatus}`,
      borderColor: verificationStatus === "SUPPORTED"
        ? "border-success/30 bg-success/5"
        : verificationStatus === "PARTIALLY_SUPPORTED"
        ? "border-warning/30 bg-warning/5"
        : "border-error/30 bg-error/5",
      titleColor: verificationStatus === "SUPPORTED"
        ? "text-success"
        : verificationStatus === "PARTIALLY_SUPPORTED"
        ? "text-warning"
        : "text-error"
    }
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-white/5 select-none">
        <h3 className="text-xs font-bold text-primary uppercase tracking-widest font-outfit">
          LangGraph RAG Workflow
        </h3>
      </div>
      
      <p className="text-[10px] text-subtext leading-relaxed font-medium mb-4 select-none">
        This visualization highlights the active agent-based execution workflow schema taken by AgentForge-X to resolve your query.
      </p>

      {/* Workflow nodes list */}
      <div className="flex flex-col items-center gap-2 relative">
        {flowNodes.map((node, idx) => {
          const isLast = idx === flowNodes.length - 1;

          return (
            <React.Fragment key={node.id}>
              {/* Card Node */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: idx * 0.05 }}
                whileHover={{ scale: 1.02 }}
                className={`w-full max-w-[260px] p-3 border rounded-xl flex items-center gap-3 shadow-md glass-panel glass-panel-hover ${node.borderColor}`}
              >
                <div className="w-8 h-8 rounded-lg bg-background/50 border border-white/5 flex items-center justify-center flex-shrink-0">
                  {node.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <div className={`text-xs font-bold font-outfit ${node.titleColor}`}>
                    {node.title}
                  </div>
                  <div className="text-[9px] text-subtext font-semibold truncate mt-0.5">
                    {node.desc}
                  </div>
                </div>
              </motion.div>

              {/* Arrow Connector */}
              {!isLast && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.4 }}
                  className="text-subtext flex items-center justify-center py-0.5 select-none"
                >
                  <ArrowDown className="w-3.5 h-3.5 text-primary/80 animate-bounce" />
                </motion.div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
