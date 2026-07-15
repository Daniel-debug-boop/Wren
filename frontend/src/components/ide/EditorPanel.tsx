/* Simple code editor display with line numbers and basic syntax coloring */
import { useMemo } from "react";

interface EditorPanelProps {
  filename: string;
  content: string;
  language?: string;
}

/* Simple syntax highlighting for common languages */
function highlightLine(line: string): React.ReactNode {
  const tokens: React.ReactNode[] = [];
  let remaining = line;

  const patterns: Array<[RegExp, string]> = [
    [/(\/\/.*$)/gm, "comment"],
    [/(\/\*[\s\S]*?\*\/)/g, "comment"],
    [/(['"`])(?:(?!\1|\\).|\\.)*?\1/g, "string"],
    [/\b(import|export|from|const|let|var|function|return|if|else|for|while|class|interface|type|extends|implements|new|this|async|await|try|catch|throw|import|export|default|as)\b/g, "keyword"],
    [/\b(true|false|null|undefined|void|number|string|boolean|any|never|unknown)\b/g, "type"],
    [/\b(\d+\.?\d*)\b/g, "number"],
    [/([{}()\[\];:,.<>+*/=-])/g, "punctuation"],
  ];

  const allMatches: Array<{ index: number; length: number; className: string }> = [];
  for (const [regex, className] of patterns) {
    let match;
    while ((match = regex.exec(line)) !== null) {
      allMatches.push({ index: match.index, length: match[0].length, className });
    }
  }

  allMatches.sort((a, b) => a.index - b.index);

  let pos = 0;
  let key = 0;
  for (const m of allMatches) {
    if (m.index < pos) continue;
    if (m.index > pos) {
      tokens.push(<span key={key++}>{line.slice(pos, m.index)}</span>);
    }
    tokens.push(
      <span key={key++} className={`hl-${m.className}`}>
        {line.slice(m.index, m.index + m.length)}
      </span>
    );
    pos = m.index + m.length;
  }
  if (pos < line.length) {
    tokens.push(<span key={key++}>{line.slice(pos)}</span>);
  }

  return <>{tokens}</>;
}

export function EditorPanel({ filename, content, language }: EditorPanelProps) {
  const lines = useMemo(() => content.split("\n"), [content]);
  const lang = language || (filename ? filename.split(".").pop() || "txt" : "txt");

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Editor tab bar */}
      <div
        className="flex items-center gap-1 px-2 py-1 text-[11px]"
        style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}
      >
        <div
          className="flex items-center gap-1.5 rounded-t px-2.5 py-1"
          style={{
            background: "var(--surface-elevated)",
            color: "var(--text-primary)",
            border: "1px solid var(--border)",
            borderBottom: "none",
          }}
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M3 1.5h6a1.5 1.5 0 011.5 1.5v6A1.5 1.5 0 019 10.5H3A1.5 1.5 0 011.5 9V3A1.5 1.5 0 013 1.5z" />
          </svg>
          <span>{filename || "untitled"}</span>
          <span className="text-[9px] px-1 rounded" style={{ background: "color-mix(in srgb, var(--accent) 10%, transparent)", color: "var(--accent)" }}>
            {lang}
          </span>
        </div>
      </div>

      {/* Code area with line numbers */}
      <div
        className="flex-1 overflow-auto text-xs leading-relaxed"
        style={{ fontFamily: "var(--font-mono)", background: "var(--surface)" }}
      >
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, i) => (
              <tr
                key={i}
                className="hover:opacity-90"
                style={{
                  background: i % 2 === 0 ? "transparent" : "color-mix(in srgb, var(--border) 20%, transparent)",
                }}
              >
                <td
                  className="select-none text-right px-3 py-0 align-top"
                  style={{
                    color: "var(--text-quiet)",
                    minWidth: "48px",
                    borderRight: "1px solid var(--border)",
                    userSelect: "none",
                  }}
                >
                  {i + 1}
                </td>
                <td className="px-3 py-0 whitespace-pre" style={{ color: "var(--text-primary)" }}>
                  {line ? highlightLine(line) : <br />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Status bar */}
      <div
        className="flex items-center justify-between px-3 py-1 text-[10px]"
        style={{ borderTop: "1px solid var(--border)", color: "var(--text-quiet)", background: "var(--surface)" }}
      >
        <span>{lines.length} lines</span>
        <span>{lang.toUpperCase()}</span>
      </div>

      <style>{`
        .hl-comment { color: var(--text-quiet); font-style: italic; }
        .hl-string { color: #86EFAC; }
        .hl-keyword { color: #C084FC; }
        .hl-type { color: #67E8F9; }
        .hl-number { color: #FDE68A; }
        .hl-punctuation { color: var(--text-secondary); }
      `}</style>
    </div>
  );
}
