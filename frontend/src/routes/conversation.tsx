import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router";
import { FileTree, type FileNode } from "#/components/ide/FileTree";

import { Button } from "#/components/ui/Button";
import { ConversationApi } from "#/api/conversation-service/conversation-service.api";
import { useArtifacts } from "#/components/layout/ArtifactsContext";
import { useMode } from "#/components/layout/ModeContext";
import { suggestMode, type ModeId } from "#/types/mode";
import { AgentTimeline } from "#/components/ui/AgentTimeline";
import { PlanView } from "#/components/ui/PlanView";
import { IDEWorkspace } from "#/components/ide/IDEWorkspace";
import { StackTraceViewer } from "#/components/ui/StackTraceViewer";
import type {
  FixSuggestion,
  ReviewFile,
  Message,
  TimelineEvent,
  PlanStep,
  DebugError,
  TerminalLine,
} from "#/types/conversation";
import { ReviewWorkspace } from "#/components/ui/ReviewWorkspace";
import { AutonomousOrchestrator } from "#/components/ui/AutonomousOrchestrator";
import { MessageBubble } from "#/components/conversation/MessageBubble";
import { ErrorBoundary } from "#/components/ErrorBoundary";
import { ThinkingPanel, type ThinkingStep } from "#/components/ui/ThinkingPanel";
import { Terminal } from "#/components/Terminal";
import { SuggestionTextarea } from "#/components/conversation/SuggestionTextarea";

import { useConversationWebSocket } from "#/hooks/use-conversation-websocket";

/* ── Page Component ── */
export default function ConversationPage() {
  return (
    <ErrorBoundary>
      <ConversationContent />
    </ErrorBoundary>
  );
}

function ConversationContent() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const artifacts = useArtifacts();
  const { mode: contextMode } = useMode();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [focused, setFocused] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversation, setConversation] = useState<{
    sessionApiKey: string;
    agentServerUrl: string;
    sandboxStatus: string;
    executionStatus?: string | null;
    title?: string | null;
  } | null>(null);
  const [needsResume, setNeedsResume] = useState(false);
  const [isResuming, setIsResuming] = useState(false);

  /* ── Mode state ── */
  const [selectedMode, setSelectedMode] = useState<ModeId>(contextMode);
  const [autoMode] = useState(true);
  const [autoModeFlash, setAutoModeFlash] = useState<string | null>(null);
  const [showAgentPanel, setShowAgentPanel] = useState(false);

  /* ── Thinking / CoT state ── */
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [thinkingCollapsed, setThinkingCollapsed] = useState(false);

  /* ── Terminal visibility ── */
  const [showChatTerminal, setShowChatTerminal] = useState(false);

  /* ── Inline suggestion for chat input ── */
  const [inputSuggestion, setInputSuggestion] = useState<string | null>(null);

  /* Generate input suggestions from agent context */
  useEffect(() => {
    if (!input.trim() || isRunning) {
      setInputSuggestion(null);
      return;
    }
    const lastMsg = messages[messages.length - 1];
    if (!lastMsg || lastMsg.role === "user") {
      setInputSuggestion(null);
      return;
    }
    /* Suggest mode-appropriate follow-ups based on last agent message */
    const content = lastMsg.content.toLowerCase();
    if (content.includes("fix") || content.includes("error")) {
      setInputSuggestion(" and test it");
    } else if (content.includes("plan")) {
      setInputSuggestion(null);
    } else if (content.includes("review") || content.includes("diff")) {
      setInputSuggestion(" and apply the changes");
    } else if (input.startsWith("build") || input.startsWith("create")) {
      setInputSuggestion(" a React component");
    } else if (input.startsWith("refactor") || input.startsWith("optimize")) {
      setInputSuggestion(" the codebase");
    } else {
      setInputSuggestion(null);
    }
  }, [input, messages, isRunning]);

  /* ── Timeline ── */
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const timelineEventIdRef = useRef(0);

  /* ── Plan mode ── */
  const [planSteps, setPlanSteps] = useState<PlanStep[]>([]);
  const [pendingInput, setPendingInput] = useState<string | null>(null);

  /* ── Debug mode state ── */
  const [debugError, setDebugError] = useState<DebugError | null>(null);
  const [debugFixes, setDebugFixes] = useState<FixSuggestion[]>([]);

  /* ── Review mode state ── */
  const [reviewFiles, setReviewFiles] = useState<ReviewFile[]>([]);
  const [reviewOverallStatus, setReviewOverallStatus] = useState<
    "pending" | "approved" | "changes-requested"
  >("pending");

  /* ── IDE workspace state ── */
  const [workspaceFiles, setWorkspaceFiles] = useState<FileNode[]>([
    { name: "src", path: "src", type: "folder", children: [] },
    { name: "package.json", path: "package.json", type: "file" },
  ]);
  const [terminalLines, setTerminalLines] = useState<TerminalLine[]>([
    {
      id: "welcome",
      type: "system",
      text: "Wren Terminal v1.0 — Type 'help' for available commands",
      timestamp: Date.now(),
    },
  ]);

  /* ── Refs ── */
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /* ── WebSocket hook ── */
  const { connectWebSocket, sendCommand } = useConversationWebSocket({
    state: conversation
      ? {
          conversationId: conversationId!,
          ...conversation,
          sandboxStatus: conversation.sandboxStatus,
        }
      : null,
    handlers: {
      onMessage: (msg) =>
        setMessages((prev) =>
          prev.some((m) => m.id === msg.id) ? prev : [...prev, msg],
        ),
      onUpdateMessage: (updater) => setMessages(updater),
      onTimelineEvent: (event) => {
        setTimelineEvents((prev) => [
          ...prev,
          {
            ...event,
            id: `tl-${timelineEventIdRef.current++}`,
            timestamp: new Date(),
          },
        ]);
        // Extract agent thinking from action events with thoughts
        const detail = event.detail;
        if (detail && event.type === "action") {
          setThinkingSteps((prev) => [
            ...prev,
            {
              id: `think-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
              timestamp: Date.now(),
              type: "reasoning",
              title: event.title || "Agent reasoning",
              content: detail,
            },
          ]);
        }
      },
      onError: (err) => {
        setError(err || null);
        if (err) {
          setThinkingSteps((prev) => [
            ...prev,
            {
              id: `think-err-${Date.now()}`,
              timestamp: Date.now(),
              type: "error",
              title: "Error",
              content: err || "An error occurred",
            },
          ]);
        }
      },
      onRunningChange: setIsRunning,
      onModeSuggested: (mode) => setSelectedMode(mode),
      onModeFlash: (mode) => {
        setAutoModeFlash(mode);
        setTimeout(() => setAutoModeFlash(null), 2000);
      },
      onPlanSteps: setPlanSteps,
      onDebugError: setDebugError,
      onDebugFixes: setDebugFixes,
      onReviewFile: (file) =>
        setReviewFiles((prev) =>
          prev.some((f) => f.path === file.path) ? prev : [...prev, file],
        ),
      onWorkspaceFile: (path) =>
        setWorkspaceFiles((prev) =>
          prev.some((f) => f.path === path)
            ? prev
            : [
                ...prev,
                {
                  name: path.split("/").pop() || path,
                  path,
                  type: "file" as const,
                },
              ],
        ),
      onTerminalLine: (line) => setTerminalLines((prev) => [...prev, line]),
      onArtifactsCode: (code) => artifacts.setCode(code),
      onArtifactsTerminal: (text) => artifacts.appendTerminal(text),
      onArtifactsOpen: () => artifacts.setOpen(true),
    },
    selectedMode,
    autoMode,
    reviewFiles,
  });

  /* ── Auto-suggest mode ── */
  useEffect(() => {
    if (input && !isRunning) {
      const suggested = suggestMode(input);
      if (suggested && suggested !== selectedMode) {
        setSelectedMode(suggested);
      }
    }
  }, [input, isRunning, selectedMode]);

  /* ── Scroll to bottom ── */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /* ── Initialize connection ── */
  useEffect(() => {
    if (!conversationId) return;
    let mounted = true;

    async function init() {
      try {
        setIsConnecting(true);
        setError(null);
        const token = localStorage.getItem("token");
        const response = await fetch(
          `/api/v1/app-conversations/${conversationId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        if (!mounted) return;
        if (response.ok) {
          const data = await response.json();
          const convState = {
            sessionApiKey: data.session_api_key || "",
            agentServerUrl: data.conversation_url || "",
            sandboxStatus: data.sandbox_status,
            executionStatus: data.execution_status,
            title: data.title,
          };
          setConversation(convState);
          if (data.sandbox_status === "RUNNING") {
            connectWebSocket(convState.agentServerUrl, convState.sessionApiKey);
          } else {
            setIsConnecting(false);
            setNeedsResume(true);
          }
        } else if (response.status === 404) {
          setError("Conversation not found");
          setIsConnecting(false);
        } else {
          setError("Failed to load conversation");
          setIsConnecting(false);
        }
      } catch {
        if (mounted) {
          setError("Failed to load conversation");
          setIsConnecting(false);
        }
      }
    }
    init();
    return () => {
      mounted = false;
    };
  }, [conversationId, connectWebSocket]);

  /* ── Send message ── */
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || !conversationId || isRunning) return;
      const trimmed = text.trim();
      setInput("");

      // Plan mode: hold as pending for approval
      if (selectedMode === "plan") {
        setPendingInput(trimmed);
        setPlanSteps([
          {
            id: "step-1",
            title: "Analyze request",
            description: `Understanding: "${trimmed.slice(0, 100)}"`,
            files: [],
            riskLevel: "low",
          },
          {
            id: "step-2",
            title: "Identify affected files",
            description: "Scan codebase for relevant files and dependencies",
            files: [],
            riskLevel: "medium",
          },
        ]);
        setMessages((prev) => [
          ...prev,
          {
            id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
            role: "user",
            content: trimmed,
            timestamp: new Date(),
            mode: selectedMode,
          },
        ]);
        return;
      }

      // Reset thinking + mode-specific state on new message
      setThinkingSteps([]);
      if (selectedMode === "debug") {
        setDebugError(null);
        setDebugFixes([]);
      }
      if (selectedMode === "review") {
        setReviewFiles([]);
        setReviewOverallStatus("pending");
      }

      setIsRunning(true);
      setError(null);
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
          role: "user",
          content: trimmed,
          timestamp: new Date(),
          mode: selectedMode,
        },
      ]);
      try {
        await ConversationApi.sendMessage(conversationId, trimmed);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to send message");
        setIsRunning(false);
      }
    },
    [conversationId, isRunning, selectedMode],
  );

  /* ── Plan approve/reject ── */
  const handlePlanApprove = useCallback(async () => {
    if (!pendingInput || !conversationId) return;
    setPlanSteps([]);
    setPendingInput(null);
    setIsRunning(true);
    setError(null);
    try {
      await ConversationApi.sendMessage(conversationId, pendingInput);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      setIsRunning(false);
    }
  }, [pendingInput, conversationId]);

  const handlePlanReject = useCallback(() => {
    setPlanSteps([]);
    setPendingInput(null);
    setIsRunning(false);
    setMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}-sys`,
        role: "system",
        content: "Plan rejected. Rephrase your request.",
        timestamp: new Date(),
      },
    ]);
  }, []);

  /* ── Autonomous mode: auto-approve plan ── */
  useEffect(() => {
    if (
      selectedMode === "autonomous" &&
      planSteps.length > 0 &&
      pendingInput &&
      !isRunning
    ) {
      setPlanSteps([]);
      setPendingInput(null);
      setIsRunning(true);
      setError(null);
      ConversationApi.sendMessage(conversationId!, input).catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to send message");
        setIsRunning(false);
      });
    }
  }, [selectedMode, planSteps.length, pendingInput, isRunning, conversationId]);

  /* ── Input handlers ── */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input);
      }
    },
    [sendMessage, input],
  );

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      const el = e.target;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    },
    [],
  );

  /* ── Resume ── */
  const handleResume = useCallback(async () => {
    if (
      !conversationId ||
      !conversation?.agentServerUrl ||
      !conversation?.sessionApiKey
    )
      return;
    setIsResuming(true);
    setError(null);
    try {
      await ConversationApi.resumeConversation(conversationId);
      connectWebSocket(conversation.agentServerUrl, conversation.sessionApiKey);
      setNeedsResume(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resume");
    } finally {
      setIsResuming(false);
    }
  }, [conversationId, conversation, connectWebSocket]);

  const isCodeMode = selectedMode === "code" || selectedMode === "vibe-code";

  const handleTerminalCommand = useCallback(
    (cmd: string) => {
      setTerminalLines((prev) => [
        ...prev,
        {
          id: `cmd-${Date.now()}`,
          type: "input",
          text: `$ ${cmd}`,
          timestamp: Date.now(),
        },
      ]);
      sendCommand(cmd);
    },
    [sendCommand],
  );

  /* ── Loading ── */
  if (isConnecting && !conversation) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4 animate-fade-in-up">
          <div
            className="flex h-12 w-12 items-center justify-center rounded-xl animate-pulse-glow"
            style={{
              background:
                "linear-gradient(135deg, var(--accent), var(--accent-hover))",
              boxShadow:
                "0 0 24px color-mix(in srgb, var(--accent) 30%, transparent)",
            }}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
            Loading conversation...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col" data-testid="conversation-screen">
      {isCodeMode ? (
        /* ── IDE Layout: sidebar + editor + agent panel ── */
        <div className="flex flex-1 overflow-hidden">
          {/* ── Left: Files sidebar ── */}
          <div className="w-64 shrink-0 border-r overflow-y-auto" style={{ borderColor: "var(--border)", background: "color-mix(in srgb, var(--surface) 90%, transparent)" }}>
            <FileTree
              files={workspaceFiles}
              onOpenFile={(path) => {
                /* open file in editor - placeholder */
              }}
              editable={true}
              viewMode="tree"
            />
          </div>

          {/* ── Center: Code editor ── */}
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
            <IDEWorkspace
              files={workspaceFiles}
              timelineEvents={timelineEvents}
              terminalLines={terminalLines}
              onTerminalCommand={handleTerminalCommand}
            />
          </div>

          {/* ── Right: Agent panel ── */}
          {showAgentPanel && (
            <div
              className="w-80 shrink-0 border-l overflow-y-auto"
              style={{
                borderColor: "var(--border)",
                background: "color-mix(in srgb, var(--surface) 80%, transparent)",
              }}
            >
              <AutonomousOrchestrator
                goal={messages.find((m) => m.role === "user")?.content || "Build the requested feature"}
                conversationId={conversationId}
              />
            </div>
          )}
        </div>
      ) : (
        /* ── Chat Layout: chat + agent panel ── */
        <div className="flex h-full">
          {/* ── Left: Chat Area ── */}
          <div className="flex flex-1 flex-col min-w-0">
            {/* ── Chat messages ── */}
            {selectedMode === "review" && reviewFiles.length > 0 ? (
              <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="mx-auto max-w-3xl animate-fade-in-up">
                  <ReviewWorkspace
                    files={reviewFiles}
                    onAcceptFile={(path) => {
                      setReviewFiles((prev) =>
                        prev.map((f) =>
                          f.path === path ? { ...f, status: "accepted" } : f,
                        ),
                      );
                    }}
                    onRejectFile={(path) => {
                      setReviewFiles((prev) =>
                        prev.map((f) =>
                          f.path === path ? { ...f, status: "rejected" } : f,
                        ),
                      );
                    }}
                    onApproveAll={() => {
                      setReviewOverallStatus("approved");
                      setReviewFiles((prev) =>
                        prev.map((f) => ({ ...f, status: "accepted" as const })),
                      );
                    }}
                    onRejectAll={() => {
                      setReviewOverallStatus("changes-requested");
                      setReviewFiles((prev) =>
                        prev.map((f) => ({ ...f, status: "rejected" as const })),
                      );
                    }}
                    overallStatus={reviewOverallStatus}
                  />
                </div>
              </div>
            ) : selectedMode === "debug" && debugError ? (
              <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="mx-auto max-w-3xl animate-fade-in-up">
                  <StackTraceViewer
                    errorMessage={debugError.message}
                    errorType={debugError.type}
                    rawStack={debugError.stack}
                    fixSuggestions={debugFixes}
                  />
                </div>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="mx-auto max-w-3xl">
                  <div className="flex flex-col gap-4">
                    {/* Timeline (collapsible) */}
                    {timelineEvents.length > 0 && (
                      <div className="mb-2 animate-fade-in-up">
                        <AgentTimeline events={timelineEvents} />
                      </div>
                    )}

                    {/* Thinking / Chain-of-Thought panel */}
                    {thinkingSteps.length > 0 && (
                      <div className="animate-fade-in-up">
                        <ThinkingPanel
                          steps={thinkingSteps}
                          collapsed={thinkingCollapsed}
                          onToggleCollapse={() => setThinkingCollapsed((c) => !c)}
                        />
                      </div>
                    )}

                    {/* Plan steps shown inline for plan/debug */}
                    {planSteps.length > 0 && (
                      <div className="mb-2 animate-fade-in-up">
                        <PlanView
                          steps={planSteps}
                          onApprove={handlePlanApprove}
                          onReject={handlePlanReject}
                        />
                      </div>
                    )}

                    {messages.length === 0 ? (
                      <>
                        <div className="glass-bubble animate-fade-in-up max-w-[85%] self-start p-4">
                          <p
                            className="text-sm leading-relaxed"
                            style={{
                              color: "var(--text-primary)",
                              fontWeight: 480,
                            }}
                          >
                            I'm ready to help. What would you like me to work on?
                          </p>
                        </div>
                        <div
                          className="animate-fade-in-up max-w-[85%] self-end rounded-2xl p-4"
                          style={{
                            background:
                              "color-mix(in srgb, var(--accent) 15%, transparent)",
                            border:
                              "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
                            backdropFilter: "blur(12px)",
                          }}
                        >
                          <p
                            className="text-sm leading-relaxed"
                            style={{
                              color: "var(--text-primary)",
                              fontWeight: 480,
                            }}
                          >
                            Build a React component for a glassmorphism card
                          </p>
                        </div>
                      </>
                    ) : (
                      messages.map((message) => (
                        <MessageBubble key={message.id} message={message} />
                      ))
                    )}

                    {isRunning && (
                      <div className="flex items-center gap-2 px-4 py-2">
                        <div className="flex items-center gap-1">
                          {[0, 1, 2].map((i) => (
                            <span
                              key={i}
                              className="inline-block h-1.5 w-1.5 rounded-full animate-pulse-glow"
                              style={{
                                background: "var(--accent)",
                                boxShadow:
                                  "0 0 12px color-mix(in srgb, var(--accent) 30%, transparent)",
                              }}
                            />
                          ))}
                        </div>
                        <span
                          className="text-xs"
                          style={{ color: "var(--text-subtle)" }}
                        >
                          Thinking
                        </span>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>
                </div>
              </div>
            )}

            {/* Error banner */}
            {error && (
              <div className="mx-auto max-w-3xl px-4 pb-4">
                <div
                  className="card border-error/30 p-4"
                  style={{ borderColor: "var(--error)" }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm" style={{ color: "var(--error)" }}>
                      {error}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setError(null)}
                    >
                      Dismiss
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* ── Toggleable Terminal (chat mode) ── */}
            {showChatTerminal && (
              <div className="shrink-0 px-6 pb-2 animate-fade-in-up">
                <div className="mx-auto max-w-3xl">
                  <Terminal
                    lines={terminalLines}
                    onCommand={handleTerminalCommand}
                    height={200}
                  />
                </div>
              </div>
            )}

            {/* ── Chat input ── */}
            <div className="shrink-0 px-6 pb-6 pt-1">
              <div className="mx-auto max-w-3xl">
                <div
                  className="glass-input relative overflow-hidden transition-all duration-300"
                  style={{
                    borderColor: focused
                      ? "color-mix(in srgb, var(--accent) 50%, transparent)"
                      : "var(--border-strong)",
                    boxShadow: focused
                      ? "0 0 0 1px color-mix(in srgb, var(--accent) 20%, transparent), var(--shadow-md)"
                      : "var(--shadow-sm), var(--shadow-inner)",
                  }}
                >
                  <div className="flex flex-col">
                    <SuggestionTextarea
                      ref={inputRef}
                      value={input}
                      suggestion={inputSuggestion}
                      onAcceptSuggestion={() => {
                        if (inputSuggestion) {
                          setInput((prev) => prev + inputSuggestion);
                          setInputSuggestion(null);
                          // Focus back after accepting
                          setTimeout(() => inputRef.current?.focus(), 0);
                        }
                      }}
                      onChange={handleInput}
                      onKeyDown={handleKeyDown}
                      onFocus={() => setFocused(true)}
                      onBlur={() => setFocused(false)}
                      placeholder={isRunning ? "Agent is working..." : "Type a message..."}
                      rows={1}
                      disabled={isRunning || planSteps.length > 0}
                      className="w-full resize-none border-none bg-transparent px-4 py-3.5 text-sm leading-relaxed outline-none placeholder:select-none"
                      style={{
                        color: "var(--text-primary)",
                        caretColor: "var(--accent)",
                      }}
                    />
                    <div
                      className="flex items-center justify-between px-3 py-2"
                      style={{ borderTop: "1px solid var(--border)" }}
                    >
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => setShowChatTerminal(!showChatTerminal)}
                          className="press flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium"
                          style={{
                            background: showChatTerminal
                              ? "color-mix(in srgb, var(--accent) 10%, transparent)"
                              : "transparent",
                            color: showChatTerminal
                              ? "var(--accent)"
                              : "var(--text-muted)",
                          }}
                          title="Toggle terminal"
                        >
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 12 12"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <path d="M1.5 2.5l3 3-3 3M5.5 8.5h4" />
                          </svg>
                          Terminal
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowAgentPanel(!showAgentPanel)}
                          className="press flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium"
                          style={{
                            background: showAgentPanel
                              ? "color-mix(in srgb, var(--accent) 10%, transparent)"
                              : "transparent",
                            color: showAgentPanel
                              ? "var(--accent)"
                              : "var(--text-muted)",
                          }}
                          title="Toggle agent activity panel"
                        >
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 12 12"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                          >
                            <circle cx="6" cy="6" r="4.5" />
                            <path d="M6 3.5v5M3.5 6h5" />
                          </svg>
                          Agent
                        </button>
                        {autoModeFlash && (
                          <div
                            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium animate-fade-in-up"
                            style={{
                              background:
                                "color-mix(in srgb, var(--accent) 12%, transparent)",
                              color: "var(--accent)",
                              border:
                                "1px solid color-mix(in srgb, var(--accent) 15%, transparent)",
                            }}
                          >
                            Auto
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          onClick={() => sendMessage(input)}
                          disabled={
                            !input.trim() || isRunning || planSteps.length > 0
                          }
                          className="btn-accent h-8 gap-1.5 px-3 text-xs font-semibold"
                        >
                          {isRunning ? (
                            <>
                              <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                              Running
                            </>
                          ) : (
                            <>
                              <svg
                                width="14"
                                height="14"
                                viewBox="0 0 14 14"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              >
                                <path d="M12 7l-4-4-4 4M12 6l-4-4-4 4" />
                              </svg>
                              Send
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Resume banner */}
            {(needsResume ||
              (conversation?.sandboxStatus &&
                conversation.sandboxStatus !== "RUNNING")) && (
              <div className="mx-auto max-w-3xl px-6 pt-2">
                <div className="card gradient-accent-border p-4">
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div>
                      <p
                        className="text-sm font-medium"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {conversation?.title || "Conversation"} is not running
                      </p>
                      <p
                        className="text-xs"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        {conversation?.sandboxStatus === "MISSING"
                          ? "The sandbox no longer exists. Start a new conversation to continue."
                          : "Click Resume to reconnect and continue where you left off."}
                      </p>
                    </div>
                    <Button
                      onClick={handleResume}
                      disabled={isResuming}
                      className="whitespace-nowrap"
                    >
                      {isResuming ? "Resuming..." : "Resume"}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}