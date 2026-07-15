import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { useAppMode } from "#/hooks/use-app-mode";
import { useConfig } from "#/hooks/query/use-config";
import { Button } from "#/components/ui/Button";
import { ConversationApi } from "#/api/conversation-service/conversation-service.api";
import { useArtifacts } from "#/components/layout/ArtifactsContext";
import { useMode } from "#/components/layout/ModeContext";
import { MODES, suggestMode, getModeDef, type ModeId } from "#/types/mode";
import { AgentTimeline } from "#/components/ui/AgentTimeline";
import { PlanView } from "#/components/ui/PlanView";
import { IDEWorkspace } from "#/components/ide/IDEWorkspace";
import type { FileNode } from "#/components/ide/FileTree";
import { StackTraceViewer } from "#/components/ui/StackTraceViewer";
import type { FixSuggestion } from "#/types/conversation";
import { ReviewWorkspace } from "#/components/ui/ReviewWorkspace";
import type { ReviewFile } from "#/types/conversation";
import { AutonomousOrchestrator } from "#/components/ui/AutonomousOrchestrator";
import { MessageBubble } from "#/components/conversation/MessageBubble";
import { InputActionButton } from "#/components/conversation/InputActionButton";
import { useConversationWebSocket } from "#/hooks/use-conversation-websocket";
import type { Message, TimelineEvent, PlanStep, DebugError, TerminalLine } from "#/types/conversation";

/* ── Page Component ── */
export default function ConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  const { isOss, isSaas, isCloud } = useAppMode();
  const isCustomMode = conversationId === "modes";
  const { data: config } = useConfig();
  const artifacts = useArtifacts();
  const { mode: contextMode, setMode: setContextMode } = useMode();

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
  const [autoMode, setAutoMode] = useState(true);
  const [autoModeFlash, setAutoModeFlash] = useState<string | null>(null);

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
  const [reviewOverallStatus, setReviewOverallStatus] = useState<"pending" | "approved" | "changes-requested">("pending");

  /* ── IDE workspace state ── */
  const [workspaceFiles, setWorkspaceFiles] = useState<FileNode[]>([
    { name: "src", path: "src", type: "folder", children: [] },
    { name: "package.json", path: "package.json", type: "file" },
  ]);
  const [terminalLines, setTerminalLines] = useState<TerminalLine[]>([
    { id: "welcome", type: "system", text: "Wren IDE Terminal — connected", timestamp: Date.now() },
  ]);

  /* ── Refs ── */
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /* ── WebSocket hook ── */
  const { connectWebSocket, sendCommand } = useConversationWebSocket({
    state: conversation
      ? { conversationId: conversationId!, ...conversation, sandboxStatus: conversation.sandboxStatus }
      : null,
    handlers: {
      onMessage: (msg) => setMessages((prev) => (prev.some((m) => m.id === msg.id) ? prev : [...prev, msg])),
      onUpdateMessage: (updater) => setMessages(updater),
      onTimelineEvent: (event) =>
        setTimelineEvents((prev) => [
          ...prev,
          { ...event, id: `tl-${timelineEventIdRef.current++}`, timestamp: new Date() },
        ]),
      onError: (err) => setError(err || null),
      onRunningChange: setIsRunning,
      onModeSuggested: (mode) => setSelectedMode(mode),
      onModeFlash: (mode) => {
        setAutoModeFlash(mode);
        setTimeout(() => setAutoModeFlash(null), 2000);
      },
      onPlanSteps: setPlanSteps,
      onDebugError: setDebugError,
      onDebugFixes: setDebugFixes,
      onReviewFile: (file) => setReviewFiles((prev) => (prev.some((f) => f.path === file.path) ? prev : [...prev, file])),
      onWorkspaceFile: (path) =>
        setWorkspaceFiles((prev) => (prev.some((f) => f.path === path) ? prev : [...prev, { name: path.split("/").pop() || path, path, type: "file" as const }])),
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
        const response = await fetch(`/api/v1/app-conversations/${conversationId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
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

      // Reset mode-specific state on new message
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
    if (selectedMode === "autonomous" && planSteps.length > 0 && pendingInput && !isRunning) {
      const input = pendingInput;
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

  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, []);

  /* ── Resume ── */
  const handleResume = useCallback(async () => {
    if (!conversationId || !conversation?.agentServerUrl || !conversation?.sessionApiKey) return;
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

  /* ── Loading ── */
  if (isConnecting && !conversation) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-4 animate-fade-in-up">
          <div
            className="flex h-12 w-12 items-center justify-center rounded-xl animate-pulse-glow"
            style={{
              background: "linear-gradient(135deg, var(--accent), var(--accent-hover))",
              boxShadow: "0 0 24px color-mix(in srgb, var(--accent) 30%, transparent)",
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <p className="text-sm" style={{ color: "var(--text-subtle)" }}>Loading conversation...</p>
        </div>
      </div>
    );
  }

  const isCodeMode = selectedMode === "code";

  const handleTerminalCommand = useCallback(
    (cmd: string) => {
      setTerminalLines((prev) => [
        ...prev,
        { id: `cmd-${Date.now()}`, type: "input", text: `$ ${cmd}`, timestamp: Date.now() },
      ]);
      sendCommand(cmd);
    },
    [sendCommand],
  );

  return (
    <div className="flex h-full flex-col" data-testid="conversation-screen">
      {/* ── Content area ── */}
      {selectedMode === "autonomous" ? (
        <AutonomousOrchestrator
          goal={messages.find((m) => m.role === "user")?.content || "Build the requested feature"}
          files={workspaceFiles}
          timelineEvents={timelineEvents}
          terminalLines={terminalLines}
          diffs={reviewFiles}
        />
      ) : selectedMode === "review" && reviewFiles.length > 0 ? (
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl animate-fade-in-up">
            <ReviewWorkspace
              files={reviewFiles}
              onAcceptFile={(path) => {
                setReviewFiles((prev) => prev.map((f) => (f.path === path ? { ...f, status: "accepted" } : f)));
              }}
              onRejectFile={(path) => {
                setReviewFiles((prev) => prev.map((f) => (f.path === path ? { ...f, status: "rejected" } : f)));
              }}
              onApproveAll={() => {
                setReviewOverallStatus("approved");
                setReviewFiles((prev) => prev.map((f) => ({ ...f, status: "accepted" as const })));
              }}
              onRejectAll={() => {
                setReviewOverallStatus("changes-requested");
                setReviewFiles((prev) => prev.map((f) => ({ ...f, status: "rejected" as const })));
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
      ) : isCodeMode ? (
        <div className="flex-1 min-h-0 overflow-hidden">
          <IDEWorkspace
            files={workspaceFiles}
            timelineEvents={timelineEvents}
            terminalLines={terminalLines}
            onTerminalCommand={handleTerminalCommand}
          />
        </div>
      ) : (
        /* ── Standard chat messages (non-code modes) ── */
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl">
            <div className="flex flex-col gap-4">
              {/* Timeline (collapsible) */}
              {timelineEvents.length > 0 && (
                <div className="mb-2 animate-fade-in-up">
                  <AgentTimeline events={timelineEvents} />
                </div>
              )}

              {/* Plan steps (Plan mode) */}
              {planSteps.length > 0 && (
                <div className="mb-2 animate-fade-in-up">
                  <PlanView steps={planSteps} onApprove={handlePlanApprove} onReject={handlePlanReject} />
                </div>
              )}

              {messages.length === 0 ? (
                <>
                  <div className="glass-bubble animate-fade-in-up max-w-[85%] self-start p-4">
                    <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)", fontWeight: 480 }}>
                      I'm ready to help. What would you like me to work on?
                    </p>
                  </div>
                  <div
                    className="animate-fade-in-up max-w-[85%] self-end rounded-2xl p-4"
                    style={{
                      background: "color-mix(in srgb, var(--accent) 15%, transparent)",
                      border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
                      backdropFilter: "blur(12px)",
                    }}
                  >
                    <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)", fontWeight: 480 }}>
                      Build a React component for a glassmorphism card
                    </p>
                  </div>
                </>
              ) : (
                messages.map((message) => <MessageBubble key={message.id} message={message} />)
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
                          boxShadow: "0 0 12px color-mix(in srgb, var(--accent) 30%, transparent)",
                        }}
                      />
                    ))}
                  </div>
                  <span className="text-xs" style={{ color: "var(--text-subtle)" }}>
                    {selectedMode === "plan" ? "Analyzing..." : "Thinking"}
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
          <div className="card border-error/30 p-4" style={{ borderColor: "var(--error)" }}>
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm" style={{ color: "var(--error)" }}>{error}</span>
              <Button variant="ghost" size="sm" onClick={() => setError(null)}>
                Dismiss
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ── Persistent Mode Chips (Gemini-style) ── */}
      <div className="shrink-0 px-6 pb-2">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            <span
              className="text-[10px] font-medium uppercase tracking-wider flex-shrink-0 mr-1"
              style={{ color: "var(--text-quiet)" }}
            >
              Mode:
            </span>
            {MODES.filter((m) => m.enabledByDefault).map((m) => {
              const isActive = selectedMode === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    setSelectedMode(m.id);
                    setContextMode(m.id);
                    if (m.id === "video") navigate("/video");
                  }}
                  title={m.description}
                  className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-all duration-200 whitespace-nowrap press ${
                    isActive
                      ? "bg-accent/15 text-accent shadow-sm"
                      : "text-text-muted hover:text-text-primary hover:bg-surface-hover"
                  }`}
                  style={{
                    border: isActive
                      ? "1px solid color-mix(in srgb, var(--accent) 25%, transparent)"
                      : "1px solid transparent",
                  }}
                >
                  {/* Mode icons */}
                  {m.id === "plan" && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <path d="M6 1.5v9M1.5 6h9" />
                      <circle cx="6" cy="6" r="4.5" />
                    </svg>
                  )}
                  {m.id === "code" && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <path d="M4.5 3l-3 3 3 3M7.5 3l3 3-3 3" />
                    </svg>
                  )}
                  {m.id === "review" && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <circle cx="6" cy="6" r="4.5" />
                      <path d="M4 6l1.5 1.5L8 4.5" />
                    </svg>
                  )}
                  {m.id === "debug" && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <circle cx="6" cy="6" r="4.5" />
                      <path d="M6 3.5v2.5l1.5 1.5" />
                    </svg>
                  )}
                  {m.id === "ask" && (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                      <circle cx="6" cy="6" r="4.5" />
                      <path d="M6 4.5v.5M6 7v.5" />
                    </svg>
                  )}
                  {m.shortLabel}
                </button>
              );
            })}

            {/* Auto-toggle chip */}
            <div className="flex items-center gap-1.5 ml-auto flex-shrink-0">
              <button
                type="button"
                role="switch"
                aria-checked={autoMode}
                onClick={() => setAutoMode(!autoMode)}
                title="Auto-switch mode based on your input"
                className={`flex items-center gap-1.5 rounded-lg px-2 py-1 text-[10px] font-medium transition-all duration-200 ${
                  autoMode
                    ? "bg-accent/10 text-accent"
                    : "text-text-quiet hover:text-text-muted"
                }`}
              >
                <svg
                  width="10"
                  height="10"
                  viewBox="0 0 10 10"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  aria-hidden="true"
                >
                  <path d="M5 1l1 3h3l-2.5 2 1 3L5 6.5 2.5 9l1-3L1 4h3z" />
                </svg>
                Auto
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Premium Glass Input Card */}
      <div className="shrink-0 px-6 pb-6 pt-1">
        <div
          className="pointer-events-none absolute bottom-8 left-1/2 h-16 w-3/4 -translate-x-1/2"
          style={{
            background: `radial-gradient(ellipse at center, color-mix(in srgb, var(--accent) 6%, transparent) 0%, transparent 70%)`,
          }}
        />

        <div className="mx-auto max-w-3xl">
          <div
            className="glass-input relative overflow-hidden transition-all duration-300"
            style={{
              borderColor: focused ? "color-mix(in srgb, var(--accent) 50%, transparent)" : "var(--border-strong)",
              boxShadow: focused
                ? "0 0 0 1px color-mix(in srgb, var(--accent) 20%, transparent), var(--shadow-md)"
                : "var(--shadow-sm), var(--shadow-inner)",
            }}
          >
            {/* Top accent bar */}
            <div
              className="pointer-events-none absolute left-0 top-0 h-px w-full origin-left transition-all duration-300"
              style={{
                background: "linear-gradient(90deg, transparent, var(--accent), transparent)",
                opacity: focused ? 0.6 : 0,
                transform: focused ? "scaleX(1)" : "scaleX(0)",
              }}
            />

            <div className="flex flex-col">
              {/* Input Area */}
              <textarea
                ref={inputRef}
                value={input}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder={isRunning ? "Agent is working..." : "Type a message..."}
                rows={1}
                disabled={isRunning || planSteps.length > 0}
                className="w-full resize-none border-none bg-transparent px-4 py-3.5 text-sm leading-relaxed outline-none placeholder:select-none"
                style={{ color: "var(--text-primary)", caretColor: "var(--accent)" }}
              />

              {/* Attachment Tray */}
              <div className="flex items-center justify-between px-3 py-2" style={{ borderTop: "1px solid var(--border)" }}>
                <div className="flex items-center gap-1">
                  {/* Auto-mode indicator flash */}
                  {autoModeFlash && (
                    <div
                      className="flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-medium animate-fade-in-up"
                      style={{
                        background: "color-mix(in srgb, var(--accent) 12%, transparent)",
                        color: "var(--accent)",
                        border: "1px solid color-mix(in srgb, var(--accent) 15%, transparent)",
                      }}
                    >
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M5 1l1 3h3l-2.5 2 1 3L5 6.5 2.5 9l1-3L1 4h3z" />
                      </svg>
                      Switched to {getModeDef(autoModeFlash as ModeId).shortLabel}
                    </div>
                  )}

                  <InputActionButton label="Attach file">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M7 4v6M4 7h6" />
                      <path d="M12 7a5 5 0 1 1-10 0 5 5 0 0 1 10 0z" />
                    </svg>
                  </InputActionButton>
                  <InputActionButton label="Open artifacts" onClick={() => artifacts.toggle()}>
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="1.5" y="1.5" width="11" height="11" rx="2" />
                      <circle cx="5" cy="5" r="1.5" />
                      <path d="M1.5 9.5l3-3 3 3 2-2 3 3" />
                    </svg>
                  </InputActionButton>
                </div>

                <div className="flex items-center gap-1">
                  <span className="mr-1 text-[11px]" style={{ color: "var(--text-quiet)" }}>
                    {input.length > 0 ? `${input.length} chars` : ""}
                  </span>
                  <Button
                    type="button"
                    onClick={() => sendMessage(input)}
                    disabled={!input.trim() || isRunning || planSteps.length > 0}
                    className="btn-accent h-8 gap-1.5 px-3 text-xs font-semibold"
                  >
                    {isRunning ? (
                      <>
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        Running
                      </>
                    ) : input.trim() ? (
                      <>
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M11 12l-4-4-4 4M11 6l-4-4-4 4" />
                        </svg>
                        Send
                      </>
                    ) : (
                      <>
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
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
      {(needsResume || (conversation?.sandboxStatus && conversation.sandboxStatus !== "RUNNING")) && (
        <div className="mx-auto max-w-3xl px-6 pt-2">
          <div className="card gradient-accent-border p-4">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                  {conversation?.title || "Conversation"} is not running
                </p>
                <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  {conversation?.sandboxStatus === "MISSING"
                    ? "The sandbox no longer exists. Start a new conversation to continue."
                    : "Click Resume to reconnect and continue where you left off."}
                </p>
              </div>
              <Button onClick={handleResume} disabled={isResuming} className="whitespace-nowrap">
                {isResuming ? "Resuming..." : "Resume"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
