// Frontend API Service for AgentForge-X Backend API

const API_BASE = "http://127.0.0.1:8000/api/v1";

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  id: string;
  message_id: string;
  document_id?: string;
  page_number?: number;
  snippet: string;
  filename?: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  citations: Citation[];
}

export interface SessionWithMessages extends Session {
  messages: Message[];
}

export interface ChatResponse {
  answer: string;
  confidence_score: number;
  grounding_score: number;
  verification_score: number;
  verification_status: string;
  adaptive_retrieval_used: boolean;
  verification_improvement: number;
  citations: {
    document_id?: string;
    filename: string;
    page_number?: number;
    snippet: string;
  }[];
  retrieval_mode?: string;
  graph_entities?: any[];
  graph_relationships?: any[];
  hybrid_used?: boolean;
  sub_questions?: string[];
  research_depth?: string;
  retrieval_modes?: string[];
  faithfulness_score?: number;
  answer_relevancy_score?: number;
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function createSession(title: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete session");
  return res.json();
}

export async function fetchSessionDetails(sessionId: string): Promise<SessionWithMessages> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session details");
  return res.json();
}

export async function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to execute RAG query");
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to upload document");
  }
  return res.json();
}

export interface SystemStatus {
  status: string;
  dependencies: {
    sqlite: boolean;
    chromadb: boolean;
    neo4j: boolean;
    ollama: boolean;
    gemini?: boolean;
  };
  timestamp: number;
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  try {
    const res = await fetch(`${API_BASE}/monitoring/readiness`);
    if (!res.ok) {
      const data = await res.json().catch(() => null);
      if (data && data.status) {
        return data;
      }
      return {
        status: "degraded",
        dependencies: { sqlite: false, chromadb: false, neo4j: false, ollama: false, gemini: false },
        timestamp: Date.now() / 1000
      };
    }
    const data = await res.json().catch(() => null);
    if (!data) {
      return {
        status: "degraded",
        dependencies: { sqlite: false, chromadb: false, neo4j: false, ollama: false, gemini: false },
        timestamp: Date.now() / 1000
      };
    }
    return data;
  } catch (err) {
    return {
      status: "offline",
      dependencies: { sqlite: false, chromadb: false, neo4j: false, ollama: false, gemini: false },
      timestamp: Date.now() / 1000
    };
  }
}

