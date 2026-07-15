export interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  status: ConversationStatus;
  selected_repository: string | null;
}

export type ConversationStatus =
  | "running"
  | "stopped"
  | "awaiting_user_input"
  | "finished"
  | "error";

export interface ConversationSummary {
  conversation_id: string;
  title: string;
  last_message_preview: string | null;
  created_at: string;
  updated_at: string;
  status: ConversationStatus;
}

/* ── Message types ── */

export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  actionType?: string;
  actionTitle?: string;
  mode?: string;
}

/* ── WebSocket types ── */

export interface WebSocketEvent {
  type: string;
  source?: string;
  message?: { role: string; content: Array<{ type: string; text?: string }> };
  action?: { action_type: string; thought?: string; title?: string };
  observation?: { content: string; extracted_code?: string };
  error?: { code: string; detail: string };
  status?: { execution_status?: string };
}

/* ── Timeline types ── */

export interface TimelineEvent {
  id: string;
  type: "action" | "observation" | "message" | "error" | "status";
  actionType?: string;
  title: string;
  detail?: string;
  timestamp: Date;
  duration?: number;
  status?: "running" | "done" | "error" | "skipped";
}

/* ── Plan types ── */

export interface PlanStep {
  id: string;
  title: string;
  description: string;
  files: string[];
  estimatedTokens?: string;
  riskLevel?: "low" | "medium" | "high";
}

/* ── Debug types ── */

export interface DebugError {
  message: string;
  type?: string;
  stack?: string;
}

export interface FixSuggestion {
  title: string;
  description: string;
}

/* ── Review types ── */

export interface ReviewFile {
  path: string;
  diff: string;
  status: "pending" | "accepted" | "rejected";
  comments: Array<{ line: number; text: string }>;
}

/* ── Terminal types ── */

export interface TerminalLine {
  id: string;
  type: "input" | "output" | "system";
  text: string;
  timestamp: number;
}
