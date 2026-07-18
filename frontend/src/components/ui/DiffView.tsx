import { useMemo, useState } from "react";

interface DiffHunk {
  oldStart: number;
  newStart: number;
  lines: DiffLine[];
}

interface DiffLine {
  type: "add" | "del" | "ctx";
  content: string;
  oldLine?: number;
  newLine?: number;
}

interface DiffFile {
  path: string;
  hunks: DiffHunk[];
}

interface DiffViewProps {
  files: DiffFile[];
}

function parseUnifiedDiff(diff: string): DiffFile[] {
  const files: DiffFile[] = [];
  let currentFile: DiffFile | null = null;
  let currentHunk: DiffHunk | null = null;

  for (const line of diff.split("\n")) {
    if (line.startsWith("--- ") || line.startsWith("+++ ")) continue;
    if (line.startsWith("diff --git ")) {
      if (currentFile && currentFile.hunks.length > 0) files.push(currentFile);
      const match = line.match(/diff --git a\/(.+) b\/(.+)/);
      currentFile = {
        path: match?.[2] ?? match?.[1] ?? "unknown",
        hunks: [],
      };
      currentHunk = null;
      continue;
    }
    if (line.startsWith("@@ ")) {
      const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (currentFile) {
        currentHunk = {
          oldStart: match ? parseInt(match[1]) : 0,
          newStart: match ? parseInt(match[2]) : 0,
          lines: [],
        };
        currentFile.hunks.push(currentHunk);
      }
      continue;
    }
    if (!currentHunk) continue;
    if (line.startsWith("+")) {
      currentHunk.lines.push({
        type: "add",
        content: line.slice(1),
        newLine:
          currentHunk.newStart +
          currentHunk.lines.filter((l) => l.type !== "del").length,
      });
    } else if (line.startsWith("-")) {
      currentHunk.lines.push({
        type: "del",
        content: line.slice(1),
        oldLine:
          currentHunk.oldStart +
          currentHunk.lines.filter((l) => l.type !== "add").length,
      });
    } else {
      const ctxLine = line.startsWith(" ") ? line.slice(1) : line;
      currentHunk.lines.push({ type: "ctx", content: ctxLine });
    }
  }

  if (currentFile && currentFile.hunks.length > 0) files.push(currentFile);
  return files;
}

export function DiffView({ files: rawFiles }: DiffViewProps) {
  return (
    <div className="flex flex-col gap-3">
      {rawFiles.map((file) => (
        <DiffFileBlock key={file.path} file={file} />
      ))}
    </div>
  );
}

export function DiffViewRaw({ diff }: { diff: string }) {
  const files = useMemo(() => parseUnifiedDiff(diff), [diff]);
  if (files.length === 0) {
    return (
      <div
        className="flex items-center justify-center py-12 text-sm"
        style={{ color: "var(--text-quiet)" }}
      >
        No changes to display
      </div>
    );
  }
  return <DiffView files={files} />;
}

function DiffFileBlock({ file }: { file: DiffFile }) {
  const [collapsed, setCollapsed] = useState(false);
  const addCount = file.hunks.reduce(
    (s, h) => s + h.lines.filter((l) => l.type === "add").length,
    0,
  );
  const delCount = file.hunks.reduce(
    (s, h) => s + h.lines.filter((l) => l.type === "del").length,
    0,
  );

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{ border: "1px solid var(--border)" }}
    >
      {/* File header */}
      <button
        type="button"
        onClick={() => setCollapsed((c) => !c)}
        className="flex w-full items-center justify-between gap-2 px-4 py-2 text-left press transition-colors"
        style={{
          background: "color-mix(in srgb, var(--accent) 4%, var(--surface))",
          borderBottom: collapsed ? "none" : "1px solid var(--border)",
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ color: "var(--text-subtle)", flexShrink: 0 }}
          >
            <path d="M3 1h8l2 2v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z" />
            <path d="M5 1v4h4V1" />
          </svg>
          <span
            className="text-sm font-mono truncate"
            style={{ color: "var(--text-primary)" }}
          >
            {file.path}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {addCount > 0 && (
            <span
              className="text-xs font-medium"
              style={{ color: "var(--diff-add)" }}
            >
              +{addCount}
            </span>
          )}
          {delCount > 0 && (
            <span
              className="text-xs font-medium"
              style={{ color: "var(--diff-del)" }}
            >
              -{delCount}
            </span>
          )}
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{
              color: "var(--text-quiet)",
              transform: collapsed ? "rotate(-90deg)" : "rotate(0deg)",
              transition: "transform 0.2s",
            }}
          >
            <path d="M3 4.5l3 3 3-3" />
          </svg>
        </div>
      </button>

      {/* Hunk lines */}
      {!collapsed && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[12.5px] leading-relaxed font-mono">
            <tbody>
              {file.hunks.map((hunk, hi) =>
                hunk.lines.map((line, li) => (
                  <tr
                    key={`${hi}-${li}`}
                    className="transition-colors duration-100"
                    style={{
                      background:
                        line.type === "add"
                          ? "color-mix(in srgb, var(--diff-add) 10%, transparent)"
                          : line.type === "del"
                            ? "color-mix(in srgb, var(--diff-del) 10%, transparent)"
                            : "transparent",
                    }}
                  >
                    <td
                      className="w-12 min-w-[3rem] select-none px-2 text-right"
                      style={{ color: "var(--text-quiet)" }}
                    >
                      {line.type === "del" ? (line.oldLine ?? "") : ""}
                    </td>
                    <td
                      className="w-12 min-w-[3rem] select-none px-2 text-right"
                      style={{ color: "var(--text-quiet)" }}
                    >
                      {line.type === "add"
                        ? (line.newLine ?? "")
                        : line.type === "ctx"
                          ? (line.oldLine ?? "")
                          : ""}
                    </td>
                    <td
                      className="w-4 min-w-[1rem] select-none text-center"
                      style={{ color: "var(--text-quiet)" }}
                    >
                      {line.type === "add"
                        ? "+"
                        : line.type === "del"
                          ? "-"
                          : " "}
                    </td>
                    <td
                      className="px-2 py-0 whitespace-pre"
                      style={{
                        color:
                          line.type === "add"
                            ? "var(--diff-add-text)"
                            : line.type === "del"
                              ? "var(--diff-del-text)"
                              : "var(--text-primary)",
                      }}
                    >
                      {line.content}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
