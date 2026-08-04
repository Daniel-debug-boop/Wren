import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslation } from "react-i18next";
import Editor, { type OnMount, type BeforeMount } from "@monaco-editor/react";
import { TerminalComponent } from "../components/Terminal";
import {
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Send,
  Sparkles,
  Terminal as TerminalIcon,
  MessageSquare,
  GitBranch,
  Settings,
  Play,
  StopCircle,
  Plus,
  Clock,
  ChevronDown,
  ChevronRight,
  File,
  Folder,
  FolderOpen,
  Save,
} from "lucide-react";
import { useWorkspaceStore } from "../store/workspace-store";
import { useWebSocket } from "../hooks/useWebSocket";
import { filesApi } from "../api/client";
import type { AgentState, FileTreeNode } from "../types";

const DEFAULT_CODE = `// Wren Workspace
// Pick a file from the sidebar or type a prompt to start building.
// Ctrl/Cmd + S saves the open file back to your workspace.

function App() {
  return (
    <div>
      <h1>Welcome to Wren</h1>
      <p>Your AI engineering platform is ready.</p>
    </div>
  );
}

export default App;
`;

function languageFromPath(path: string | null): string {
  if (!path) return "typescript";
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    ts: "typescript",
    tsx: "typescript",
    js: "javascript",
    jsx: "javascript",
    py: "python",
    json: "json",
    css: "css",
    html: "html",
    md: "markdown",
    yml: "yaml",
    yaml: "yaml",
    sh: "shell",
    go: "go",
    rs: "rust",
    java: "java",
    kt: "kotlin",
    sql: "sql",
    toml: "ini",
    txt: "plaintext",
  };
  return map[ext] || "plaintext";
}

function getStatusDotClass(agentState: AgentState): string {
  if (
    agentState === "thinking" ||
    agentState === "writing_code" ||
    agentState === "running_command"
  ) {
    return "bg-accent animate-pulse";
  }
  return agentState === "error" ? "bg-status-error" : "bg-status-success";
}

function getStatusLabel(agentState: AgentState): string {
  switch (agentState) {
    case "thinking":
      return "Thinking...";
    case "writing_code":
      return "Writing code...";
    case "running_command":
      return "Running...";
    case "error":
      return "Error";
    default:
      return "Ready";
  }
}

function getMessageBubbleClass(role: string): string {
  if (role === "user") return "bg-accent text-black rounded-tr-sm";
  if (role === "system")
    return "bg-status-error/10 text-status-error border border-status-error/20";
  return "bg-bg-elevated text-text-secondary border border-border-default";
}

function getSaveButtonClass(
  saveState: "idle" | "saving" | "saved",
  hasActiveFile: boolean,
): string {
  if (saveState === "saved") return "bg-status-success/10 text-status-success";
  return hasActiveFile
    ? "text-text-secondary hover:text-accent hover:bg-bg-elevated"
    : "text-text-muted cursor-not-allowed";
}

function renderChevron(isDir: boolean, expanded: boolean) {
  if (!isDir) return <span className="w-3" />;
  return expanded ? (
    <ChevronDown className="w-3 h-3 text-text-muted" />
  ) : (
    <ChevronRight className="w-3 h-3 text-text-muted" />
  );
}

function renderFileIcon(isDir: boolean, expanded: boolean) {
  if (!isDir) return <File className="w-3.5 h-3.5 text-text-muted" />;
  return expanded ? (
    <FolderOpen className="w-3.5 h-3.5 text-accent/70" />
  ) : (
    <Folder className="w-3.5 h-3.5 text-text-muted" />
  );
}

function FileTreeNodeComponent({
  node,
  depth = 0,
  activeFilePath,
  onOpen,
}: {
  node: FileTreeNode;
  depth?: number;
  activeFilePath: string | null;
  onOpen: (node: FileTreeNode) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const isDir = node.type === "directory";

  return (
    <div>
      <div
        className="flex items-center gap-1.5 px-2 py-1 rounded-md cursor-pointer hover:bg-bg-elevated group"
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => (isDir ? setExpanded(!expanded) : onOpen(node))}
      >
        {renderChevron(isDir, expanded)}
        {renderFileIcon(isDir, expanded)}
        <span
          className={`text-xs truncate ${
            node.path === activeFilePath ? "text-accent" : "text-text-secondary"
          }`}
        >
          {node.name}
        </span>
      </div>
      {isDir &&
        expanded &&
        node.children?.map((child, i) => (
          <FileTreeNodeComponent
            key={`${child.path}-${i}`}
            node={child}
            depth={depth + 1}
            activeFilePath={activeFilePath}
            onOpen={onOpen}
          />
        ))}
    </div>
  );
}

export function Workspace() {
  const { t } = useTranslation();
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { sendMessage } = useWebSocket();
  const chatEndRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  const {
    conversations,
    activeConversationId,
    messages,
    agentState,
    agentThought,
    sidebarOpen,
    rightPanelOpen,
    rightPanelTab,
    terminalHistory,
    files,
    activeFilePath,
    activeFileContent,
    settings: appSettings,
    toggleSidebar,
    toggleRightPanel,
    setRightPanelTab,
    setActiveConversation,
    createConversation,
    setFiles,
    setActiveFile,
    addTerminalLine,
  } = useWorkspaceStore();

  const [input, setInput] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">(
    "idle",
  );

  // Initialize conversation
  useEffect(() => {
    if (conversationId) {
      setActiveConversation(conversationId);
    } else if (!activeConversationId && conversations.length === 0) {
      createConversation();
    }
  }, [conversationId]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, agentThought]);

  // Load the real workspace file tree from the backend
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await filesApi.tree();
        if (!cancelled && res.data?.tree?.children) {
          setFiles(res.data.tree.children);
          addTerminalLine(
            `$ [wren] loaded workspace "${res.data.root}" (${res.data.tree.children.length} top-level items)`,
          );
        }
      } catch {
        if (!cancelled) {
          addTerminalLine(
            "$ [wren] backend offline — showing demo file tree (start wren/server.py)",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setFiles, addTerminalLine]);

  const handleSend = () => {
    if (!input.trim() || agentState === "thinking") return;
    const msg = input.trim();
    setInput("");
    sendMessage(msg);
  };

  const isThinking =
    agentState === "thinking" ||
    agentState === "writing_code" ||
    agentState === "running_command";

  const statusDot = getStatusDotClass(agentState);
  const statusLabel = getStatusLabel(agentState);

  // ── File tree interactions ────────────────────────────────────────────

  const openFile = useCallback(
    async (node: FileTreeNode) => {
      setActiveFile(node.path, "// Loading…");
      try {
        const res = await filesApi.read(node.path);
        setActiveFile(node.path, res.data.content);
        addTerminalLine(`$ opened ${node.path}`);
      } catch {
        setActiveFile(
          node.path,
          `// Could not load ${node.path}\n// Is the backend running? (cd wren && python server.py)`,
        );
        addTerminalLine(`$ [wren] failed to open ${node.path}`);
      }
    },
    [setActiveFile, addTerminalLine],
  );

  const handleSave = useCallback(async () => {
    if (!activeFilePath) return;
    setSaveState("saving");
    try {
      const content = editorRef.current?.getValue() ?? activeFileContent ?? "";
      await filesApi.write(activeFilePath, content);
      setSaveState("saved");
      addTerminalLine(`$ saved ${activeFilePath}`);
      setTimeout(() => setSaveState("idle"), 1800);
    } catch {
      setSaveState("idle");
      addTerminalLine(
        `$ [wren] failed to save ${activeFilePath} — backend offline`,
      );
    }
  }, [activeFilePath, activeFileContent, addTerminalLine]);

  const editorBeforeMount: BeforeMount = (monaco) => {
    monaco.editor.defineTheme("wren-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [{ token: "comment", foreground: "71717A" }],
      colors: {
        "editor.background": "#0A0A0C",
        "editor.foreground": "#F4F4F5",
        "editorLineNumber.foreground": "#52525B",
        "editorLineNumber.activeForeground": "#A1A1AA",
        "editorCursor.foreground": "#F59E0B",
        "editor.selectionBackground": "rgba(245,158,11,0.18)",
        "editor.lineHighlightBackground": "rgba(255,255,255,0.03)",
        "editorIndentGuide.background": "#1C1C21",
        "editorIndentGuide.activeBackground": "#3F3F46",
        "editorGutter.background": "#0A0A0C",
        "editorWidget.background": "#111114",
        "editorWidget.border": "#1C1C21",
        "editorSuggestWidget.background": "#111114",
        "editorSuggestWidget.border": "#1C1C21",
        "scrollbarSlider.background": "rgba(255,255,255,0.08)",
        "scrollbarSlider.hoverBackground": "rgba(255,255,255,0.14)",
      },
    });
  };

  const editorOnMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    editor.addCommand(
      // eslint-disable-next-line no-bitwise -- monaco keybinding API
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
      () => {
        handleSave();
      },
    );
    editor.focus();
  };

  return (
    <div className="h-screen flex flex-col bg-bg-deep">
      {/* Top Bar */}
      <header className="h-11 flex items-center justify-between px-4 border-b border-border-default bg-bg-surface shrink-0">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggleSidebar}
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-elevated transition-colors"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="w-4 h-4" />
            ) : (
              <PanelLeftOpen className="w-4 h-4" />
            )}
          </button>

          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-accent" />
            <span className="text-sm font-medium text-text-primary font-heading">
              {t("APP_NAME")}
            </span>
          </div>

          <div className="h-4 w-px bg-border-default" />

          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${statusDot}`} />
            <span className="text-xs text-text-tertiary">{statusLabel}</span>
          </div>

          {agentThought && isThinking && (
            <span className="text-xs text-text-muted italic max-w-[300px] truncate">
              {agentThought}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handleSave}
            disabled={!activeFilePath || saveState === "saving"}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-all ${getSaveButtonClass(
              saveState,
              Boolean(activeFilePath),
            )}`}
            title="Save file (Ctrl+S)"
          >
            <Save className="w-3.5 h-3.5" />
            {saveState === "saved" ? "Saved" : "Save"}
          </button>

          <select className="bg-transparent text-xs text-text-secondary border border-border-default rounded-md px-2 py-1 hover:border-border-strong focus:outline-none cursor-pointer">
            <option>{t("WORKSPACE$MODEL_CLAUDE_SONNET")}</option>
            <option>{t("WORKSPACE$MODEL_GPT4O")}</option>
            <option>{t("WORKSPACE$MODEL_CLAUDE_OPUS")}</option>
            <option>{t("WORKSPACE$MODEL_DEEPSEEK")}</option>
          </select>

          <button
            type="button"
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-elevated transition-colors"
          >
            <Play className="w-4 h-4" />
          </button>

          <button
            type="button"
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-elevated transition-colors"
          >
            <StopCircle className="w-4 h-4" />
          </button>

          <div className="h-4 w-px bg-border-default" />

          <button
            type="button"
            onClick={() => navigate("/settings")}
            className="p-1.5 rounded-md text-text-muted hover:text-text-secondary hover:bg-bg-elevated transition-colors"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.aside
              className="w-52 border-r border-border-default bg-bg-surface shrink-0 flex flex-col"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 208, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              {/* Conversations */}
              <div className="p-3 border-b border-border-default">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    {t("WORKSPACE$CONVERSATIONS")}
                  </span>
                  <button
                    type="button"
                    onClick={() => createConversation()}
                    className="p-1 rounded hover:bg-bg-elevated text-text-muted hover:text-text-secondary transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="space-y-0.5 max-h-[180px] overflow-y-auto">
                  {conversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer text-xs transition-colors ${
                        conv.id === activeConversationId
                          ? "bg-accent/10 text-accent"
                          : "text-text-tertiary hover:text-text-secondary hover:bg-bg-elevated"
                      }`}
                      onClick={() => navigate(`/workspace/${conv.id}`)}
                    >
                      <MessageSquare className="w-3 h-3 shrink-0" />
                      <span className="truncate">{conv.title}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* File Tree */}
              <div className="flex-1 p-3 overflow-y-auto">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    {t("WORKSPACE$FILES")}
                  </span>
                  <GitBranch className="w-3 h-3 text-text-muted" />
                </div>
                {files.length === 0 ? (
                  <p className="text-xs text-text-muted leading-relaxed mt-2">
                    {t("WORKSPACE$NO_FILES")}
                  </p>
                ) : (
                  files.map((node, i) => (
                    <FileTreeNodeComponent
                      key={`${node.path}-${i}`}
                      node={node}
                      activeFilePath={activeFilePath}
                      onOpen={openFile}
                    />
                  ))
                )}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Center: Monaco Editor */}
        <div className="flex-1 flex flex-col min-w-0 bg-bg-deep">
          <div className="flex items-center justify-between px-4 py-1.5 border-b border-border-default bg-bg-surface">
            <span className="text-xs text-text-tertiary font-mono">
              {activeFilePath || "welcome.tsx"}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-text-muted uppercase tracking-wider">
                {languageFromPath(activeFilePath)}
              </span>
              <button
                type="button"
                onClick={toggleRightPanel}
                className="p-1 rounded text-text-muted hover:text-text-secondary hover:bg-bg-elevated transition-colors"
              >
                {rightPanelOpen ? (
                  <PanelRightClose className="w-3.5 h-3.5" />
                ) : (
                  <PanelRightOpen className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>

          {/* Monaco Editor */}
          <div className="flex-1 relative min-h-0">
            <Editor
              path={activeFilePath || "welcome.tsx"}
              language={languageFromPath(activeFilePath)}
              theme="wren-dark"
              beforeMount={editorBeforeMount}
              onMount={editorOnMount}
              value={activeFileContent ?? DEFAULT_CODE}
              onChange={(value) => {
                if (activeFilePath) {
                  setActiveFile(activeFilePath, value ?? "");
                }
              }}
              options={{
                fontSize: appSettings.fontSize || 14,
                tabSize: appSettings.tabSize || 2,
                wordWrap: appSettings.wordWrap ? "on" : "off",
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: { top: 16, bottom: 16 },
                fontFamily: "'Geist Mono', 'JetBrains Mono', monospace",
                smoothScrolling: true,
                cursorBlinking: "smooth",
                renderLineHighlight: "all",
                fontLigatures: true,
              }}
            />
          </div>
        </div>

        {/* Right Panel */}
        <AnimatePresence>
          {rightPanelOpen && (
            <motion.div
              className="w-[380px] border-l border-border-default bg-bg-surface shrink-0 flex flex-col"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 380, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              {/* Panel Tabs */}
              <div className="flex border-b border-border-default">
                {[
                  { id: "chat" as const, icon: MessageSquare, label: "Chat" },
                  {
                    id: "terminal" as const,
                    icon: TerminalIcon,
                    label: "Terminal",
                  },
                  { id: "timeline" as const, icon: Clock, label: "Timeline" },
                ].map((tab) => (
                  <button
                    type="button"
                    key={tab.id}
                    onClick={() => setRightPanelTab(tab.id)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${
                      rightPanelTab === tab.id
                        ? "text-accent border-b-2 border-accent bg-accent/[0.03]"
                        : "text-text-tertiary hover:text-text-secondary hover:bg-bg-elevated"
                    }`}
                  >
                    <tab.icon className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                ))}
              </div>

              {/* Chat Panel */}
              {rightPanelTab === "chat" && (
                <div className="flex-1 flex flex-col min-h-0">
                  <div className="flex-1 overflow-y-auto p-3 space-y-3">
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        {msg.role !== "user" && (
                          <div className="w-6 h-6 rounded-lg bg-accent/10 flex items-center justify-center shrink-0 mt-0.5">
                            <Sparkles className="w-3 h-3 text-accent" />
                          </div>
                        )}
                        <div
                          className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${getMessageBubbleClass(
                            msg.role,
                          )}`}
                        >
                          <div className="whitespace-pre-wrap break-words font-mono text-[13px]">
                            {msg.content}
                          </div>
                          {msg.actions && msg.actions.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-border-default space-y-1">
                              {msg.actions.map((action, i) => (
                                <div
                                  key={i}
                                  className="flex items-start gap-1.5 text-[11px] text-text-tertiary"
                                >
                                  <div className="w-1 h-1 rounded-full bg-accent/60 mt-1.5 shrink-0" />
                                  <span>{action.thought}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        {msg.role === "user" && (
                          <div className="w-6 h-6 rounded-lg bg-accent/20 flex items-center justify-center shrink-0 mt-0.5">
                            <span className="text-[10px] text-accent font-semibold">
                              U
                            </span>
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Agent thinking indicator */}
                    {isThinking && (
                      <div className="flex gap-2">
                        <div className="w-6 h-6 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                          <Sparkles className="w-3 h-3 text-accent" />
                        </div>
                        <div className="bg-bg-elevated border border-border-default rounded-xl px-3 py-2">
                          <div className="flex items-center gap-2">
                            <div className="flex gap-1">
                              <span
                                className="w-1.5 h-1.5 bg-accent/60 rounded-full animate-bounce"
                                style={{ animationDelay: "0ms" }}
                              />
                              <span
                                className="w-1.5 h-1.5 bg-accent/60 rounded-full animate-bounce"
                                style={{ animationDelay: "150ms" }}
                              />
                              <span
                                className="w-1.5 h-1.5 bg-accent/60 rounded-full animate-bounce"
                                style={{ animationDelay: "300ms" }}
                              />
                            </div>
                            <span className="text-xs text-text-tertiary">
                              {agentThought || "Thinking..."}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={chatEndRef} />
                  </div>

                  {/* Chat Input */}
                  <div className="p-3 border-t border-border-default">
                    <div className="relative">
                      <textarea
                        className="w-full bg-bg-elevated border border-border-default rounded-xl px-4 py-3 pr-12 text-sm text-text-primary placeholder-text-muted resize-none focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 transition-all"
                        placeholder="Type your prompt... (e.g., 'Build a React todo app')"
                        rows={2}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSend();
                          }
                        }}
                      />
                      <button
                        type="button"
                        onClick={handleSend}
                        disabled={!input.trim() || isThinking}
                        className={`absolute right-2 bottom-2 p-2 rounded-lg transition-all ${
                          input.trim() && !isThinking
                            ? "bg-accent text-black hover:bg-accent-hover hover:glow-accent-sm"
                            : "bg-bg-card text-text-muted cursor-not-allowed"
                        }`}
                      >
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Terminal Panel */}
              {rightPanelTab === "terminal" && (
                <div className="flex-1 overflow-hidden">
                  <TerminalComponent
                    wsUrl={`${window.location.protocol === "https:" ? "wss:" : "ws:"}//${import.meta.env.VITE_BACKEND_HOST || "127.0.0.1:3000"}/ws/terminal`}
                    onExit={(code) => {
                      addTerminalLine(`$ [process exited with code ${code}]`);
                    }}
                    onError={(msg) => {
                      addTerminalLine(`$ [terminal error: ${msg}]`);
                    }}
                  />
                </div>
              )}

              {/* Timeline Panel */}
              {rightPanelTab === "timeline" && (
                <div className="flex-1 overflow-y-auto p-3">
                  <div className="space-y-3">
                    {messages.map((msg, i) => (
                      <div key={msg.id} className="flex items-start gap-2">
                        <div className="flex flex-col items-center">
                          <div
                            className={`w-2 h-2 rounded-full ${msg.role === "user" ? "bg-accent" : "bg-status-success"}`}
                          />
                          {i < messages.length - 1 && (
                            <div className="w-px flex-1 bg-border-default" />
                          )}
                        </div>
                        <div className="pb-4">
                          <span className="text-xs text-text-tertiary">
                            {msg.role === "user"
                              ? "You said:"
                              : "Agent responded:"}
                          </span>
                          <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
                            {msg.content.substring(0, 100)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
