"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  BookOpen,
  Brain,
  Cpu,
  Layers,
  Activity,
  Award,
  ChevronRight,
  TrendingUp,
  Database,
  ArrowRight,
  ShieldCheck,
  Menu,
  X,
  FileText
} from "lucide-react";
import "./workspace.css";

import {
  Session,
  Message,
  fetchSessions,
  createSession,
  deleteSession,
  fetchSessionDetails,
  sendChatMessage,
} from "../lib/api";

import SessionSidebar from "./components/SessionSidebar";
import ChatInterface from "./components/ChatInterface";
import CitationPanel from "./components/CitationPanel";
import ResearchTracePanel from "./components/ResearchTracePanel";
import ExecutionTimeline from "./components/ExecutionTimeline";
import DeepResearchVisualization from "./components/DeepResearchVisualization";

export default function WorkspacePage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [activeTab, setActiveTab] = useState<"citations" | "trace" | "timeline" | "visualization">("citations");
  const [activeQueryResponse, setActiveQueryResponse] = useState<any>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);
  
  // Responsive UI toggles
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);

  // Load all sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load active session messages when currentSessionId changes
  useEffect(() => {
    if (currentSessionId) {
      loadSessionDetails(currentSessionId);
    } else {
      setMessages([]);
      setSelectedMessage(null);
      setActiveQueryResponse(null);
    }
  }, [currentSessionId]);

  const loadSessions = async () => {
    try {
      setGlobalError(null);
      const data = await fetchSessions();
      setSessions(data);
      if (data.length > 0 && !currentSessionId) {
        setCurrentSessionId(data[0].id);
      }
    } catch (err: any) {
      console.error(err);
      setGlobalError("Failed to fetch chat sessions. Make sure the backend server is running.");
    }
  };

  const loadSessionDetails = async (id: string) => {
    try {
      setGlobalError(null);
      const data = await fetchSessionDetails(id);
      setMessages(data.messages || []);
      setSelectedMessage(null);
      setActiveQueryResponse(null);
      
      const assistantMsgs = (data.messages || []).filter((m) => m.role === "assistant");
      if (assistantMsgs.length > 0) {
        const lastMsg = assistantMsgs[assistantMsgs.length - 1];
        setSelectedMessage(lastMsg);
      }
    } catch (err: any) {
      console.error(err);
      setGlobalError("Failed to load conversation history.");
    }
  };

  const handleCreateSession = async () => {
    try {
      const title = `Research Session ${sessions.length + 1}`;
      const newSession = await createSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
    } catch (err: any) {
      console.error(err);
      alert("Failed to create new chat session.");
    }
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (currentSessionId === id) {
        setCurrentSessionId(null);
      }
    } catch (err: any) {
      console.error(err);
      alert("Failed to delete session.");
    }
  };

  const handleSendMessage = async (text: string, useDeepResearch: boolean) => {
    if (!currentSessionId) return;

    const userMsg: Message = {
      id: Math.random().toString(),
      session_id: currentSessionId,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
      citations: [],
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setGlobalError(null);

    try {
      const res = await sendChatMessage(currentSessionId, text);
      
      const assistantMsg: Message = {
        id: Math.random().toString(),
        session_id: currentSessionId,
        role: "assistant",
        content: res.answer,
        created_at: new Date().toISOString(),
        citations: res.citations.map((c: any, i: number) => ({
          id: Math.random().toString(),
          message_id: "",
          document_id: c.document_id,
          page_number: c.page_number,
          snippet: c.snippet,
          filename: c.filename,
        })),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setSelectedMessage(assistantMsg);
      setActiveQueryResponse(res);
      
      if (messages.length === 0) {
        loadSessions();
      }
    } catch (err: any) {
      console.error(err);
      setGlobalError(err.message || "RAG engine query failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMessage = (msg: Message | null) => {
    setSelectedMessage(msg);
    if (msg && activeQueryResponse && activeQueryResponse.answer === msg.content) {
      // Keep existing activeQueryResponse
    } else {
      setActiveQueryResponse(null);
    }
  };

  const handleUploadSuccess = (doc: any) => {
    loadSessions();
  };

  const hasSessions = sessions.length > 0;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-text font-sans">
      {/* 1. Left Sidebar */}
      <AnimatePresence initial={false}>
        {showLeftSidebar && (
          <motion.div
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ type: "spring", damping: 20, stiffness: 100 }}
            className="h-full flex-shrink-0 relative z-20"
          >
            <SessionSidebar
              sessions={sessions}
              currentSessionId={currentSessionId}
              onSelectSession={setCurrentSessionId}
              onCreateSession={handleCreateSession}
              onDeleteSession={handleDeleteSession}
              onUploadSuccess={handleUploadSuccess}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. Main Chat Area & Hero State */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-[#0b0f19]">
        {/* Toggle Sidebar Buttons for Mobile/Tablet */}
        <div className="absolute left-4 bottom-20 z-40 flex gap-2">
          <button
            onClick={() => setShowLeftSidebar(!showLeftSidebar)}
            className="p-3 bg-[#111827] border border-white/10 rounded-full text-subtext hover:text-text shadow-lg focus:outline-none hover:scale-105 active:scale-95 transition-all"
            title="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowRightPanel(!showRightPanel)}
            className="p-3 bg-[#111827] border border-white/10 rounded-full text-subtext hover:text-text shadow-lg focus:outline-none hover:scale-105 active:scale-95 transition-all"
            title="Toggle Right Panel"
          >
            <Activity className="w-5 h-5" />
          </button>
        </div>

        {globalError && (
          <div className="bg-error/10 border-b border-error/20 px-6 py-3 text-xs text-error/90 font-medium flex justify-between items-center select-none z-40">
            <span>⚠️ {globalError}</span>
            <button onClick={() => setGlobalError(null)} className="text-error/70 hover:text-error text-base font-bold">×</button>
          </div>
        )}

        {!currentSessionId ? (
          /* Landing Page Experience */
          <div className="flex-1 overflow-y-auto flex items-center justify-center p-6 md:p-12">
            <div className="max-w-3xl w-full text-center space-y-12 select-none">
              
              {/* Header Titles */}
              <div className="space-y-4">
                <motion.div
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 border border-primary/20 rounded-full text-[11px] font-bold text-primary tracking-wide uppercase"
                >
                  <Sparkles className="w-3.5 h-3.5 animate-pulse text-primary" />
                  Local-First Research Agent
                </motion.div>
                <motion.h1
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 }}
                  className="text-5xl md:text-6xl font-extrabold font-outfit tracking-tight bg-gradient-to-r from-white via-indigo-200 to-indigo-500 bg-clip-text text-transparent"
                >
                  AgentForge-X
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.2 }}
                  className="text-sm md:text-base text-subtext max-w-lg mx-auto font-medium"
                >
                  Deep Research AI Platform powered by multi-agent reasoning, semantic vector search, and real-time grounding.
                </motion.p>
              </div>

              {/* Start Button */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <button
                  onClick={handleCreateSession}
                  className="px-8 py-4 bg-gradient-to-r from-primary to-indigo-600 hover:opacity-95 text-white font-bold text-base rounded-2xl shadow-xl shadow-primary/20 hover:shadow-primary/30 flex items-center gap-3.5 mx-auto hover:scale-105 active:scale-98 transition-all duration-200"
                >
                  Start Research
                  <ArrowRight className="w-5 h-5 text-white animate-pulse" />
                </button>
              </motion.div>

              {/* Features Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                {[
                  {
                    icon: <Brain className="w-5 h-5 text-indigo-400" />,
                    title: "Multi-Agent Reasoning",
                    desc: "Collaborative agents analyze, plan, and verify steps asynchronously."
                  },
                  {
                    icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />,
                    title: "Citation Grounding",
                    desc: "All statements are strictly validated against referenced documents."
                  },
                  {
                    icon: <Database className="w-5 h-5 text-amber-400" />,
                    title: "Knowledge Graph Retrieval",
                    desc: "Neo4j integration enables semantic cross-document entity mappings."
                  },
                  {
                    icon: <Layers className="w-5 h-5 text-pink-400" />,
                    title: "Deep Research Workflows",
                    desc: "Parallel sub-question decomposing and RAG query expansions."
                  }
                ].map((feat, idx) => (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.4 + idx * 0.1 }}
                    key={idx}
                    className="p-5 rounded-2xl bg-[#111827]/40 border border-white/5 text-left flex gap-4 glass-panel glass-panel-hover"
                  >
                    <div className="w-10 h-10 rounded-xl bg-background/50 border border-white/5 flex items-center justify-center flex-shrink-0 shadow-md">
                      {feat.icon}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-text font-outfit uppercase tracking-wider">{feat.title}</h4>
                      <p className="text-[11px] text-subtext leading-relaxed mt-1 font-medium">{feat.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Main Interactive Chat Interface */
          <ChatInterface
            messages={messages}
            currentSessionId={currentSessionId}
            loading={loading}
            onSendMessage={handleSendMessage}
            onSelectMessage={handleSelectMessage}
            selectedMessageId={selectedMessage ? selectedMessage.id : null}
          />
        )}
      </div>

      {/* 3. Detail Right Panel */}
      <AnimatePresence initial={false}>
        {showRightPanel && currentSessionId && (
          <motion.div
            initial={{ x: 450, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 450, opacity: 0 }}
            transition={{ type: "spring", damping: 20, stiffness: 100 }}
            className="detail-panel border-l border-white/5 bg-card flex flex-col h-full relative z-20 w-[450px] shadow-2xl glass-panel"
          >
            {/* Header Tabs */}
            <div className="flex border-b border-white/5 bg-background/25">
              {[
                { id: "citations", label: "Citations" },
                { id: "trace", label: "Research Trace" },
                { id: "timeline", label: "Execution" },
                { id: "visualization", label: "Workflow Graph" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  className={`flex-1 py-3.5 text-[10px] font-bold text-center border-b-2 uppercase tracking-wider transition-colors duration-150 ${
                    activeTab === tab.id
                      ? "text-primary border-primary"
                      : "text-subtext/60 border-transparent hover:text-text"
                  }`}
                  onClick={() => setActiveTab(tab.id as any)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Contents */}
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === "citations" && <CitationPanel message={selectedMessage} />}
              {activeTab === "trace" && (
                <ResearchTracePanel message={selectedMessage} activeQueryResponse={activeQueryResponse} />
              )}
              {activeTab === "timeline" && <ExecutionTimeline activeQueryResponse={activeQueryResponse} />}
              {activeTab === "visualization" && <DeepResearchVisualization activeQueryResponse={activeQueryResponse} />}
            </div>
            
            {/* Link back to metrics dashboard */}
            <div className="p-4 border-t border-white/5 bg-background/25 text-center">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1.5 text-primary text-[10px] font-bold uppercase tracking-wider hover:opacity-85 transition-opacity"
              >
                📊 View System Evaluation Dashboard
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
