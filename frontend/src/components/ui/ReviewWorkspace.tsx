/* Review workspace — split diff view with accept/reject per file and comments */
import { useMemo, useState, useCallback } from "react";
import { DiffViewRaw } from "./DiffView";

export type ReviewStatus = "pending" | "accepted" | "rejected";

interface ReviewFile {
  path: string;
  diff: string;
  status: ReviewStatus;
  comments: ReviewComment[];
}

interface ReviewComment {
  id: string;
  line: number;
  text: string;
  author: string;
  timestamp: Date;
}

interface ReviewWorkspaceProps {
  files: ReviewFile[];
  onAcceptFile?: (path: string) => void;
  onRejectFile?: (path: string) => void;
  onComment?: (path: string, line: number, text: string) => void;
  onApproveAll?: () => void;
  onRejectAll?: () => void;
  overallStatus?: "pending" | "approved" | "changes-requested";
}

function FileReviewCard({
  file,
  onAccept,
  onReject,
  onComment,
}: {
  file: ReviewFile;
  onAccept?: () => void;
  onReject?: () => void;
  onComment?: (line: number, text: string) => void;
}) {
  const [commentText, setCommentText] = useState("");
  const [showCommentInput, setShowCommentInput] = useState(false);

  const statusColors: Record<ReviewStatus, string> = {
    pending: "var(--text-quiet)",
    accepted: "var(--color-success)",
    rejected: "var(--error)",
  };

  const statusLabels: Record<ReviewStatus, string> = {
    pending: "Pending Review",
    accepted: "Accepted",
    rejected: "Rejected",
  };

  return (
    <div
      className="rounded-xl overflow-hidden transition-all"
      style={{
        border: `1px solid ${
          file.status === "accepted"
            ? "color-mix(in srgb, var(--color-success) 30%, transparent)"
            : file.status === "rejected"
              ? "color-mix(in srgb, var(--error) 30%, transparent)"
              : "var(--border)"
        }`,
        background: "var(--surface)",
        opacity: file.status === "accepted" ? 0.85 : 1,
      }}
    >
      {/* File header with actions */}
      <div
        className="flex items-center justify-between gap-2 px-4 py-2.5"
        style={{
          borderBottom: "1px solid var(--border)",
          background:
            file.status === "accepted"
              ? "color-mix(in srgb, var(--color-success) 4%, transparent)"
              : file.status === "rejected"
                ? "color-mix(in srgb, var(--error) 4%, transparent)"
                : "transparent",
        }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: "var(--text-subtle)", flexShrink: 0 }}>
            <path d="M3 1h8l2 2v9a1 1 0 01-1 1H3a1 1 0 01-1-1V2a1 1 0 011-1z" />
            <path d="M5 1v4h4V1" />
          </svg>
          <span className="text-sm font-mono truncate" style={{ color: "var(--text-primary)" }}>
            {file.path}
          </span>
          <span
            className="text-[9px] px-1.5 py-0.5 rounded-full font-medium"
            style={{
              background: `color-mix(in srgb, ${statusColors[file.status]} 10%, transparent)`,
              color: statusColors[file.status],
            }}
          >
            {statusLabels[file.status]}
          </span>
        </div>

        {file.status === "pending" && (
          <div className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              onClick={onAccept}
              className="press flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-all"
              style={{
                background: "color-mix(in srgb, var(--color-success) 10%, transparent)",
                color: "var(--color-success)",
                border: "1px solid color-mix(in srgb, var(--color-success) 20%, transparent)",
              }}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 5l2 2 4-4" />
              </svg>
              Accept
            </button>
            <button
              type="button"
              onClick={onReject}
              className="press flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition-all"
              style={{
                background: "color-mix(in srgb, var(--error) 8%, transparent)",
                color: "var(--error)",
                border: "1px solid color-mix(in srgb, var(--error) 15%, transparent)",
              }}
            >
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 2l6 6M8 2l-6 6" />
              </svg>
              Reject
            </button>
          </div>
        )}
      </div>

      {/* Diff content */}
      <div className="max-h-96 overflow-y-auto">
        <DiffViewRaw diff={file.diff} />
      </div>

      {/* Comments */}
      {file.comments.length > 0 && (
        <div className="px-4 py-2 border-t" style={{ borderColor: "var(--border)" }}>
          <p className="text-[10px] font-semibold uppercase mb-1" style={{ color: "var(--text-quiet)" }}>
            Comments ({file.comments.length})
          </p>
          {file.comments.map((c) => (
            <div key={c.id} className="flex items-start gap-2 py-1">
              <span className="text-[10px] font-mono shrink-0 mt-0.5" style={{ color: "var(--text-quiet)" }}>
                L{c.line}
              </span>
              <div>
                <p className="text-xs" style={{ color: "var(--text-primary)" }}>{c.text}</p>
                <span className="text-[9px]" style={{ color: "var(--text-quiet)" }}>
                  {c.author} · {c.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Comment input */}
      {file.status === "pending" && (
        <div className="border-t px-4 py-2" style={{ borderColor: "var(--border)" }}>
          {showCommentInput ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Add a comment..."
                className="flex-1 rounded-lg px-2.5 py-1.5 text-[11px] outline-none"
                style={{
                  background: "var(--claude-canvas)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--text-primary)",
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && commentText.trim()) {
                    onComment?.(1, commentText.trim());
                    setCommentText("");
                    setShowCommentInput(false);
                  }
                  if (e.key === "Escape") {
                    setCommentText("");
                    setShowCommentInput(false);
                  }
                }}
              />
              <button
                type="button"
                onClick={() => { setShowCommentInput(false); setCommentText(""); }}
                className="text-[10px] press px-2"
                style={{ color: "var(--text-quiet)" }}
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowCommentInput(true)}
              className="flex items-center gap-1 text-[11px] press transition-colors"
              style={{ color: "var(--text-subtle)" }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M1.5 6a4.5 4.5 0 118.6 2.1l-.7 1.8-1.8.8A4.5 4.5 0 011.5 6z" />
              </svg>
              Add comment
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export function ReviewWorkspace({
  files: initialFiles,
  onAcceptFile,
  onRejectFile,
  onApproveAll,
  onRejectAll,
  overallStatus = "pending",
}: ReviewWorkspaceProps) {
  const [files, setFiles] = useState(initialFiles);
  const [view, setView] = useState<"list" | "unified">("list");

  // Sync with external files prop
  useMemo(() => {
    setFiles(initialFiles);
  }, [initialFiles]);

  const handleAccept = useCallback(
    (path: string) => {
      setFiles((prev) =>
        prev.map((f) => (f.path === path ? { ...f, status: "accepted" as const } : f)),
      );
      onAcceptFile?.(path);
    },
    [onAcceptFile],
  );

  const handleReject = useCallback(
    (path: string) => {
      setFiles((prev) =>
        prev.map((f) => (f.path === path ? { ...f, status: "rejected" as const } : f)),
      );
      onRejectFile?.(path);
    },
    [onRejectFile],
  );

  const acceptedCount = files.filter((f) => f.status === "accepted").length;
  const rejectedCount = files.filter((f) => f.status === "rejected").length;
  const pendingCount = files.filter((f) => f.status === "pending").length;

  return (
    <div className="flex flex-col gap-4">
      {/* Review summary header */}
      <div
        className="rounded-xl p-4"
        style={{
          background: "var(--surface)",
          border: `1px solid ${
            overallStatus === "approved"
              ? "color-mix(in srgb, var(--color-success) 30%, transparent)"
              : overallStatus === "changes-requested"
                ? "color-mix(in srgb, var(--error) 30%, transparent)"
                : "var(--border)"
          }`,
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
              Code Review
            </h3>
            <div className="flex items-center gap-3 text-xs">
              <span style={{ color: "var(--text-subtle)" }}>
                {files.length} file{files.length !== 1 ? "s" : ""} changed
              </span>
              <span style={{ color: "var(--diff-add)" }}>
                {acceptedCount} accepted
              </span>
              <span style={{ color: "var(--diff-del)" }}>
                {rejectedCount} rejected
              </span>
              {pendingCount > 0 && (
                <span style={{ color: "var(--text-quiet)" }}>
                  {pendingCount} pending
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {pendingCount > 0 && onApproveAll && (
              <button
                type="button"
                onClick={onApproveAll}
                className="press flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
                style={{
                  background: "color-mix(in srgb, var(--color-success) 10%, transparent)",
                  color: "var(--color-success)",
                  border: "1px solid color-mix(in srgb, var(--color-success) 20%, transparent)",
                }}
              >
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M2 5l2 2 4-4" />
                </svg>
                Approve All
              </button>
            )}
            {pendingCount > 0 && onRejectAll && (
              <button
                type="button"
                onClick={onRejectAll}
                className="press flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
                style={{
                  background: "color-mix(in srgb, var(--error) 8%, transparent)",
                  color: "var(--error)",
                  border: "1px solid color-mix(in srgb, var(--error) 15%, transparent)",
                }}
              >
                Reject All
              </button>
            )}
          </div>
        </div>
      </div>

      {/* View toggle */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setView("list")}
          className="press rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all"
          style={{
            background: view === "list" ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
            color: view === "list" ? "var(--accent)" : "var(--text-subtle)",
          }}
        >
          Per File
        </button>
        <button
          type="button"
          onClick={() => setView("unified")}
          className="press rounded-lg px-2.5 py-1 text-[11px] font-medium transition-all"
          style={{
            background: view === "unified" ? "color-mix(in srgb, var(--accent) 10%, transparent)" : "transparent",
            color: view === "unified" ? "var(--accent)" : "var(--text-subtle)",
          }}
        >
          Unified
        </button>
      </div>

      {/* File review cards */}
      {files.length === 0 ? (
        <div
          className="flex flex-col items-center gap-3 py-12 rounded-xl"
          style={{ border: "1px dashed var(--border-strong)" }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: "var(--text-quiet)" }}>
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
            <path d="M14 2v6h6" />
          </svg>
          <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
            No files to review. Changes will appear here.
          </p>
        </div>
      ) : view === "list" ? (
        <div className="flex flex-col gap-3">
          {files.map((file) => (
            <FileReviewCard
              key={file.path}
              file={file}
              onAccept={() => handleAccept(file.path)}
              onReject={() => handleReject(file.path)}
            />
          ))}
        </div>
      ) : (
        /* Unified view: concatenate all diffs */
        <div className="rounded-xl overflow-hidden" style={{ border: "1px solid var(--border)" }}>
          <div className="p-2">
            {files
              .filter((f) => f.diff)
              .map((f) => (
                <div key={f.path} className="mb-4 last:mb-0">
                  <div className="flex items-center gap-2 mb-2 px-2">
                    <span className="text-xs font-mono" style={{ color: "var(--text-primary)" }}>
                      {f.path}
                    </span>
                    <span
                      className="text-[9px] px-1.5 py-0.5 rounded-full"
                      style={{
                        background:
                          f.status === "accepted"
                            ? "color-mix(in srgb, var(--color-success) 10%, transparent)"
                            : f.status === "rejected"
                              ? "color-mix(in srgb, var(--error) 10%, transparent)"
                              : "color-mix(in srgb, var(--accent) 8%, transparent)",
                        color:
                          f.status === "accepted"
                            ? "var(--color-success)"
                            : f.status === "rejected"
                              ? "var(--error)"
                              : "var(--accent)",
                      }}
                    >
                      {f.status}
                    </span>
                  </div>
                  <DiffViewRaw diff={f.diff} />
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Bottom actions bar */}
      {files.length > 0 && pendingCount === 0 && (
        <div
          className="rounded-xl p-3 text-center text-sm"
          style={{
            background: "color-mix(in srgb, var(--color-success) 6%, transparent)",
            border: "1px solid color-mix(in srgb, var(--color-success) 15%, transparent)",
            color: "var(--color-success)",
          }}
        >
          All files have been reviewed.
          {acceptedCount > 0 && ` ${acceptedCount} accepted.`}
          {rejectedCount > 0 && ` ${rejectedCount} rejected.`}
        </div>
      )}
    </div>
  );
}

export type { ReviewFile, ReviewComment };
