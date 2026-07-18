/* ── FileTree component for Files tab in ConversationPage ──
 *  Displays workspace files with tabs for list/tree views, matching IDE mockup layout
 */
import { useState, useCallback } from "react";
export interface FileNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children?: FileNode[];
  size?: number;
}
import { ChevronDown, ChevronRight, File, Folder } from "lucide-react";

interface FileTreeProps {
  files: FileNode[];
  onOpenFile?: (path: string) => void;
  editable?: boolean;
  viewMode?: "list" | "tree";
}

export function FileTree({ files, onOpenFile, editable = true, viewMode = "tree" }: FileTreeProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [viewModeState, setViewModeState] = useState(viewMode);

  const toggleFolder = useCallback((path: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "--"; 
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const renderFile = (file: FileNode, depth = 0) => {
    const isFolder = file.type === "folder";
    const isExpanded = expandedFolders.has(file.path);
    const indent = depth * 20;

    return (
      <div key={file.path} className="select-none">
        <div
          className="flex items-center py-1.5 px-2 rounded-md transition-colors cursor-pointer group"
          style={{ paddingLeft: `${indent + 8}px` }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--surface-hover)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
          onClick={() => {
            if (isFolder) {
              toggleFolder(file.path);
            } else if (onOpenFile) {
              onOpenFile(file.path);
            }
          }}
        >
          <div className="w-4 flex-shrink-0 flex items-center justify-center mr-2">
            {isFolder ? (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFolder(file.path);
                }}
                className="p-0.5 rounded transition-colors"
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--surface-hover)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                {isExpanded ? (
                  <ChevronDown size={12} className="text-text-muted" />
                ) : (
                  <ChevronRight size={12} className="text-text-muted" />
                )}
              </button>
            ) : (
              <File size={12} className="text-text-muted" />
            )}
          </div>

          <div className="flex items-center gap-2 flex-1 min-w-0">
            {isFolder ? (
              <Folder size={14} className="text-text-muted flex-shrink-0" />
            ) : (
              <div className="w-3.5 h-3.5 flex-shrink-0" />
            )}

            <span className={`text-sm font-medium truncate ${!isFolder ? "text-text-primary" : "text-text-muted"}`}>
              {file.name}
            </span>

            {!isFolder && file.size && (
              <span className="text-xs text-text-quiet ml-auto pr-2">
                {formatFileSize(file.size)}
              </span>
            )}

            {!isFolder && editable && (
              <div className="flex gap-1 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    /* edit file */
                  }}
                  className="p-1 hover:bg-apurple-20 rounded text-text-muted hover:text-purple-600 transition-colors"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M11 4a2 2 0 114.001 3.999A2 2 0 0111.001 6.999A2 2 0 019.001 4l-4 4 4 4 4-4z" />
                  </svg>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    /* delete file */
                  }}
                  className="p-1 hover:bg-error/20 rounded text-text-muted hover:text-error transition-colors"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M8 6l1-2h6l1 2M5 12v6a2 2 0 002 2h6a2 2 0 002-2V12m-3-3v-4m3 4v-4" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>

        {isFolder && isExpanded && file.children && file.children.length > 0 && (
          <div className="mt-1">
            {file.children.map(child => renderFile(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2.5 border-b" style={{ borderColor: "var(--border)" }}>
        <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-quiet)" }}>
          Files
        </h3>
        <div className="text-xs" style={{ color: "var(--text-subtle)" }}>
          {files.filter(f => f.type === "file").length} files
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {viewModeState === "tree" ? (
          files.map(file => renderFile(file))
        ) : (
          <div className="space-y-1">
            {files.filter(f => f.type === "file").map(file => renderFile(file))}
          </div>
        )}
      </div>

      <div className="px-3 py-2 border-t" style={{ borderColor: "var(--border)" }}>
        <div className="flex gap-2">
          <button
            onClick={() => setViewModeState("tree")}
            className={`px-2 py-1 text-xs rounded transition-all ${viewModeState === "tree"
              ? "bg-accent/20 text-accent"
              : "text-text-muted hover:text-text-primary"
            }`}
            onMouseEnter={(e) => {
              if (viewModeState !== 'tree') e.currentTarget.style.background = 'var(--surface-hover)';
            }}
            onMouseLeave={(e) => {
              if (viewModeState !== 'tree') e.currentTarget.style.background = 'transparent';
            }}
          >
            Tree View
          </button>
          <button
            onClick={() => setViewModeState("list")}
            className={`px-2 py-1 text-xs rounded transition-all ${viewModeState === "list"
              ? "bg-accent/20 text-accent"
              : "text-text-muted hover:text-text-primary"}`}
            onMouseEnter={(e) => {
              if (viewModeState !== 'list') e.currentTarget.style.background = 'var(--surface-hover)';
            }}
            onMouseLeave={(e) => {
              if (viewModeState !== 'list') e.currentTarget.style.background = 'transparent';
            }}
          >
            List View
          </button>
        </div>
      </div>
    </div>
  );
}