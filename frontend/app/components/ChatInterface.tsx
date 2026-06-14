import React, { useState, useRef, useEffect } from "react";
import { Message, fetchSystemStatus, SystemStatus } from "../../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Sparkles,
  Paperclip,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Search,
  BookOpen,
  ShieldAlert,
  Server,
  Activity,
  Cpu,
  Database,
  Share2
} from "lucide-react";

interface ChatInterfaceProps {
  messages: Message[];
  currentSessionId: string | null;
  loading: boolean;
  onSendMessage: (text: string, useDeepResearch: boolean) => void;
  onSelectMessage: (msg: Message | null) => void;
  selectedMessageId: string | null;
}

// Helper to format basic Markdown to HTML
function renderMarkdown(text: string) {
  if (!text) return "";
  
  // Escape HTML
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks: ```content```
  html = html.replace(/```([\s\S]*?)```/g, (_, code) => {
    return `<pre class="bg-slate-950/80 border border-white/5 p-4 rounded-xl overflow-x-auto font-mono text-xs my-3 text-slate-200 shadow-inner"><code class="block whitespace-pre">${code.trim()}</code></pre>`;
  });

  // Bold: **text**
  html = html.replace(/\*\*([\s\S]*?)\*\*/g, "<strong class='text-white font-semibold'>$1</strong>");

  // Inline code: `code`
  html = html.replace(/`([^`\n]+)`/g, "<code class='bg-slate-800/60 px-1.5 py-0.5 rounded-md font-mono text-xs text-primary font-semibold'>$1</code>");

  // Bullet points
  html = html.replace(/^\s*[\*\-]\s+(.+)$/gm, "<li class='ml-5 list-disc my-1 text-slate-300'>$1</li>");

  // Newlines
  html = html.replace(/\n/g, "<br />");

  return html;
}

export default function ChatInterface({
  messages,
  currentSessionId,
  loading,
  onSendMessage,
  onSelectMessage,
  selectedMessageId,
}: ChatInterfaceProps) {
  const [inputText, setInputText] = useState("");
  const [useDeepResearch, setUseDeepResearch] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  // System status states
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [backendStatus, setBackendStatus] = useState<"online" | "offline">("offline");

  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Poll system status
  useEffect(() => {
    const checkStatus = async () => {
      const data = await fetchSystemStatus();
      setSystemStatus(data);
      if (data.status === "offline") {
        setBackendStatus("offline");
      } else {
        setBackendStatus("online");
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    onSendMessage(inputText, useDeepResearch);
    setInputText("");
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Mock upload action
  const handleAttachmentClick = () => {
    const sidebarUpload = document.getElementById("sidebar-file-upload") as HTMLInputElement;
    if (sidebarUpload) {
      sidebarUpload.click();
    } else {
      fileInputRef.current?.click();
    }
  };

  // Simulated progressive step indicator for multi-agent RAG workflow
  const [loadingStep, setLoadingStep] = useState(0);
  useEffect(() => {
    if (!loading) {
      setLoadingStep(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingStep((prev) => (prev < 3 ? prev + 1 : prev));
    }, 2500);
    return () => clearInterval(interval);
  }, [loading]);

  const loadingSteps = [
    { name: "Planning Research...", label: "Planner Agent is decomposing query", color: "text-indigo-400" },
    { name: "Retrieving Evidence...", label: "ChromaDB & Neo4j are fetching relevant contexts", color: "text-emerald-400" },
    { name: "Generating Response...", label: "Gemini is synthesizing facts into answer", color: "text-amber-400" },
    { name: "Verifying Grounding...", label: "Verifier Agent is checking statements against sources", color: "text-rose-400" }
  ];

  return (
    <div className="main-chat-area flex flex-col h-full bg-[#0b0f19]">
      {/* Header with System Status Bar */}
      <header className="p-4 border-b border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#111827]/30 backdrop-blur-md relative z-10">
        <div>
          <h2 className="text-sm font-bold text-text tracking-tight font-outfit flex items-center gap-2">
            {currentSessionId ? "RAG Research Workspace" : "Select or Start a Session"}
            {currentSessionId && (
              <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-semibold ${
                backendStatus === "offline" || systemStatus?.status === "not_ready"
                  ? "bg-error/10 text-error border border-error/20"
                  : systemStatus?.status === "degraded"
                  ? "bg-warning/10 text-warning border border-warning/20"
                  : "bg-success/10 text-success border border-success/20"
              }`}>
                <span className={`w-1 h-1 rounded-full ${
                  backendStatus === "offline" || systemStatus?.status === "not_ready"
                    ? "bg-error"
                    : systemStatus?.status === "degraded"
                    ? "bg-warning"
                    : "bg-success animate-pulse"
                }`} />
                {backendStatus === "offline" || systemStatus?.status === "not_ready"
                  ? "Offline"
                  : systemStatus?.status === "degraded"
                  ? "Degraded"
                  : "Online"
                }
              </span>
            )}
          </h2>
          <p className="text-[10px] text-subtext mt-0.5">
            Query local documents and view multi-agent verification traces
          </p>
        </div>
        
        {/* Status Indicators & Mode Toggle */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Status Bar */}
          <div className="flex items-center gap-2 bg-background/50 border border-white/5 px-2.5 py-1 rounded-xl text-[10px] font-semibold text-subtext/90">
            <span className="flex items-center gap-1.5 border-r border-white/10 pr-2">
              <span className={`w-1.5 h-1.5 rounded-full ${backendStatus === "online" ? "bg-success animate-pulse" : "bg-error"}`} />
              Backend
            </span>
            <span className="flex items-center gap-1.5 border-r border-white/10 pr-2">
              <span className={`w-1.5 h-1.5 rounded-full ${systemStatus?.dependencies.sqlite ? "bg-success" : "bg-error"}`} />
              SQLite
            </span>
            <span className="flex items-center gap-1.5 border-r border-white/10 pr-2">
              <span className={`w-1.5 h-1.5 rounded-full ${systemStatus?.dependencies.chromadb ? "bg-success" : "bg-error"}`} />
              Chroma
            </span>
            <span className="flex items-center gap-1.5 border-r border-white/10 pr-2">
              <span className={`w-1.5 h-1.5 rounded-full ${systemStatus?.dependencies.neo4j ? "bg-success" : "bg-warning"}`} />
              Neo4j
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${systemStatus?.dependencies.gemini ? "bg-success animate-pulse" : "bg-error"}`} />
              Gemini
            </span>
          </div>

          {/* Mode Selector */}
          <div className="flex bg-[#111827] p-0.5 rounded-xl border border-white/5">
            <button
              onClick={() => setUseDeepResearch(false)}
              className={`px-3 py-1 rounded-lg text-[10px] font-bold transition-all duration-150 ${
                !useDeepResearch
                  ? "bg-slate-800 text-white shadow-sm"
                  : "text-subtext/75 hover:text-text"
              }`}
            >
              Adaptive RAG
            </button>
            <button
              onClick={() => setUseDeepResearch(true)}
              className={`px-3 py-1 rounded-lg text-[10px] font-bold transition-all duration-150 flex items-center gap-1 ${
                useDeepResearch
                  ? "bg-primary text-white shadow-lg shadow-primary/10"
                  : "text-subtext/75 hover:text-text"
              }`}
            >
              <Sparkles className="w-2.5 h-2.5 text-amber-300 animate-pulse" />
              Deep Research (Gemini)
            </button>
          </div>
        </div>
      </header>

      {/* Hidden file input for drag and drop attachment mock */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            // Forward to sidebar file uploader handler
            const sidebarUpload = document.getElementById("sidebar-file-upload") as HTMLInputElement;
            if (sidebarUpload) {
              const dataTransfer = new DataTransfer();
              dataTransfer.items.add(file);
              sidebarUpload.files = dataTransfer.files;
              sidebarUpload.dispatchEvent(new Event("change", { bubbles: true }));
            }
          }
        }}
        accept=".pdf"
        className="hidden"
      />

      {/* Chat History Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
        {!currentSessionId ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 select-none max-w-xl mx-auto space-y-6">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/25 to-indigo-500/10 border border-primary/20 flex items-center justify-center text-primary shadow-xl shadow-primary/5"
            >
              <Sparkles className="w-8 h-8 animate-pulse text-primary" />
            </motion.div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold font-outfit text-white tracking-tight">Welcome to AgentForge-X Workspace</h3>
              <p className="text-xs text-subtext leading-relaxed">
                Select an existing chat session from the sidebar or click **"New Research Session"** to query documents using Gemini multi-agent reasoning.
              </p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 select-none max-w-xl mx-auto space-y-6">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/25 to-indigo-500/10 border border-primary/20 flex items-center justify-center text-primary shadow-xl shadow-primary/5"
            >
              <BookOpen className="w-8 h-8 text-primary" />
            </motion.div>
            <div className="space-y-2">
              <h3 className="text-xl font-bold font-outfit text-white tracking-tight">Start Your Document Inquiry</h3>
              <p className="text-xs text-subtext leading-relaxed">
                Ask questions about your uploaded PDFs. The Gemini-powered multi-agent system will retrieve contexts and verify answers.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-4xl mx-auto">
            {messages.map((msg, index) => {
              const isAssistant = msg.role === "assistant";
              const isSelected = selectedMessageId === msg.id;

              return (
                <motion.div
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  key={msg.id || index}
                  className={`flex gap-4 ${isAssistant ? "justify-start" : "justify-end"}`}
                >
                  {isAssistant && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-indigo-700 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-primary/10 select-none flex-shrink-0">
                      AI
                    </div>
                  )}

                  <div className={`flex flex-col max-w-[85%] gap-1.5 ${isAssistant ? "items-start" : "items-end"}`}>
                    <div
                      onClick={() => isAssistant && onSelectMessage(msg)}
                      className={`p-4 rounded-2xl text-[13px] leading-relaxed relative cursor-pointer border transition-all duration-200 ${
                        isAssistant
                          ? isSelected
                            ? "bg-slate-900/60 border-primary shadow-lg shadow-primary/5 text-text"
                            : "bg-slate-900/40 border-white/5 hover:border-white/10 text-text"
                          : "bg-primary text-white border-transparent shadow-lg shadow-primary/10 rounded-br-none"
                      }`}
                    >
                      {isAssistant ? (
                        <div
                          className="prose prose-invert max-w-none prose-sm"
                          dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                        />
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      )}

                      {/* Tool Actions overlay on hover (Assistant only) */}
                      {isAssistant && (
                        <div className="absolute right-2 top-2 opacity-0 hover:opacity-100 group-hover:opacity-100 flex items-center gap-1.5 bg-slate-950/80 border border-white/10 px-1.5 py-0.5 rounded-lg backdrop-blur-sm transition-all duration-200">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopy(msg.id, msg.content);
                            }}
                            className="p-1 text-subtext hover:text-white rounded transition-colors"
                            title="Copy Answer"
                          >
                            {copiedId === msg.id ? (
                              <Check className="w-3.5 h-3.5 text-success" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      )}
                    </div>

                    {isAssistant && (
                      <div className="flex items-center gap-3 text-[10px] font-semibold text-subtext/60 px-1 select-none">
                        {msg.citations && msg.citations.length > 0 && (
                          <span className="flex items-center gap-1">
                            📂 {msg.citations.length} Citations
                          </span>
                        )}
                        <span className="text-primary/70 hover:text-primary transition-colors cursor-pointer">
                          🔬 Click to inspect reasoning trace
                        </span>
                      </div>
                    )}
                  </div>

                  {!isAssistant && (
                    <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-subtext text-xs font-bold select-none flex-shrink-0">
                      U
                    </div>
                  )}
                </motion.div>
              );
            })}

            {/* Agent execution progressive loading indicator */}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4 justify-start max-w-4xl"
              >
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-indigo-700 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-primary/10 select-none flex-shrink-0 animate-pulse">
                  AI
                </div>

                <div className="flex flex-col max-w-[85%] gap-2 bg-slate-900/30 border border-white/5 rounded-2xl p-4 w-full shadow-lg">
                  {/* Step Loader Indicators */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 border-b border-white/5 pb-3">
                    {loadingSteps.map((step, idx) => {
                      const isActive = loadingStep === idx;
                      const isCompleted = loadingStep > idx;

                      return (
                        <div
                          key={idx}
                          className={`flex items-center gap-2 p-1.5 rounded-lg transition-all duration-300 ${
                            isActive
                              ? "bg-white/5 border border-white/10"
                              : "border border-transparent opacity-50"
                          }`}
                        >
                          <div className="relative flex-shrink-0">
                            {isActive ? (
                              <div className="w-4 h-4 rounded-full border border-primary border-t-transparent animate-spin" />
                            ) : isCompleted ? (
                              <CheckCircle2 className="w-4 h-4 text-success" />
                            ) : (
                              <div className="w-4 h-4 rounded-full bg-slate-800 border border-white/10" />
                            )}
                          </div>
                          <div className="min-w-0">
                            <div className={`text-[10px] font-bold truncate ${isActive ? step.color : "text-subtext"}`}>
                              {step.name}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Active Step Details */}
                  <div className="flex items-center gap-3 pt-1">
                    <Activity className="w-3.5 h-3.5 text-primary animate-pulse flex-shrink-0" />
                    <span className="text-[11px] font-medium text-subtext animate-pulse">
                      {loadingSteps[loadingStep]?.label || "Running Multi-Agent workflow..."}
                    </span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-white/5 bg-[#111827]/20 backdrop-blur-md">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSend} className="relative bg-slate-900/90 border border-white/5 focus-within:border-primary/50 shadow-xl rounded-2xl p-2 flex items-end gap-2 transition-all duration-300">
            {/* Attachment Button */}
            <button
              type="button"
              onClick={handleAttachmentClick}
              disabled={!currentSessionId || loading}
              className="p-2.5 rounded-xl hover:bg-white/5 text-subtext hover:text-text disabled:opacity-50 transition-colors"
              title="Upload PDF attachment"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            {/* Main input text */}
            <textarea
              className="flex-1 bg-transparent text-xs text-text placeholder-subtext/50 outline-none p-2 resize-none max-h-36 font-sans outline-0"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
              placeholder={
                currentSessionId 
                  ? "Ask a question about the uploaded PDFs..." 
                  : "Select or create a session to start research..."
              }
              disabled={!currentSessionId || loading}
              rows={1}
            />

            {/* Send Button */}
            <button
              type="submit"
              disabled={!inputText.trim() || !currentSessionId || loading}
              className="p-2.5 rounded-xl bg-gradient-to-r from-primary to-indigo-600 hover:opacity-95 text-white disabled:bg-slate-800 disabled:opacity-30 disabled:text-subtext flex-shrink-0 shadow-lg shadow-primary/10 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
