import { useCallback, useEffect, useRef } from "react";
import type { WebSocketEvent, TimelineEvent, Message } from "#/types/conversation";
import type { ModeId } from "#/types/mode";
import type { FixSuggestion } from "#/types/conversation";
import type { ReviewFile } from "#/types/conversation";
import type { FileNode } from "#/components/ide/FileTree";
import type { PlanStep } from "#/types/conversation";
import type { DebugError } from "#/types/conversation";
import type { TerminalLine } from "#/types/conversation";

interface ConversationState {
  conversationId: string;
  agentServerUrl: string;
  sessionApiKey: string;
  sandboxStatus: string;
}

interface WebSocketHandlers {
  onMessage: (msg: Message) => void;
  onUpdateMessage: (updater: (prev: Message[]) => Message[]) => void;
  onTimelineEvent: (event: Omit<TimelineEvent, "id" | "timestamp">) => void;
  onError: (error: string) => void;
  onRunningChange: (isRunning: boolean) => void;
  onModeSuggested: (mode: ModeId) => void;
  onModeFlash: (mode: string) => void;
  onPlanSteps: (steps: PlanStep[]) => void;
  onDebugError: (error: DebugError) => void;
  onDebugFixes: (fixes: FixSuggestion[]) => void;
  onReviewFile: (file: ReviewFile) => void;
  onWorkspaceFile: (path: string) => void;
  onTerminalLine: (line: TerminalLine) => void;
  onArtifactsCode: (code: string) => void;
  onArtifactsTerminal: (text: string) => void;
  onArtifactsOpen: () => void;
}

interface UseConversationWebSocketOptions {
  state: ConversationState | null;
  handlers: WebSocketHandlers;
  selectedMode: ModeId;
  autoMode: boolean;
  reviewFiles: ReviewFile[];
}

export function useConversationWebSocket({
  state,
  handlers,
  selectedMode,
  autoMode,
  reviewFiles,
}: UseConversationWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const eventIdRef = useRef(0);
  const timelineEventIdRef = useRef(0);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;
  const selectedModeRef = useRef(selectedMode);
  selectedModeRef.current = selectedMode;
  const autoModeRef = useRef(autoMode);
  autoModeRef.current = autoMode;

  const addTimelineEvent = useCallback((event: Omit<TimelineEvent, "id" | "timestamp">) => {
    handlersRef.current.onTimelineEvent(event);
  }, []);

  const handleWebSocketMessage = useCallback((data: WebSocketEvent) => {
    const h = handlersRef.current;
    const currentMode = selectedModeRef.current;
    const isAutoMode = autoModeRef.current;

    switch (data.type) {
      case "message":
        if (data.message?.role === "user") {
          const content = data.message.content.map((c) => c.text).join("");
          h.onMessage({
            id: `${Date.now()}-${eventIdRef.current++}`,
            role: "user",
            content,
            timestamp: new Date(),
          });
        } else if (data.message?.role === "assistant") {
          const content = data.message.content.map((c) => c.text).join("");
          h.onUpdateMessage((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && last.isLoading) {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: content || last.content,
                isLoading: false,
              };
              return updated;
            }
            if (content) {
              return [
                ...prev,
                {
                  id: `${Date.now()}-${eventIdRef.current++}`,
                  role: "assistant" as const,
                  content,
                  timestamp: new Date(),
                },
              ];
            }
            return prev;
          });
          addTimelineEvent({
            type: "message",
            title:
              data.message.content
                .map((c) => c.text?.slice(0, 80))
                .join("")
                .trim() || "Response",
            status: "done",
          });
        }
        break;

      case "action": {
        const actionType = data.action?.action_type || "task";
        const title = data.action?.title || actionType;

        addTimelineEvent({
          type: "action",
          actionType,
          title,
          detail: data.action?.thought,
          status: "running",
        });

        // In plan mode, extract plan steps from action
        if (currentMode === "plan" && data.action?.thought?.toLowerCase().includes("plan:")) {
          const thought = data.action.thought;
          const steps: PlanStep[] = [];
          const stepRegex = /\d+\.\s+\*\*(.+?)\*\*(?:\s*[–—]\s*(.+?))?(?=\n\d+\.|\n*$)/gs;
          let match;
          while ((match = stepRegex.exec(thought)) !== null) {
            steps.push({
              id: `step-${steps.length + 1}`,
              title: match[1].trim(),
              description: (match[2] || "").trim(),
              files: [],
              riskLevel: "low",
            });
          }
          if (steps.length > 0) h.onPlanSteps(steps);
        }

        h.onMessage({
          id: `${Date.now()}-${eventIdRef.current++}`,
          role: "assistant",
          content: data.action?.thought || title,
          timestamp: new Date(),
          actionType,
          actionTitle: title,
          isLoading: true,
        });
        break;
      }

      case "observation": {
        const obsContent = data.observation?.content || "";

        h.onUpdateMessage((prev) => {
          let idx = -1;
          for (let i = prev.length - 1; i >= 0; i--) {
            if (prev[i].isLoading) {
              idx = i;
              break;
            }
          }
          if (idx >= 0) {
            const updated = [...prev];
            updated[idx] = { ...updated[idx], content: obsContent, isLoading: false };
            return updated;
          }
          return prev;
        });
        addTimelineEvent({
          type: "observation",
          title: obsContent.slice(0, 80),
          detail: obsContent,
          status: "done",
        });

        // Pipe terminal output
        if (obsContent.includes("$ ") || obsContent.includes("> ")) {
          h.onArtifactsTerminal(obsContent);
          h.onTerminalLine({
            id: `term-${Date.now()}`,
            type: "output",
            text: obsContent,
            timestamp: Date.now(),
          });
        }

        // Pipe code diffs to artifacts + IDE files
        const extractedCode = data.observation?.extracted_code;
        if (extractedCode) {
          h.onArtifactsCode(extractedCode);
          const filenameMatch =
            obsContent.match(/(?:file|path):\s*(.+?)(?:\n|$)/i) ||
            obsContent.match(/^\/\/\s*(.+?\.\w+)/);
          if (filenameMatch) {
            h.onWorkspaceFile(filenameMatch[1].trim());
          }
        }

        // Auto-open artifacts on code
        if (extractedCode) {
          h.onArtifactsOpen();
        }

        // Track review files from diff observations
        if (
          currentMode === "review" &&
          (obsContent.includes("diff --git") || obsContent.includes("--- ") || obsContent.includes("+++ "))
        ) {
          const pathMatch = obsContent.match(/diff --git a\/(.+) b\/(.+)/);
          const filePath = pathMatch?.[2] || pathMatch?.[1] || `file-${reviewFiles.length + 1}`;
          h.onReviewFile({
            path: filePath,
            diff: obsContent,
            status: "pending",
            comments: [],
          });
        }

        // Track debug data from error observations
        if (currentMode === "debug" && (obsContent.includes("Error:") || obsContent.includes("Traceback"))) {
          const errMsg = obsContent.match(/Error:\s*(.+?)(?:\n|$)/)?.[1] || obsContent.slice(0, 200);
          h.onDebugError({
            message: errMsg,
            type: obsContent.includes("Traceback") ? "Traceback" : "RuntimeError",
            stack: obsContent,
          });
          const lines = obsContent.split("\n").filter((l) => l.includes("suggestion") || l.includes("fix") || l.includes("tip:"));
          if (lines.length > 0) {
            h.onDebugFixes(
              lines.map((l) => ({
                title: "Suggested Fix",
                description: l.replace(/^(suggestion|fix|tip):\s*/i, ""),
              }))
            );
          }
        }
        break;
      }

      case "error": {
        const errMsg = data.error?.detail || "An error occurred";
        h.onError(errMsg);
        addTimelineEvent({
          type: "error",
          title: errMsg,
          status: "error",
        });
        break;
      }

      case "status":
        if (data.status?.execution_status === "running") {
          h.onRunningChange(true);
        } else if (
          ["awaiting_user_input", "paused", "stopped"].includes(data.status?.execution_status ?? "")
        ) {
          h.onRunningChange(false);
        }
        addTimelineEvent({
          type: "status",
          title: `Status: ${data.status?.execution_status}`,
          status: data.status?.execution_status === "running" ? "running" : "done",
        });
        break;

      default:
        break;
    }
  }, [addTimelineEvent, reviewFiles]);

  const connectWebSocket = useCallback(
    (agentServerUrl: string, sessionApiKey: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const conversationId = state?.conversationId;
      if (!conversationId) return;

      const wsUrl = `${agentServerUrl.replace("http", "ws")}/sockets/events/${conversationId}?session_api_key=${sessionApiKey}&resend_mode=all`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        handlersRef.current.onError("");
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data: WebSocketEvent = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch {
          /* noop */
        }
      };

      wsRef.current.onerror = () => {
        handlersRef.current.onError("Connection error. Retrying...");
      };

      wsRef.current.onclose = () => {
        handlersRef.current.onError("Disconnected. Attempting to reconnect...");
        reconnectTimeoutRef.current = setTimeout(() => {
          if (agentServerUrl && sessionApiKey) {
            connectWebSocket(agentServerUrl, sessionApiKey);
          }
        }, 3000);
      };
    },
    [handleWebSocketMessage, state?.conversationId],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, []);

  const sendCommand = useCallback((cmd: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: "run",
          args: { command: cmd },
          message_id: `term-${Date.now()}`,
        })
      );
    }
  }, []);

  return { connectWebSocket, sendCommand, wsRef };
}
