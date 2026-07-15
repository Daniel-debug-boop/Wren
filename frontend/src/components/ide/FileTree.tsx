/* File tree for IDE workspace — shows workspace files from observations */
import { useState } from "react";

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children?: FileNode[];
  active?: boolean;
}

interface FileTreeProps {
  files: FileNode[];
  activeFile?: string;
  onFileSelect: (path: string) => void;
}

function FileTreeItem({
  node,
  depth,
  activeFile,
  onFileSelect,
}: {
  node: FileNode;
  depth: number;
  activeFile?: string;
  onFileSelect: (path: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isActive = activeFile === node.path;

  if (node.type === "folder") {
    return (
      <div>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center gap-1.5 px-2 py-1 text-xs transition-colors hover:opacity-80"
          style={{ color: "var(--text-secondary)", paddingLeft: `${8 + depth * 16}px` }}
        >
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 0.15s" }}
          >
            <path d="M3 2l3 3-3 3" />
          </svg>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            {expanded ? (
              <path d="M1.5 3.5h4l1.5 1.5h5.5v6.5a1 1 0 01-1 1h-10a1 1 0 01-1-1v-7a1 1 0 011-1z" />
            ) : (
              <path d="M1.5 3.5h4l1.5 1.5h5.5v6.5a1 1 0 01-1 1h-10a1 1 0 01-1-1v-7a1 1 0 011-1z" />
            )}
          </svg>
          <span>{node.name}</span>
        </button>
        {expanded && node.children?.map((child) => (
          <FileTreeItem
            key={child.path}
            node={child}
            depth={depth + 1}
            activeFile={activeFile}
            onFileSelect={onFileSelect}
          />
        ))}
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onFileSelect(node.path)}
      className="flex w-full items-center gap-1.5 px-2 py-1 text-xs transition-colors"
      style={{
        paddingLeft: `${8 + depth * 16}px`,
        background: isActive ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
        color: isActive ? "var(--accent)" : "var(--text-secondary)",
        borderRight: isActive ? "2px solid var(--accent)" : "2px solid transparent",
      }}
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M3.5 2.5h7a1 1 0 011 1v7a1 1 0 01-1 1h-7a1 1 0 01-1-1v-7a1 1 0 011-1z" />
      </svg>
      <span>{node.name}</span>
    </button>
  );
}

export function FileTree({ files, activeFile, onFileSelect }: FileTreeProps) {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-wider"
        style={{ color: "var(--text-quiet)", borderBottom: "1px solid var(--border)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M1.5 3h3l1.5 1.5H10a1 1 0 011 1v4a1 1 0 01-1 1H2a1 1 0 01-1-1V4a1 1 0 011-1z" />
        </svg>
        Workspace
      </div>
      {/* File list */}
      <div className="flex-1 overflow-y-auto py-1">
        {files.length === 0 ? (
          <p className="px-3 py-4 text-xs text-center" style={{ color: "var(--text-quiet)" }}>
            No files yet
          </p>
        ) : (
          files.map((node) => (
            <FileTreeItem
              key={node.path}
              node={node}
              depth={0}
              activeFile={activeFile}
              onFileSelect={onFileSelect}
            />
          ))
        )}
      </div>
    </div>
  );
}
