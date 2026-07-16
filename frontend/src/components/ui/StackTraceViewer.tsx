/* Stack trace viewer for debug mode — parses error stacks, shows frames + fix suggestions */
import { useMemo, useState } from "react";

interface StackFrame {
  file: string;
  line: number;
  column: number;
  function: string;
  source?: string;
}

interface FixSuggestion {
  title: string;
  description: string;
  code?: string;
  file?: string;
  line?: number;
}

interface StackTraceViewerProps {
  errorMessage?: string;
  errorType?: string;
  rawStack?: string;
  fixSuggestions?: FixSuggestion[];
  onFileSelect?: (file: string, line: number) => void;
}

function parseStackFrames(raw: string): StackFrame[] {
  const frames: StackFrame[] = [];
  const lines = raw.split("\n");

  for (const line of lines) {
    /* Node stack: at fn (/path/file.js:line:col) */
    const nodeMatch = line.match(/at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)/);
    if (nodeMatch) {
      frames.push({
        function: nodeMatch[1],
        file: nodeMatch[2],
        line: parseInt(nodeMatch[3]),
        column: parseInt(nodeMatch[4]),
      });
      continue;
    }

    /* V8 stack: at /path/file.js:line:col */
    const v8Match = line.match(/at\s+(.+?):(\d+):(\d+)/);
    if (v8Match) {
      frames.push({
        function: "<anonymous>",
        file: v8Match[1],
        line: parseInt(v8Match[2]),
        column: parseInt(v8Match[3]),
      });
      continue;
    }

    /* Python traceback: File "/path/file.py", line N, in fn */
    const pyMatch = line.match(
      /File\s+"(.+?)",\s+line\s+(\d+)(?:,\s+in\s+(.+))?/,
    );
    if (pyMatch) {
      frames.push({
        file: pyMatch[1],
        line: parseInt(pyMatch[2]),
        column: 0,
        function: pyMatch[3] || "<module>",
      });
      continue;
    }
  }

  return frames;
}

function FrameRow({
  frame,
  isLast,
  onFileSelect,
}: {
  frame: StackFrame;
  isLast: boolean;
  onFileSelect?: (file: string, line: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="flex items-start gap-2 py-1.5 px-2 rounded-lg transition-colors hover:opacity-90"
      style={{
        borderLeft: isLast
          ? "2px solid var(--accent)"
          : "2px solid transparent",
        background: isLast
          ? "color-mix(in srgb, var(--accent) 4%, transparent)"
          : "transparent",
      }}
    >
      <svg
        width="10"
        height="10"
        viewBox="0 0 10 10"
        fill="none"
        stroke={isLast ? "var(--accent)" : "var(--text-quiet)"}
        strokeWidth="1.5"
        className="mt-0.5 shrink-0"
      >
        <path d="M3 1l4 4-4 4" />
      </svg>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span
            className="text-[11px] font-mono truncate"
            style={{ color: "var(--text-primary)" }}
          >
            {frame.function}
          </span>
          <span
            className="text-[9px] font-mono shrink-0"
            style={{ color: "var(--text-quiet)" }}
          >
            {frame.file}:{frame.line}:{frame.column}
          </span>
        </div>
        {frame.function !== "<anonymous>" && !isLast && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-[10px] font-mono truncate block max-w-full hover:opacity-80 transition-opacity"
            style={{ color: "var(--text-quiet)" }}
          >
            {expanded ? frame.file : frame.file.split("/").pop()}
          </button>
        )}
        {onFileSelect && (
          <button
            type="button"
            onClick={() => onFileSelect(frame.file, frame.line)}
            className="text-[9px] mt-0.5 press rounded px-1 py-0.5 transition-colors"
            style={{
              color: "var(--accent)",
              background: "color-mix(in srgb, var(--accent) 6%, transparent)",
            }}
          >
            Open in editor
          </button>
        )}
      </div>
    </div>
  );
}

export function StackTraceViewer({
  errorMessage,
  errorType,
  rawStack,
  fixSuggestions = [],
  onFileSelect,
}: StackTraceViewerProps) {
  const frames = useMemo(
    () => (rawStack ? parseStackFrames(rawStack) : []),
    [rawStack],
  );
  const [showAllFrames, setShowAllFrames] = useState(false);
  const visibleFrames = showAllFrames ? frames : frames.slice(0, 5);

  return (
    <div className="flex flex-col gap-4">
      {/* Error header */}
      <div
        className="rounded-xl p-4"
        style={{
          background: "color-mix(in srgb, var(--error) 8%, transparent)",
          border: "1px solid color-mix(in srgb, var(--error) 20%, transparent)",
        }}
      >
        <div className="flex items-start gap-3">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-lg shrink-0"
            style={{
              background: "color-mix(in srgb, var(--error) 15%, transparent)",
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="var(--error)"
              strokeWidth="1.5"
            >
              <circle cx="8" cy="8" r="6" />
              <path d="M8 5v3M8 11h0" />
            </svg>
          </div>
          <div className="min-w-0">
            {errorType && (
              <span
                className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                style={{
                  background:
                    "color-mix(in srgb, var(--error) 10%, transparent)",
                  color: "var(--error)",
                }}
              >
                {errorType}
              </span>
            )}
            <p
              className="text-sm font-medium mt-1"
              style={{ color: "var(--error)" }}
            >
              {errorMessage || "Unknown error"}
            </p>
          </div>
        </div>
      </div>

      {/* Stack frames */}
      {frames.length > 0 && (
        <div
          className="rounded-xl overflow-hidden"
          style={{
            border: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          <div
            className="flex items-center justify-between px-3 py-2 text-[10px] font-semibold uppercase tracking-wider"
            style={{
              color: "var(--text-quiet)",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <span>Stack Trace</span>
            <span
              className="font-mono normal-case"
              style={{ color: "var(--text-quiet)" }}
            >
              {frames.length} frame{frames.length !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="p-2">
            {/* Source frame (first) */}
            {visibleFrames.map((frame, i) => (
              <FrameRow
                key={`${frame.file}:${frame.line}`}
                frame={frame}
                isLast={i === 0}
                onFileSelect={onFileSelect}
              />
            ))}
            {frames.length > 5 && (
              <button
                type="button"
                onClick={() => setShowAllFrames(!showAllFrames)}
                className="w-full text-[10px] py-1.5 press rounded-lg transition-colors"
                style={{ color: "var(--accent)" }}
              >
                {showAllFrames
                  ? "Show less"
                  : `Show ${frames.length - 5} more frames`}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Fix suggestions */}
      {fixSuggestions.length > 0 && (
        <div
          className="rounded-xl overflow-hidden"
          style={{
            border: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          <div
            className="flex items-center gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-wider"
            style={{
              color: "var(--text-quiet)",
              borderBottom: "1px solid var(--border)",
            }}
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M9 2l1 1-6.5 6.5L2 10l.5-1.5L9 2z" />
            </svg>
            Fix Suggestions
          </div>
          <div className="flex flex-col gap-2 p-3">
            {fixSuggestions.map((s, i) => (
              <div
                key={i}
                className="rounded-lg p-3"
                style={{
                  background:
                    "color-mix(in srgb, var(--accent) 4%, transparent)",
                  border:
                    "1px solid color-mix(in srgb, var(--accent) 10%, transparent)",
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="text-xs font-semibold"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {s.title}
                  </span>
                  {s.file && (
                    <span
                      className="text-[9px] font-mono"
                      style={{ color: "var(--text-quiet)" }}
                    >
                      {s.file}
                      {s.line ? `:${s.line}` : ""}
                    </span>
                  )}
                </div>
                <p
                  className="text-[11px]"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {s.description}
                </p>
                {s.code && (
                  <pre
                    className="mt-2 rounded-lg p-2 text-[10px] overflow-x-auto"
                    style={{
                      background: "var(--claude-canvas)",
                      fontFamily: "var(--font-mono)",
                      color: "var(--text-primary)",
                    }}
                  >
                    <code>{s.code}</code>
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!errorMessage && frames.length === 0 && (
        <div className="flex flex-col items-center gap-3 py-8">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ color: "var(--text-quiet)" }}
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h0" />
          </svg>
          <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
            No error data yet. Run your code in debug mode to see stack traces
            here.
          </p>
        </div>
      )}
    </div>
  );
}

export type { StackFrame, FixSuggestion };
