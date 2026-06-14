"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { LineChart, BarChart, PieChart } from "../components/Charts";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  Clock,
  Sparkles,
  Shield,
  Database,
  Network,
  History,
  BarChart3,
  ArrowLeft,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Activity,
  Cpu,
  Layers,
  Award,
  Zap,
  CheckCircle,
  Search
} from "lucide-react";

// Configuration for API Host
const API_BASE = "http://127.0.0.1:8000/api/v1";

interface OverviewData {
  total_queries: number;
  supported_percentage: number;
  partially_supported_percentage: number;
  unsupported_percentage: number;
  adaptive_retrieval_trigger_rate: number;
  avg_verification_score: number;
  avg_grounding_score: number;
  avg_verification_improvement: number;
}

interface DistributionItem {
  range: string;
  count: number;
}

interface VerificationData {
  verification_distribution: DistributionItem[];
  grounding_distribution: DistributionItem[];
  improvement_distribution: DistributionItem[];
  timeline: {
    timestamp: string;
    verification_score: number;
    grounding_score: number;
    verification_improvement: number;
  }[];
}

interface RoutingData {
  direct_route_count: number;
  retrieval_route_count: number;
  direct_route_percentage: number;
  retrieval_route_percentage: number;
  confidence_distribution: DistributionItem[];
  timeline: {
    timestamp: string;
    route: string;
    confidence: number;
  }[];
}

interface RetrievalData {
  total_retrieval_queries: number;
  adaptive_retrieval_count: number;
  adaptive_retrieval_percentage: number;
  retrieval_attempts_distribution: { attempts: number; count: number }[];
  avg_evidence_expansion_factor: number;
  expansion_factor_distribution: DistributionItem[];
  timeline: {
    timestamp: string;
    adaptive_retrieval_used: boolean;
    retrieval_attempts: number;
    evidence_expansion_factor: number;
  }[];
}

interface LatencyData {
  avg_router_time_ms: number;
  avg_retriever_time_ms: number;
  avg_generator_time_ms: number;
  avg_verifier_time_ms: number;
  avg_total_time_ms: number;
  timeline: {
    timestamp: string;
    router_time_ms: number;
    retriever_time_ms: number;
    generator_time_ms: number;
    verifier_time_ms: number;
    total_time_ms: number;
  }[];
}

interface HistoryItem {
  id: string;
  query: string;
  route: string;
  verification_score: number;
  grounding_score: number;
  adaptive_retrieval_used: boolean;
  timestamp: string;
}

interface GraphData {
  neo4j_online: boolean;
  entity_count: number;
  relationship_count: number;
  graph_queries: number;
  hybrid_queries: number;
  graph_hit_rate: number;
  verification_metrics: {
    avg_graph_verification_score: number;
    avg_graph_grounding_score: number;
    avg_hybrid_verification_score: number;
    avg_hybrid_grounding_score: number;
  };
  entity_growth: { range: string; count: number }[];
  relationship_growth: { range: string; count: number }[];
}

interface ResearchData {
  avg_sub_questions: number;
  avg_evidence_count: number;
  avg_faithfulness: number;
  avg_answer_relevancy: number;
  avg_grounding: number;
  avg_verification: number;
  avg_planner_latency_ms: number;
  avg_research_latency_ms: number;
  avg_aggregation_latency_ms: number;
  timeline: {
    timestamp: string;
    sub_question_count: number;
    evidence_count: number;
    faithfulness: number;
    answer_relevancy: number;
    grounding: number;
    verification: number;
    planner_latency: number;
    research_latency: number;
    aggregation_latency: number;
  }[];
}

interface DeploymentData {
  uptime: number;
  request_count: number;
  avg_latency: number;
  retrieval_distribution: { name: string; count: number }[];
  verification_distribution: { name: string; count: number }[];
  graph_usage: number;
  deep_research_usage: number;
  total_queries: number;
}

export default function Dashboard() {
  const [filter, setFilter] = useState<string>("all");
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // States for fetched analytics data
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [verification, setVerification] = useState<VerificationData | null>(null);
  const [routing, setRouting] = useState<RoutingData | null>(null);
  const [retrieval, setRetrieval] = useState<RetrievalData | null>(null);
  const [latency, setLatency] = useState<LatencyData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [graphMetrics, setGraphMetrics] = useState<GraphData | null>(null);
  const [research, setResearch] = useState<ResearchData | null>(null);
  const [deployment, setDeployment] = useState<DeploymentData | null>(null);

  const fetchData = async (selectedFilter: string) => {
    setLoading(true);
    setError(null);
    try {
      const endpoints = [
        `/analytics/overview?time_range=${selectedFilter}`,
        `/analytics/verification?time_range=${selectedFilter}`,
        `/analytics/routing?time_range=${selectedFilter}`,
        `/analytics/retrieval?time_range=${selectedFilter}`,
        `/analytics/latency?time_range=${selectedFilter}`,
        `/analytics/history?time_range=${selectedFilter}`,
        `/analytics/graph?time_range=${selectedFilter}`,
        `/analytics/research?time_range=${selectedFilter}`,
        `/analytics/deployment?time_range=${selectedFilter}`
      ];

      const responses = await Promise.all(
        endpoints.map(ep => fetch(`${API_BASE}${ep}`).then(async res => {
          if (!res.ok) throw new Error(`API failed on ${ep}`);
          return res.json();
        }))
      );

      setOverview(responses[0]);
      setVerification(responses[1]);
      setRouting(responses[2]);
      setRetrieval(responses[3]);
      setLatency(responses[4]);
      setHistory(responses[5]);
      setGraphMetrics(responses[6]);
      setResearch(responses[7]);
      setDeployment(responses[8]);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch analytics metrics from the database. Make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(filter);
  }, [filter]);

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } }
  };

  return (
    <div className="min-h-screen bg-background text-text flex flex-col font-sans">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center p-6 border-b border-white/5 justify-between gap-4 sticky top-0 z-30 bg-card/60 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-primary to-indigo-700 w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white text-base shadow-lg shadow-primary/20">
            AF
          </div>
          <div>
            <h1 className="text-base font-bold font-outfit tracking-tight">
              AgentForge-X <span className="text-primary text-xs font-semibold ml-2">v1.5 Observability</span>
            </h1>
            <p className="text-[10px] text-subtext mt-0.5">Multi-Agent RAG Evaluation & Diagnostics</p>
          </div>
        </div>
        
        {/* Navigation / Filters */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-subtext hover:text-white transition-colors py-2 px-3 hover:bg-white/5 rounded-xl border border-white/5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Chat
          </Link>
          
          <div className="flex bg-[#111827] rounded-xl p-0.5 border border-white/5">
            {["24h", "7d", "30d", "all"].map((t) => (
              <button
                key={t}
                onClick={() => setFilter(t)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all duration-150 capitalize ${
                  filter === t
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-subtext/75 hover:text-text"
                }`}
              >
                {t === "all" ? "All Time" : t === "24h" ? "24h" : `${t}`}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Navigation tabs */}
      <nav className="flex px-6 overflow-x-auto border-b border-white/5 gap-6 bg-[#111827]/20 select-none">
        {[
          { id: "overview", label: "Overview", icon: <BarChart3 className="w-3.5 h-3.5" /> },
          { id: "research", label: "Research Analytics", icon: <BrainCircuitIcon className="w-3.5 h-3.5" /> },
          { id: "deployment", label: "Deployment Metrics", icon: <Activity className="w-3.5 h-3.5" /> },
          { id: "verification", label: "Verification", icon: <Shield className="w-3.5 h-3.5" /> },
          { id: "routing", label: "Routing", icon: <Zap className="w-3.5 h-3.5" /> },
          { id: "retrieval", label: "Retrieval", icon: <Search className="w-3.5 h-3.5" /> },
          { id: "graph", label: "Knowledge Graph", icon: <Network className="w-3.5 h-3.5" /> },
          { id: "latency", label: "Latency", icon: <Clock className="w-3.5 h-3.5" /> },
          { id: "history", label: "Query History", icon: <History className="w-3.5 h-3.5" /> }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 py-4 px-1 text-[11px] font-bold uppercase tracking-wider border-b-2 transition-colors duration-150 flex-shrink-0 ${
              activeTab === tab.id
                ? "text-primary border-primary"
                : "text-subtext/60 border-transparent hover:text-text"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {error && (
          <div className="bg-error/10 border border-error/20 rounded-xl p-4 text-xs text-error/90 font-medium mb-6">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <div className="w-10 h-10 border-2 border-slate-800 border-t-primary rounded-full animate-spin" />
            <p className="text-xs text-subtext/80 animate-pulse font-medium">Loading evaluation metrics...</p>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              variants={containerVariants}
              initial="hidden"
              animate="show"
              className="space-y-6"
            >
              {/* DEPLOYMENT METRICS TAB */}
              {activeTab === "deployment" && deployment && (
                <div className="space-y-6">
                  {/* Metric cards grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    <DashboardCard
                      title="System Uptime"
                      value={
                        deployment.uptime > 3600
                          ? `${Math.floor(deployment.uptime / 3600)}h ${Math.floor((deployment.uptime % 3600) / 60)}m`
                          : `${Math.floor(deployment.uptime / 60)}m ${Math.floor(deployment.uptime % 60)}s`
                      }
                      subtitle="Server duration online"
                      color="text-success"
                      icon={<Clock className="w-4 h-4 text-success" />}
                    />
                    <DashboardCard
                      title="Request Count"
                      value={deployment.request_count.toString()}
                      subtitle="Total API requests"
                      color="text-primary"
                      icon={<Activity className="w-4 h-4 text-primary" />}
                    />
                    <DashboardCard
                      title="Avg Request Latency"
                      value={`${deployment.avg_latency.toFixed(1)} ms`}
                      subtitle="Server response speed"
                      color="text-blue-400"
                      icon={<Zap className="w-4 h-4 text-blue-400" />}
                    />
                    <DashboardCard
                      title="Deep Research Runs"
                      value={deployment.deep_research_usage.toString()}
                      subtitle="Multi-agent graph runs"
                      color="text-indigo-400"
                      icon={<Sparkles className="w-4 h-4 text-indigo-400" />}
                    />
                    <DashboardCard
                      title="Graph Database Usage"
                      value={deployment.graph_usage.toString()}
                      subtitle="Neo4j interactions"
                      color="text-warning"
                      icon={<Network className="w-4 h-4 text-warning" />}
                    />
                  </div>

                  {/* Deployment charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Retrieval Strategy Distribution
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">RAG database fetches by strategy</p>
                      <div className="flex justify-center p-2">
                        <PieChart data={deployment.retrieval_distribution.map(item => ({
                          name: item.name,
                          value: item.count,
                          color: item.name === "Vector RAG" ? "#3b82f6" : (item.name === "Graph RAG" ? "#10b981" : "#f59e0b")
                        }))} />
                      </div>
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Verification Support Breakdown
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Factual alignment status rates</p>
                      <div className="flex justify-center p-2">
                        <PieChart data={deployment.verification_distribution.map(item => ({
                          name: item.name,
                          value: item.count,
                          color: item.name === "Supported" ? "#10b981" : (item.name === "Partially Supported" ? "#f59e0b" : "#ef4444")
                        }))} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* RESEARCH ANALYTICS TAB */}
              {activeTab === "research" && research && (
                <div className="space-y-6">
                  {/* Metric cards grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                    <DashboardCard
                      title="Avg Sub-Questions"
                      value={research.avg_sub_questions.toString()}
                      subtitle="Query decomposition factor"
                      color="text-primary"
                      icon={<Layers className="w-4 h-4 text-primary" />}
                    />
                    <DashboardCard
                      title="Avg Evidence Count"
                      value={research.avg_evidence_count.toString()}
                      subtitle="Retrieved chunks per query"
                      color="text-blue-400"
                      icon={<Database className="w-4 h-4 text-blue-400" />}
                    />
                    <DashboardCard
                      title="Faithfulness"
                      value={`${Math.round(research.avg_faithfulness * 100)}%`}
                      subtitle="Grounded in facts"
                      color="text-success"
                      icon={<CheckCircle className="w-4 h-4 text-success" />}
                    />
                    <DashboardCard
                      title="Answer Relevancy"
                      value={`${Math.round(research.avg_answer_relevancy * 100)}%`}
                      subtitle="Addressing prompt directly"
                      color="text-warning"
                      icon={<Award className="w-4 h-4 text-warning" />}
                    />
                    <DashboardCard
                      title="Verification Score"
                      value={`${Math.round(research.avg_verification * 100)}%`}
                      subtitle="Factual truthfulness"
                      color="text-indigo-400"
                      icon={<Shield className="w-4 h-4 text-indigo-400" />}
                    />
                    <DashboardCard
                      title="Grounding Score"
                      value={`${Math.round(research.avg_grounding * 100)}%`}
                      subtitle="Semantic context overlap"
                      color="text-pink-400"
                      icon={<TrendingUp className="w-4 h-4 text-pink-400" />}
                    />
                  </div>

                  {/* Latency breakdowns card grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-card border border-white/5 p-4 rounded-xl shadow-md glass-panel flex flex-col justify-between">
                      <span className="text-[10px] font-bold text-subtext/60 uppercase tracking-wider">Avg Planner Latency</span>
                      <div className="text-lg font-bold text-error/90 font-outfit mt-1">{research.avg_planner_latency_ms.toFixed(1)} ms</div>
                    </div>
                    <div className="bg-card border border-white/5 p-4 rounded-xl shadow-md glass-panel flex flex-col justify-between">
                      <span className="text-[10px] font-bold text-subtext/60 uppercase tracking-wider">Avg Research Executor Latency</span>
                      <div className="text-lg font-bold text-blue-400 font-outfit mt-1">{research.avg_research_latency_ms.toFixed(1)} ms</div>
                    </div>
                    <div className="bg-card border border-white/5 p-4 rounded-xl shadow-md glass-panel flex flex-col justify-between">
                      <span className="text-[10px] font-bold text-subtext/60 uppercase tracking-wider">Avg Evidence Aggregator Latency</span>
                      <div className="text-lg font-bold text-primary font-outfit mt-1">{research.avg_aggregation_latency_ms.toFixed(1)} ms</div>
                    </div>
                  </div>

                  {/* Research Charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Evaluation Quality Scores Timeline
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Faithfulness, Relevancy, Verification, and Grounding timeline</p>
                      <LineChart
                        data={research.timeline}
                        xKey="timestamp"
                        yKeys={["faithfulness", "answer_relevancy", "verification", "grounding"]}
                        colors={["#10b981", "#f59e0b", "#6366f1", "#06b6d4"]}
                      />
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Deep Research Node Latency Timeline
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Speed (ms) of planner, research executor, and aggregator nodes</p>
                      <LineChart
                        data={research.timeline}
                        xKey="timestamp"
                        yKeys={["planner_latency", "research_latency", "aggregation_latency"]}
                        colors={["#f43f5e", "#3b82f6", "#a855f7"]}
                      />
                    </div>
                  </div>
                </div>
              )}
              
              {/* OVERVIEW TAB */}
              {activeTab === "overview" && overview && (
                <div className="space-y-6">
                  {/* Metric cards grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    <DashboardCard
                      title="Total Queries"
                      value={overview.total_queries.toString()}
                      subtitle="Logged user queries"
                      color="text-text"
                      icon={<FileText className="w-4 h-4 text-subtext" />}
                    />
                    <DashboardCard
                      title="Supported Answers"
                      value={`${overview.supported_percentage}%`}
                      subtitle="Fully grounded responses"
                      color="text-success"
                      icon={<CheckCircle2 className="w-4 h-4 text-success" />}
                    />
                    <DashboardCard
                      title="Partially Supported"
                      value={`${overview.partially_supported_percentage}%`}
                      subtitle="Partial grounding matches"
                      color="text-warning"
                      icon={<AlertTriangle className="w-4 h-4 text-warning" />}
                    />
                    <DashboardCard
                      title="Unsupported (Hallucinations)"
                      value={`${overview.unsupported_percentage}%`}
                      subtitle="High-risk response runs"
                      color="text-error"
                      icon={<Shield className="w-4 h-4 text-error" />}
                    />
                    <DashboardCard
                      title="Adaptive Retrieval Rate"
                      value={`${overview.adaptive_retrieval_trigger_rate}%`}
                      subtitle="Triggered double lookup"
                      color="text-blue-400"
                      icon={<TrendingUp className="w-4 h-4 text-blue-400" />}
                    />
                  </div>

                  {/* Overview charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Verification Grounding Timeline
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Verification scores and improvements timeline</p>
                      {verification && (
                        <LineChart
                          data={verification.timeline}
                          xKey="timestamp"
                          yKeys={["verification_score", "grounding_score", "verification_improvement"]}
                          colors={["#6366f1", "#10b981", "#06b6d4"]}
                        />
                      )}
                    </div>
                    
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Evaluation Status Distribution
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Final verification status breakdown</p>
                      <div className="flex justify-center p-2">
                        <PieChart data={[
                          { name: "Supported", value: overview.supported_percentage, color: "#10b981" },
                          { name: "Partially Supported", value: overview.partially_supported_percentage, color: "#f59e0b" },
                          { name: "Unsupported", value: overview.unsupported_percentage, color: "#ef4444" }
                        ]} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* VERIFICATION TAB */}
              {activeTab === "verification" && verification && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Verification Score Distribution
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Count of query responses in score brackets</p>
                      <BarChart data={verification.verification_distribution} color="#6366f1" />
                    </div>
                    
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Grounding Score Distribution
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Semantic context grounding score frequency</p>
                      <BarChart data={verification.grounding_distribution} color="#10b981" />
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Verification Improvement
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Score delta increase after adaptive retrieval</p>
                      <BarChart data={verification.improvement_distribution} color="#06b6d4" />
                    </div>
                  </div>

                  <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                    <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-3">
                      Verification & Grounding Detailed Timeline
                    </h3>
                    <LineChart
                      data={verification.timeline}
                      xKey="timestamp"
                      yKeys={["verification_score", "grounding_score"]}
                      colors={["#8b5cf6", "#10b981"]}
                    />
                  </div>
                </div>
              )}

              {/* ROUTING TAB */}
              {activeTab === "routing" && routing && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Route Choices
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Routing decisions (Direct vs. Retrieval-Augmented)</p>
                      <div className="flex justify-center p-4">
                        <PieChart data={[
                          { name: "Direct Route", value: routing.direct_route_count, color: "#ef4444" },
                          { name: "Retrieval Route", value: routing.retrieval_route_count, color: "#6366f1" }
                        ]} />
                      </div>
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Router Classifier Confidence
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Frequency of router confidence score bands</p>
                      <BarChart data={routing.confidence_distribution} color="#f59e0b" />
                    </div>
                  </div>

                  <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                    <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-3">
                      Route Confidence Timeline
                    </h3>
                    <LineChart
                      data={routing.timeline}
                      xKey="timestamp"
                      yKeys={["confidence"]}
                      colors={["#f59e0b"]}
                    />
                  </div>
                </div>
              )}

              {/* RETRIEVAL TAB */}
              {activeTab === "retrieval" && retrieval && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Retrieval Attempts
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">First-run search vs. Adaptive second-run search</p>
                      <div className="flex justify-center p-2">
                        <PieChart data={retrieval.retrieval_attempts_distribution.map(item => ({
                          name: item.attempts === 1 ? "1 Attempt (Sufficient)" : "2 Attempts (Adaptive)",
                          value: item.count,
                          color: item.attempts === 1 ? "#10b981" : "#06b6d4"
                        }))} />
                      </div>
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Evidence Expansion Distribution
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Ratio of final retrieved chunks to initial count</p>
                      <BarChart data={retrieval.expansion_factor_distribution} color="#06b6d4" />
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel flex flex-col justify-between">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-4">
                        Retrieval Summary
                      </h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center pb-2 border-b border-white/5 text-xs">
                          <span className="text-subtext font-medium">Avg Evidence Expansion:</span>
                          <span className="font-bold text-blue-400 text-sm">{retrieval.avg_evidence_expansion_factor}x</span>
                        </div>
                        <div className="flex justify-between items-center pb-2 border-b border-white/5 text-xs">
                          <span className="text-subtext font-medium">Adaptive Retrieval Usage:</span>
                          <span className="font-bold text-primary text-sm">{retrieval.adaptive_retrieval_percentage}%</span>
                        </div>
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-subtext font-medium">Total Retrieval Queries:</span>
                          <span className="font-bold text-text text-sm">{retrieval.total_retrieval_queries}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                    <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-3">
                      Evidence Expansion Factor Timeline
                    </h3>
                    <LineChart
                      data={retrieval.timeline}
                      xKey="timestamp"
                      yKeys={["evidence_expansion_factor"]}
                      colors={["#38bdf8"]}
                    />
                  </div>
                </div>
              )}

              {/* LATENCY TAB */}
              {activeTab === "latency" && latency && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <DashboardCard
                      title="Avg Router Time"
                      value={`${latency.avg_router_time_ms} ms`}
                      subtitle="Query routing latency"
                      color="text-warning"
                      icon={<Clock className="w-4 h-4 text-warning" />}
                    />
                    <DashboardCard
                      title="Avg Retriever Time"
                      value={`${latency.avg_retriever_time_ms} ms`}
                      subtitle="ChromaDB / Neo4j speed"
                      color="text-blue-400"
                      icon={<Search className="w-4 h-4 text-blue-400" />}
                    />
                    <DashboardCard
                      title="Avg Generator Time"
                      value={`${latency.avg_generator_time_ms} ms`}
                      subtitle="Gemini draft synthesis speed"
                      color="text-primary"
                      icon={<PenToolIcon className="w-4 h-4 text-primary" />}
                    />
                    <DashboardCard
                      title="Avg Verifier Time"
                      value={`${latency.avg_verifier_time_ms} ms`}
                      subtitle="Fact-checking assertion speed"
                      color="text-success"
                      icon={<Shield className="w-4 h-4 text-success" />}
                    />
                    <DashboardCard
                      title="Avg Total Execution"
                      value={`${latency.avg_total_time_ms} ms`}
                      subtitle="Complete agent graph latency"
                      color="text-text"
                      icon={<Zap className="w-4 h-4 text-white" />}
                    />
                  </div>

                  <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                    <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                      Execution Node Latency Timeline
                    </h3>
                    <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Track execution speeds for individual graph nodes over time (ms)</p>
                    <LineChart
                      data={latency.timeline}
                      xKey="timestamp"
                      yKeys={["router_time_ms", "retriever_time_ms", "generator_time_ms", "verifier_time_ms"]}
                      colors={["#f59e0b", "#38bdf8", "#a855f7", "#10b981"]}
                    />
                  </div>
                </div>
              )}

              {/* QUERY HISTORY TAB */}
              {activeTab === "history" && (
                <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                  <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                    Evaluation Log Query History
                  </h3>
                  <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Real-time evaluation logs fetched from SQLite</p>
                  
                  <div className="overflow-x-auto rounded-xl border border-white/5">
                    <table className="w-full text-xs border-collapse">
                      <thead>
                        <tr className="bg-slate-900 border-b border-white/5 text-subtext font-bold text-left select-none uppercase tracking-wider text-[9px]">
                          <th className="p-3.5 pl-4">Query</th>
                          <th className="p-3.5">Route</th>
                          <th className="p-3.5">Verification</th>
                          <th className="p-3.5">Grounding</th>
                          <th className="p-3.5">Adaptive</th>
                          <th className="p-3.5 pr-4">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody>
                        {history.map((item) => (
                          <tr key={item.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="p-3.5 pl-4 text-text font-medium max-w-[280px] truncate" title={item.query}>
                              {item.query}
                            </td>
                            <td className="p-3.5 select-none">
                              <span className={`px-2 py-0.5 rounded-lg text-[9px] font-bold uppercase ${
                                item.route === "direct"
                                  ? "bg-error/15 text-error border border-error/20"
                                  : "bg-primary/15 text-primary border border-primary/20"
                              }`}>
                                {item.route}
                              </span>
                            </td>
                            <td className="p-3.5 font-bold font-mono">
                              {item.verification_score !== null ? item.verification_score.toFixed(3) : "-"}
                            </td>
                            <td className="p-3.5 font-semibold font-mono text-subtext">
                              {item.grounding_score !== null ? item.grounding_score.toFixed(3) : "-"}
                            </td>
                            <td className="p-3.5 select-none font-semibold text-subtext/80">
                              {item.adaptive_retrieval_used ? (
                                <span className="text-blue-400">Yes (2 Runs)</span>
                              ) : (
                                <span>No (1 Run)</span>
                              )}
                            </td>
                            <td className="p-3.5 pr-4 text-subtext/50 font-semibold select-none">
                              {new Date(item.timestamp).toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* KNOWLEDGE GRAPH TAB */}
              {activeTab === "graph" && graphMetrics && (
                <div className="space-y-6">
                  {/* Neo4j Status Alert */}
                  <div className={`flex items-center p-4 rounded-xl border text-xs font-bold tracking-tight gap-2 shadow-md ${
                    graphMetrics.neo4j_online
                      ? "bg-success/10 border-success/20 text-success"
                      : "bg-error/10 border-error/20 text-error"
                  }`}>
                    <span className={`w-2 h-2 rounded-full ${graphMetrics.neo4j_online ? "bg-success animate-pulse" : "bg-error"}`} />
                    Neo4j Graph Database: {graphMetrics.neo4j_online ? "ONLINE (Connected)" : "OFFLINE (Vector Fallback Active)"}
                  </div>

                  {/* Metric cards grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                    <DashboardCard
                      title="Total Entities"
                      value={graphMetrics.entity_count.toString()}
                      subtitle="Knowledge Graph Nodes"
                      color="text-success"
                      icon={<Network className="w-4 h-4 text-success" />}
                    />
                    <DashboardCard
                      title="Total Relationships"
                      value={graphMetrics.relationship_count.toString()}
                      subtitle="Semantic Edges"
                      color="text-primary"
                      icon={<TrendingUp className="w-4 h-4 text-primary" />}
                    />
                    <DashboardCard
                      title="Graph Queries"
                      value={graphMetrics.graph_queries.toString()}
                      subtitle="Graph Traversal runs"
                      color="text-indigo-400"
                      icon={<Layers className="w-4 h-4 text-indigo-400" />}
                    />
                    <DashboardCard
                      title="Hybrid Queries"
                      value={graphMetrics.hybrid_queries.toString()}
                      subtitle="Vector + Graph RAG Combined"
                      color="text-blue-400"
                      icon={<Database className="w-4 h-4 text-blue-400" />}
                    />
                    <DashboardCard
                      title="Graph Hit Rate"
                      value={`${graphMetrics.graph_hit_rate}%`}
                      subtitle="Traversal success rate"
                      color="text-success"
                      icon={<Award className="w-4 h-4 text-success" />}
                    />
                  </div>

                  {/* Graph Analytics Charts */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Knowledge Graph Growth
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Extracted Entities & Relationships over time</p>
                      {(() => {
                        const dates = new Set<string>();
                        graphMetrics.entity_growth?.forEach((d: any) => dates.add(d.range));
                        graphMetrics.relationship_growth?.forEach((d: any) => dates.add(d.range));
                        
                        const sortedDates = Array.from(dates).sort();
                        
                        let currentEntities = 0;
                        let currentRelations = 0;
                        
                        const merged = sortedDates.map(date => {
                          const eItem = graphMetrics.entity_growth?.find((d: any) => d.range === date);
                          const rItem = graphMetrics.relationship_growth?.find((d: any) => d.range === date);
                          
                          if (eItem) currentEntities = eItem.count;
                          if (rItem) currentRelations = rItem.count;
                          
                          return {
                            range: date,
                            entities: currentEntities,
                            relationships: currentRelations
                          };
                        });

                        const chartData = merged.length > 0 ? merged : [
                          { range: "No Data Available", entities: 0, relationships: 0 }
                        ];

                        return (
                          <LineChart
                            data={chartData}
                            xKey="range"
                            yKeys={["entities", "relationships"]}
                            colors={["#10b981", "#a855f7"]}
                          />
                        );
                      })()}
                    </div>

                    <div className="bg-card border border-white/5 p-6 rounded-2xl shadow-md glass-panel">
                      <h3 className="text-xs font-bold font-outfit uppercase tracking-widest text-text mb-1">
                        Retrieval Strategy Accuracy Comparison
                      </h3>
                      <p className="text-[10px] text-subtext/70 mb-4 font-semibold">Verification and grounding comparisons</p>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-slate-900 border border-white/5 rounded-xl">
                          <span className="text-[9px] font-bold text-subtext/50 uppercase tracking-widest block">Graph RAG Verification</span>
                          <span className="text-xl font-bold font-mono text-primary block mt-1.5">
                            {graphMetrics.verification_metrics?.avg_graph_verification_score !== undefined
                              ? graphMetrics.verification_metrics.avg_graph_verification_score.toFixed(3)
                              : "0.000"}
                          </span>
                        </div>
                        <div className="p-4 bg-slate-900 border border-white/5 rounded-xl">
                          <span className="text-[9px] font-bold text-subtext/50 uppercase tracking-widest block">Hybrid RAG Verification</span>
                          <span className="text-xl font-bold font-mono text-success block mt-1.5">
                            {graphMetrics.verification_metrics?.avg_hybrid_verification_score !== undefined
                              ? graphMetrics.verification_metrics.avg_hybrid_verification_score.toFixed(3)
                              : "0.000"}
                          </span>
                        </div>
                        <div className="p-4 bg-slate-900 border border-white/5 rounded-xl">
                          <span className="text-[9px] font-bold text-subtext/50 uppercase tracking-widest block">Graph RAG Grounding</span>
                          <span className="text-xl font-bold font-mono text-blue-400 block mt-1.5">
                            {graphMetrics.verification_metrics?.avg_graph_grounding_score !== undefined
                              ? graphMetrics.verification_metrics.avg_graph_grounding_score.toFixed(3)
                              : "0.000"}
                          </span>
                        </div>
                        <div className="p-4 bg-slate-900 border border-white/5 rounded-xl">
                          <span className="text-[9px] font-bold text-subtext/50 uppercase tracking-widest block">Hybrid RAG Grounding</span>
                          <span className="text-xl font-bold font-mono text-emerald-400 block mt-1.5">
                            {graphMetrics.verification_metrics?.avg_hybrid_grounding_score !== undefined
                              ? graphMetrics.verification_metrics.avg_hybrid_grounding_score.toFixed(3)
                              : "0.000"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        )}
      </main>
    </div>
  );
}

// Reusable Dashboard Card Component with KPI layout & hover states
interface DashboardCardProps {
  title: string;
  value: string;
  subtitle: string;
  color: string;
  icon: React.ReactNode;
}

const DashboardCard: React.FC<DashboardCardProps> = ({ title, value, subtitle, color, icon }) => {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 15 },
        show: { opacity: 1, y: 0 }
      }}
      whileHover={{ y: -2 }}
      className="bg-card border border-white/5 rounded-2xl p-5 shadow-md glass-panel glass-panel-hover flex flex-col justify-between select-none"
    >
      <div className="flex justify-between items-center gap-2">
        <span className="text-[9px] font-bold text-subtext/50 uppercase tracking-widest">{title}</span>
        <div className="w-7 h-7 rounded-lg bg-background/50 border border-white/5 flex items-center justify-center">
          {icon}
        </div>
      </div>
      <div className="mt-4">
        <h2 className={`text-2xl font-bold font-outfit tracking-tight ${color}`}>{value}</h2>
        <p className="text-[9px] font-medium text-subtext/60 mt-1 leading-relaxed">{subtitle}</p>
      </div>
    </motion.div>
  );
};

// Micro-component Fallbacks for Icons
function BrainCircuitIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      <circle cx="12" cy="12" r="4" />
    </svg>
  );
}

function PenToolIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
