import React, { useState, useEffect } from "react";
import { Session } from "../../lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  Plus,
  Search,
  Trash2,
  UploadCloud,
  FileText,
  ChevronLeft,
  ChevronRight,
  Loader2
} from "lucide-react";

interface SessionSidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string) => void;
  onUploadSuccess: (doc: any) => void;
}

export default function SessionSidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onUploadSuccess,
}: SessionSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleFileChange = async (file: File) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      return;
    }

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to upload document");
      }

      const doc = await res.json();
      onUploadSuccess(doc);
      setUploadError(null);
    } catch (err: any) {
      console.error(err);
      setUploadError(err.message || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileChange(file);
    e.target.value = "";
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  // Filter sessions
  const filteredSessions = sessions.filter(s =>
    (s.title || "Untitled Session").toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group sessions by date
  const getSessionGroups = () => {
    const today: Session[] = [];
    const earlier: Session[] = [];

    if (!mounted) {
      // During SSR and initial hydration, route all sessions to 'earlier'
      // to ensure deterministic render matching the server.
      return { today: [], earlier: filteredSessions };
    }

    const now = new Date();
    now.setHours(0, 0, 0, 0);

    filteredSessions.forEach(s => {
      const date = new Date(s.created_at || Date.now());
      date.setHours(0, 0, 0, 0);
      if (date.getTime() === now.getTime()) {
        today.push(s);
      } else {
        earlier.push(s);
      }
    });

    return { today, earlier };
  };

  const { today, earlier } = getSessionGroups();

  return (
    <motion.aside
      className="bg-card border-r border-white/5 flex flex-col h-full relative z-30 shadow-2xl glass-panel"
      animate={{ width: isCollapsed ? 76 : 300 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      {/* Brand Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between overflow-hidden">
        {!isCollapsed && (
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3"
          >
            <div className="bg-gradient-to-br from-primary to-indigo-700 w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white text-base shadow-lg shadow-primary/20">
              AF
            </div>
            <div>
              <h2 className="text-base font-bold text-text tracking-tight font-outfit">AgentForge-X</h2>
              <span className="text-[10px] text-primary/80 font-medium tracking-widest uppercase">Multi-Agent v1.5</span>
            </div>
          </motion.div>
        )}
        {isCollapsed && (
          <div className="bg-gradient-to-br from-primary to-indigo-700 w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white text-base shadow-lg shadow-primary/20 mx-auto">
            AF
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-lg hover:bg-white/5 text-subtext hover:text-text transition-colors duration-150 absolute right-4 top-5 bg-card border border-white/5"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="px-4 py-3">
        <button
          onClick={onCreateSession}
          className="w-full py-2.5 px-3 bg-gradient-to-r from-primary to-indigo-600 hover:opacity-95 text-white rounded-xl font-semibold text-sm shadow-lg shadow-primary/10 flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          {!isCollapsed && <span>New Research Session</span>}
        </button>
      </div>

      {/* Session Search */}
      {!isCollapsed && (
        <div className="px-4 mb-2">
          <div className="relative flex items-center bg-background/50 border border-white/5 rounded-xl px-3 py-1.5 focus-within:border-primary/50 transition-all duration-200">
            <Search className="w-3.5 h-3.5 text-subtext mr-2" />
            <input
              type="text"
              placeholder="Search chat history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-xs text-text placeholder-subtext/50 outline-none w-full"
            />
          </div>
        </div>
      )}

      {/* Session List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-4 py-2">
        {isCollapsed ? (
          <div className="flex flex-col items-center gap-2">
            {sessions.map(s => (
              <button
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                  currentSessionId === s.id
                    ? "bg-primary/25 border border-primary/45 text-primary"
                    : "hover:bg-white/5 text-subtext"
                }`}
                title={s.title}
              >
                <MessageSquare className="w-4 h-4" />
              </button>
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-subtext/60 text-xs font-medium">
            No research sessions yet.
          </div>
        ) : (
          <div className="space-y-4">
            {today.length > 0 && (
              <div className="space-y-1">
                <div className="text-[10px] font-bold text-subtext/50 uppercase tracking-widest px-3 mb-1">Today</div>
                {today.map(s => (
                  <div
                    key={s.id}
                    onClick={() => onSelectSession(s.id)}
                    className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer border transition-all duration-200 ${
                      currentSessionId === s.id
                        ? "bg-primary/10 border-primary/20 hover:bg-primary/15"
                        : "bg-transparent border-transparent hover:bg-white/5"
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${currentSessionId === s.id ? "text-primary" : "text-subtext/70"}`} />
                      <span className={`text-xs truncate font-medium ${currentSessionId === s.id ? "text-text" : "text-subtext group-hover:text-text"}`}>
                        {s.title || "Untitled Session"}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm("Delete this session and all its messages?")) {
                          onDeleteSession(s.id);
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/10 text-subtext hover:text-error transition-all duration-150"
                      title="Delete Session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {earlier.length > 0 && (
              <div className="space-y-1">
                <div className="text-[10px] font-bold text-subtext/50 uppercase tracking-widest px-3 mb-1">Earlier</div>
                {earlier.map(s => (
                  <div
                    key={s.id}
                    onClick={() => onSelectSession(s.id)}
                    className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer border transition-all duration-200 ${
                      currentSessionId === s.id
                        ? "bg-primary/10 border-primary/20 hover:bg-primary/15"
                        : "bg-transparent border-transparent hover:bg-white/5"
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${currentSessionId === s.id ? "text-primary" : "text-subtext/70"}`} />
                      <span className={`text-xs truncate font-medium ${currentSessionId === s.id ? "text-text" : "text-subtext group-hover:text-text"}`}>
                        {s.title || "Untitled Session"}
                      </span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm("Delete this session and all its messages?")) {
                          onDeleteSession(s.id);
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/10 text-subtext hover:text-error transition-all duration-150"
                      title="Delete Session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Knowledge PDF Upload card */}
      <div className="p-4 border-t border-white/5 bg-background/30">
        {!isCollapsed ? (
          <div>
            <div className="mb-2 text-xs font-bold text-text/80 font-outfit">
              Ingest Knowledge PDF
            </div>
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border border-dashed rounded-xl p-4 text-center cursor-pointer transition-all duration-200 relative overflow-hidden ${
                dragActive
                  ? "border-primary bg-primary/5 scale-[0.98]"
                  : "border-white/10 hover:border-primary/50 hover:bg-white/5"
              }`}
            >
              <input
                type="file"
                accept=".pdf"
                onChange={onFileInputChange}
                disabled={uploading}
                className="hidden"
                id="sidebar-file-upload"
              />
              <label htmlFor="sidebar-file-upload" className="cursor-pointer block w-full">
                {uploading ? (
                  <div className="flex flex-col items-center justify-center py-2 space-y-2">
                    <Loader2 className="w-6 h-6 text-success animate-spin" />
                    <span className="text-[11px] font-semibold text-success animate-pulse">
                      Analyzing & Chunking...
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center space-y-1.5 py-1">
                    <UploadCloud className="w-7 h-7 text-subtext/60 group-hover:text-primary transition-colors duration-200" />
                    <span className="text-[11px] font-medium text-subtext block">
                      Drag & drop PDF here
                    </span>
                    <span className="text-[10px] text-primary/70 font-semibold hover:underline block">
                      Or browse files
                    </span>
                  </div>
                )}
              </label>
            </div>
          </div>
        ) : (
          <div className="flex justify-center relative">
            <input
              type="file"
              accept=".pdf"
              onChange={onFileInputChange}
              disabled={uploading}
              className="hidden"
              id="sidebar-file-upload-collapsed"
            />
            <label
              htmlFor="sidebar-file-upload-collapsed"
              className={`w-10 h-10 rounded-xl flex items-center justify-center cursor-pointer transition-all border ${
                uploading ? "bg-success/10 border-success/30 text-success" : "border-white/10 hover:border-primary/50 hover:bg-white/5 text-subtext"
              }`}
              title="Upload PDF Document"
            >
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
            </label>
          </div>
        )}
        {uploadError && !isCollapsed && (
          <div className="text-[10px] font-semibold text-error mt-2 leading-relaxed bg-error/10 border border-error/20 p-2 rounded-lg">
            ⚠️ {uploadError}
          </div>
        )}
      </div>
    </motion.aside>
  );
}
