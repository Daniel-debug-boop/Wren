import { useEffect, useRef, useCallback } from "react";
import { useWorkspaceStore } from "../store/workspace-store";
import type { AgentState } from "../types";

interface WebSocketPayload {
  content?: string;
  thought?: string;
  type?: string;
  state?: AgentState;
  line?: string;
  message?: string;
  apiKey?: string;
  conversationId?: string;
}

interface WebSocketMessage {
  type:
    "message" | "delta" | "action" | "status" | "terminal" | "file" | "error";
  payload: WebSocketPayload;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  const streamingMessageIdRef = useRef<string | null>(null);
  const {
    addMessage,
    updateMessageContent,
    setAgentState,
    setAgentThought,
    addTerminalLine,
    llmSettings,
  } = useWorkspaceStore();

  // API key resolution: settings page writes to localStorage; fall back to store
  const resolveApiKey = () =>
    localStorage.getItem("wren_llm_api_key") || llmSettings.apiKey || "";

  const handleMessage = useCallback(
    (data: WebSocketMessage) => {
      switch (data.type) {
        case "delta": {
          // Streaming token — append to the in-flight assistant message
          const delta: string = data.payload.content || "";
          if (!streamingMessageIdRef.current) {
            const id = `assistant-${Date.now()}`;
            streamingMessageIdRef.current = id;
            addMessage({
              id,
              role: "assistant",
              content: delta,
              timestamp: Date.now(),
            });
          } else {
            const id = streamingMessageIdRef.current;
            const current = useWorkspaceStore
              .getState()
              .messages.find((m) => m.id === id);
            updateMessageContent(id, (current?.content || "") + delta);
          }
          setAgentState("writing_code");
          break;
        }

        case "message": {
          // Final message — replace streamed content with the complete text
          const content: string = data.payload.content || "";
          const id = streamingMessageIdRef.current || `assistant-${Date.now()}`;
          streamingMessageIdRef.current = null;
          updateMessageContent(id, content);
          setAgentState("complete");
          setAgentThought("");
          break;
        }

        case "action":
          if (data.payload.thought) {
            setAgentThought(data.payload.thought);
          }
          if (data.payload.type === "thinking") {
            setAgentState("thinking");
          } else if (data.payload.type === "writing") {
            setAgentState("writing_code");
          } else if (data.payload.type === "running") {
            setAgentState("running_command");
          }
          break;

        case "status":
          setAgentState(data.payload.state || "idle");
          if (data.payload.thought) {
            setAgentThought(data.payload.thought);
          }
          break;

        case "terminal":
          addTerminalLine(data.payload.line || "");
          break;

        case "error":
          streamingMessageIdRef.current = null;
          addMessage({
            id: `err-${Date.now()}`,
            role: "system",
            content: `Error: ${data.payload.message}`,
            timestamp: Date.now(),
          });
          setAgentState("error");
          setAgentThought("");
          break;

        default:
          break;
      }
    },
    [
      addMessage,
      updateMessageContent,
      setAgentState,
      setAgentThought,
      addTerminalLine,
    ],
  );

  const connect = useCallback(
    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = import.meta.env.VITE_BACKEND_HOST || "127.0.0.1:3000";
      const url = `${protocol}//${host}/ws`;

      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("[Wren] WebSocket connected");
          ws.send(
            JSON.stringify({
              type: "auth",
              payload: { apiKey: resolveApiKey() },
            }),
          );
        };

        ws.onmessage = (event) => {
          try {
            const data: WebSocketMessage = JSON.parse(event.data);
            handleMessage(data);
          } catch {
            console.error("[Wren] Failed to parse WS message");
          }
        };

        ws.onclose = () => {
          console.log("[Wren] WebSocket disconnected, reconnecting in 3s...");
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = (err) => {
          console.error("[Wren] WebSocket error:", err);
        };
      } catch (err) {
        console.error("[Wren] WebSocket connection failed:", err);
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    },
    [llmSettings.apiKey],
  );

  const sendMessage = useCallback(
    (content: string) => {
      const { activeConversationId, createConversation } =
        useWorkspaceStore.getState();
      const conversationId = activeConversationId || createConversation();

      addMessage({
        id: `user-${Date.now()}`,
        role: "user",
        content,
        timestamp: Date.now(),
      });

      setAgentState("thinking");
      setAgentThought("Analyzing your request…");

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "message",
            payload: { content, conversationId },
          }),
        );
      } else {
        // Honest offline notice — no fake responses
        setTimeout(() => {
          addMessage({
            id: `sys-${Date.now()}`,
            role: "system",
            content:
              "⚠️ Backend offline. Start it with: `cd wren && pip install -r requirements.txt && python server.py`",
            timestamp: Date.now(),
          });
          setAgentState("error");
          setAgentThought("");
        }, 400);
      }
    },
    [addMessage, setAgentState, setAgentThought],
  );

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
      clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  return { sendMessage };
}
