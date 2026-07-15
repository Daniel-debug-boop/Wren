/* 3-pane IDE workspace: FileTree | Editor+Terminal | AgentTimeline */
import { useState, useRef, useCallback } from "react";
import { FileTree, type FileNode } from "./FileTree";
import { EditorPanel } from "./EditorPanel";
import { Terminal } from "#/components/Terminal";
import { AgentTimeline } from "#/components/ui/AgentTimeline";

interface TimelineEvent {
  id: string;
  type: "action" | "observation" | "message" | "error" | "status";
  actionType?: string;
  title: string;
  detail?: string;
  timestamp: Date;
  duration?: number;
  status?: "running" | "done" | "error" | "skipped";
}

interface IDEWorkspaceProps {
  files: FileNode[];
  timelineEvents: TimelineEvent[];
  terminalLines: Array<{ id: string; type: "input" | "output" | "system"; text: string; timestamp: number }>;
  onTerminalCommand?: (cmd: string) => void;
}

export function IDEWorkspace({ files, timelineEvents, terminalLines, onTerminalCommand }: IDEWorkspaceProps) {
  const [activeFile, setActiveFile] = useState<string>("");
  const [activeCode, setActiveCode] = useState<string>("");
  const [showTimeline, setShowTimeline] = useState(true);
  const [showFileTree, setShowFileTree] = useState(true);
  const [showTerminal, setShowTerminal] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  /* drag-resize state */
  const [leftWidth, setLeftWidth] = useState(240);
  const [rightWidth, setRightWidth] = useState(280);
  const [terminalHeight, setTerminalHeight] = useState(200);
  const isDraggingLeft = useRef(false);
  const isDraggingRight = useRef(false);
  const isDraggingTerminal = useRef(false);

  const handleFileSelect = useCallback((path: string) => {
    setActiveFile(path);
    /* find code content from observations - for now, pick the file name */
    setActiveCode(`// ${path}\n// Select a file to view its contents`);
  }, []);

  const handleDragStart = useCallback((ref: React.MutableRefObject<boolean>) => (e: React.MouseEvent) => {
    e.preventDefault();
    ref.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    if (isDraggingLeft.current) {
      setLeftWidth(Math.max(180, Math.min(480, e.clientX - rect.left)));
    }
    if (isDraggingRight.current) {
      setRightWidth(Math.max(200, Math.min(500, rect.right - e.clientX)));
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingLeft.current = false;
    isDraggingRight.current = false;
    isDraggingTerminal.current = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  return (
    <div
      ref={containerRef}
      className="flex h-full overflow-hidden"
      style={{ background: "var(--claude-canvas)" }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* ── Left: File Tree ── */}
      {showFileTree && (
        <>
          <div
            className="flex flex-col shrink-0 overflow-hidden"
            style={{
              width: leftWidth,
              borderRight: "1px solid var(--border)",
              background: "var(--surface)",
            }}
          >
            <FileTree
              files={files}
              activeFile={activeFile}
              onFileSelect={handleFileSelect}
            />
          </div>
          {/* Resize handle */}
          <div
            className="shrink-0 cursor-col-resize hover:bg-accent/20 transition-colors"
            style={{ width: "4px" }}
            onMouseDown={handleDragStart(isDraggingLeft)}
          />
        </>
      )}

      {/* ── Center: Editor + Terminal ── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Editor */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {activeFile ? (
            <EditorPanel filename={activeFile} content={activeCode} />
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="flex flex-col items-center gap-2">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: "var(--text-quiet)" }}>
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <path d="M14 2v6h6" />
                  <path d="M12 18v-6M9 15h6" />
                </svg>
                <p className="text-xs" style={{ color: "var(--text-quiet)" }}>
                  Select a file from the workspace to view
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Terminal resize handle */}
        {showTerminal && (
          <div
            className="shrink-0 cursor-row-resize hover:bg-accent/20 transition-colors"
            style={{ height: "4px" }}
            onMouseDown={(e) => {
              e.preventDefault();
              isDraggingTerminal.current = true;
              document.body.style.cursor = "row-resize";
            }}
          />
        )}

        {/* Terminal */}
        {showTerminal && (
          <div
            className="shrink-0 overflow-hidden"
            style={{ height: terminalHeight }}
          >
            <Terminal
              lines={terminalLines}
              onCommand={onTerminalCommand}
              height={terminalHeight}
              readOnly={!onTerminalCommand}
            />
          </div>
        )}

        {/* IDE bottom bar */}
        <div
          className="flex items-center justify-between px-3 py-1 shrink-0 text-[10px]"
          style={{
            borderTop: "1px solid var(--border)",
            background: "var(--surface)",
            color: "var(--text-quiet)",
          }}
        >
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowFileTree(!showFileTree)}
              className="flex items-center gap-1 hover:opacity-80 transition-opacity"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M1.5 2h2.5l1 1h3.5v5a.5.5 0 01-.5.5h-7a.5.5 0 01-.5-.5V2.5a.5.5 0 01.5-.5z" />
              </svg>
              {showFileTree ? "Hide" : "Files"}
            </button>
            <button
              type="button"
              onClick={() => setShowTerminal(!showTerminal)}
              className="flex items-center gap-1 hover:opacity-80 transition-opacity"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M1.5 2l3 3-3 3M5 7.5h3.5" />
              </svg>
              {showTerminal ? "Hide" : "Terminal"}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowTimeline(!showTimeline)}
              className="flex items-center gap-1 hover:opacity-80 transition-opacity"
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="2.5" cy="2.5" r="1" />
                <circle cx="2.5" cy="7.5" r="1" />
                <path d="M5 2.5h3.5M5 7.5h3.5" />
              </svg>
              Timeline
            </button>
            <span className="flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: "var(--color-success)" }} />
              Sandbox Ready
            </span>
          </div>
        </div>
      </div>

      {/* ── Right: Timeline ── */}
      {showTimeline && (
        <>
          {/* Resize handle */}
          <div
            className="shrink-0 cursor-col-resize hover:bg-accent/20 transition-colors"
            style={{ width: "4px" }}
            onMouseDown={handleDragStart(isDraggingRight)}
          />
          <div
            className="flex flex-col shrink-0 overflow-hidden"
            style={{
              width: rightWidth,
              borderLeft: "1px solid var(--border)",
              background: "var(--surface)",
            }}
          >
            <div
              className="flex items-center gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: "var(--text-quiet)", borderBottom: "1px solid var(--border)" }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="3" cy="3" r="1.5" />
                <circle cx="9" cy="6" r="1.5" />
                <circle cx="3" cy="9" r="1.5" />
                <path d="M4.5 3h3" />
                <path d="M7.5 6H9" />
                <path d="M4.5 9h3" />
              </svg>
              Agent Timeline
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              <AgentTimeline events={timelineEvents} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
