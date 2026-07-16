import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ── Types ── */

export interface WorkingMemoryEntry {
  id: string;
  type: "decision" | "progress" | "todo" | "reflection";
  content: string;
  metadata: Record<string, unknown>;
  timestamp: number;
}

export interface SubTaskItem {
  id: string;
  name: string;
  description: string;
  depends_on: string[];
  estimated_effort: string;
  acceptance_criteria: string[];
  status: "pending" | "running" | "completed" | "failed";
  result: string | null;
  error: string | null;
  started_at: number | null;
  completed_at: number | null;
}

export interface ManagerStatus {
  goal: string;
  total: number;
  status_counts: {
    pending?: number;
    running?: number;
    completed?: number;
    failed?: number;
  };
  ready: SubTaskItem[];
  all: SubTaskItem[];
}

export interface MemoryResponse {
  entries: WorkingMemoryEntry[];
  count: number;
  summary: string;
  pending: string[];
}

export interface LessonItem {
  id: string;
  content: string;
  type: string;
  timestamp: number;
}

export interface TerminalResult {
  stdout: string;
  stderr: string;
  exit_code: number;
}

export interface ContextResult {
  fable_context: string;
  working_memory_summary: string;
  conversation_id: string;
}

/* ── Helper: build params with optional conversation_id ── */

function withConv(
  params: Record<string, unknown>,
  convId?: string,
): Record<string, unknown> {
  if (convId) params.conversation_id = convId;
  return params;
}

/* ── WebSocket helper ── */

export type WsStateMessage = {
  type: "state_snapshot" | "state_update";
  manager: ManagerStatus;
  memory: MemoryResponse;
  lessons: LessonItem[];
  ts: number;
};

export function openOrchestrationWs(
  conversationId: string,
  onMessage: (msg: WsStateMessage) => void,
  onError?: (err: Event) => void,
): WebSocket {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const { host } = window.location;
  const ws = new WebSocket(
    `${protocol}//${host}/api/orchestration/ws/${conversationId}`,
  );
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as WsStateMessage;
      onMessage(msg);
    } catch {
      /* ignore parse errors */
    }
  };
  if (onError) ws.onerror = onError;
  return ws;
}

/* ── API Service ── */

export class OrchestrationApi {
  /* Working Memory */
  static async getMemory(
    entryType?: string,
    limit = 20,
    conversationId?: string,
  ): Promise<MemoryResponse> {
    const { data } = await api.get<MemoryResponse>("/orchestration/memory", {
      params: withConv({ entry_type: entryType, limit }, conversationId),
    });
    return data;
  }

  static async addMemory(
    entryType: string,
    content: string,
    metadata?: Record<string, unknown>,
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/memory", {
      entry_type: entryType,
      content,
      metadata,
      conversation_id: conversationId,
    });
    return data;
  }

  static async addDecision(
    decision: string,
    context = "",
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/memory/decision", {
      decision,
      context,
      conversation_id: conversationId,
    });
    return data;
  }

  static async addReflection(
    summary: string,
    tags?: string[],
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/memory/reflection", {
      summary,
      tags,
      conversation_id: conversationId,
    });
    return data;
  }

  static async getMemorySummary(
    conversationId?: string,
  ): Promise<{ summary: string }> {
    const { data } = await api.get("/orchestration/memory/summary", {
      params: withConv({}, conversationId),
    });
    return data;
  }

  static async clearMemory(conversationId?: string) {
    const { data } = await api.delete("/orchestration/memory", {
      params: withConv({}, conversationId),
    });
    return data;
  }

  /* Manager Agent */
  static async managerInit(goal: string, conversationId?: string) {
    const { data } = await api.post("/orchestration/manager/init", {
      goal,
      conversation_id: conversationId,
    });
    return data;
  }

  static async managerDecompose(
    subTasks: Array<{
      name: string;
      description: string;
      depends_on?: string[];
      estimated_effort?: string;
      acceptance_criteria?: string[];
    }>,
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/manager/decompose", {
      sub_tasks: subTasks,
      conversation_id: conversationId,
    });
    return data;
  }

  static async getManagerPlan(conversationId?: string): Promise<{
    sub_tasks: SubTaskItem[];
    ready: SubTaskItem[];
  }> {
    const { data } = await api.get("/orchestration/manager/plan", {
      params: withConv({}, conversationId),
    });
    return data;
  }

  static async getManagerStatus(
    conversationId?: string,
  ): Promise<ManagerStatus> {
    const { data } = await api.get<ManagerStatus>(
      "/orchestration/manager/status",
      { params: withConv({}, conversationId) },
    );
    return data;
  }

  static async getManagerSummary(
    conversationId?: string,
  ): Promise<{ summary: string }> {
    const { data } = await api.get("/orchestration/manager/summary", {
      params: withConv({}, conversationId),
    });
    return data;
  }

  static async startTask(taskId: string, conversationId?: string) {
    const { data } = await api.post("/orchestration/manager/start-task", {
      task_id: taskId,
      conversation_id: conversationId,
    });
    return data;
  }

  static async completeTask(
    taskId: string,
    result: string,
    error?: string,
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/manager/complete-task", {
      task_id: taskId,
      result,
      error,
      conversation_id: conversationId,
    });
    return data;
  }

  static async finalizeGoal(
    overallOutcome = "success",
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/manager/finalize", {
      overall_outcome: overallOutcome,
      conversation_id: conversationId,
    });
    return data;
  }

  /* Self-Memory Loop */
  static async getLessons(
    limit = 10,
    conversationId?: string,
  ): Promise<{ lessons: LessonItem[]; count: number }> {
    const { data } = await api.get("/orchestration/lessons", {
      params: withConv({ limit }, conversationId),
    });
    return data;
  }

  static async reflect(
    taskDescription: string,
    outcome: string,
    observations: string,
    tags?: string[],
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/reflect", {
      task_description: taskDescription,
      outcome,
      observations,
      tags,
      conversation_id: conversationId,
    });
    return data;
  }

  /* P1: Terminal */
  static async terminalExec(
    command: string,
    conversationId?: string,
  ): Promise<TerminalResult> {
    const { data } = await api.post<TerminalResult>(
      "/orchestration/terminal/exec",
      { command, conversation_id: conversationId },
    );
    return data;
  }

  static async terminalHistory(
    limit = 20,
    conversationId?: string,
  ): Promise<{
    history: Array<{
      cmd: string;
      stdout: string;
      exit_code: number;
      ts: number;
    }>;
    count: number;
  }> {
    const { data } = await api.get("/orchestration/terminal/history", {
      params: withConv({ limit }, conversationId),
    });
    return data;
  }

  /* P3: Context */
  static async getContext(
    query = "",
    conversationId?: string,
  ): Promise<ContextResult> {
    const { data } = await api.get<ContextResult>("/orchestration/context", {
      params: withConv({ query }, conversationId),
    });
    return data;
  }

  static async injectContext(
    injectInto = "system_prompt",
    conversationId?: string,
  ) {
    const { data } = await api.post("/orchestration/context/inject", {
      inject_into: injectInto,
      conversation_id: conversationId,
    });
    return data;
  }

  /* Session management */
  static async closeSession(conversationId: string) {
    const { data } = await api.delete(
      `/orchestration/session/${conversationId}`,
    );
    return data;
  }

  static async listSessions(): Promise<{
    sessions: string[];
    count: number;
  }> {
    const { data } = await api.get("/orchestration/sessions");
    return data;
  }
}
