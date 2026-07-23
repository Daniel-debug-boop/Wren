import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAutoGeneration } from "#/hooks/useAutoGeneration";

/* ── Utility: format ms to readable duration ── */
function formatDuration(ms: number): string {
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}m ${sec}s`;
}

/* ── Stage status icons ── */
function StageIcon({
  status,
}: {
  status: "pending" | "running" | "done" | "error";
}) {
  if (status === "running") {
    return (
      <span className="flex h-6 w-6 items-center justify-center">
        <span
          className="h-3 w-3 animate-spin rounded-full border-2 border-transparent"
          style={{
            borderTopColor: "var(--accent)",
            borderRightColor: "var(--accent)",
          }}
        />
      </span>
    );
  }
  if (status === "done") {
    return (
      <span
        className="flex h-6 w-6 items-center justify-center rounded-full"
        style={{ background: "color-mix(in srgb, var(--success) 15%, transparent)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="var(--success)" strokeWidth="2" strokeLinecap="round">
          <path d="M3 6l2 2 4-4" />
        </svg>
      </span>
    );
  }
  if (status === "error") {
    return (
      <span
        className="flex h-6 w-6 items-center justify-center rounded-full"
        style={{ background: "color-mix(in srgb, var(--error) 15%, transparent)" }}
      >
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="var(--error)" strokeWidth="2" strokeLinecap="round">
          <path d="M4 4l4 4M8 4l-4 4" />
        </svg>
      </span>
    );
  }
  return (
    <span className="flex h-6 w-6 items-center justify-center">
      <span
        className="h-2 w-2 rounded-full"
        style={{ background: "var(--text-quiet)" }}
      />
    </span>
  );
}

/* ── File status icon ── */
function FileStatusIcon({
  status,
}: {
  status: "pending" | "generating" | "done" | "error" | "correcting";
}) {
  if (status === "generating") {
    return (
      <span className="h-3 w-3 animate-pulse rounded-full" style={{ background: "var(--accent)" }} />
    );
  }
  if (status === "correcting") {
    return (
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-dashed" style={{ borderColor: "var(--warning)" }} />
    );
  }
  if (status === "done") {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="var(--success)" strokeWidth="2" strokeLinecap="round">
        <path d="M3 6l2 2 4-4" />
      </svg>
    );
  }
  if (status === "error") {
    return (
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="var(--error)" strokeWidth="2" strokeLinecap="round">
        <path d="M4 4l4 4M8 4l-4 4" />
      </svg>
    );
  }
  return <span className="h-3 w-3 rounded-full" style={{ background: "var(--text-quiet)" }} />;
}

export default function GenerationPage() {
  const {
    status,
    prompt,
    projectName,
    stages,
    files,
    result,
    error,
    elapsedMs,
    isRunning,
    isDone,
    isError,
    startGeneration,
    cancelGeneration,
    reset,
  } = useAutoGeneration();

  const [goal, setGoal] = useState("");
  const [isInitializing, setIsInitializing] = useState(false);

  const handleSubmit = async () => {
    if (!goal.trim()) return;
    setIsInitializing(true);
    try {
      await startGeneration(goal.trim());
    } catch {
      // Error handled by store
    } finally {
      setIsInitializing(false);
    }
  };

  /* ── Input Screen (idle) ── */
  if (status === "idle") {
    return (
      <div className="flex h-full flex-col items-center justify-center px-6">
        <motion.div
          className="mx-auto flex w-full max-w-xl flex-col items-center gap-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Icon */}
          <div
            className="flex h-16 w-16 items-center justify-center rounded-2xl"
            style={{
              background:
                "linear-gradient(135deg, color-mix(in srgb, var(--accent) 15%, transparent), transparent)",
              border:
                "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
            }}
          >
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--accent)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
              <path d="M12 18v-6M9 15h6" />
            </svg>
          </div>

          <div className="text-center">
            <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>
              Automated Project Generator
            </h1>
            <p className="text-sm mt-2" style={{ color: "var(--text-subtle)" }}>
              Describe your project. Wren will plan, generate, and validate every file — from manifest to production code.
            </p>
          </div>

          {/* Goal input */}
          <div
            className="w-full rounded-xl p-1 transition-all duration-300"
            style={{
              border: "1px solid var(--border-strong)",
              background: "var(--surface)",
              boxShadow: "var(--shadow-md)",
            }}
          >
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder="e.g., Build a complete 3D solar system explorer with Three.js, planet info panels, and orbit animations..."
              rows={4}
              className="w-full resize-none border-none bg-transparent px-4 py-3 text-sm leading-relaxed outline-none"
              style={{
                color: "var(--text-primary)",
                caretColor: "var(--accent)",
              }}
            />
            <div className="flex items-center justify-between px-3 pb-3">
              <span className="text-[10px]" style={{ color: "var(--text-quiet)" }}>
                Press Enter to start generation
              </span>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!goal.trim() || isInitializing}
                className="press flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-xs font-semibold transition-all duration-200"
                style={{
                  background: !goal.trim()
                    ? "var(--border)"
                    : "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                  color: !goal.trim() ? "var(--text-quiet)" : "white",
                  boxShadow: goal.trim()
                    ? "0 0 16px color-mix(in srgb, var(--accent) 25%, transparent)"
                    : "none",
                }}
              >
                {isInitializing ? (
                  <>
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Initializing...
                  </>
                ) : (
                  <>
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    >
                      <path d="M5 1l5 5-5 5M1 6h9" />
                    </svg>
                    Generate Project
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Feature cards */}
          <div className="grid grid-cols-3 gap-3 w-full">
            {[
              { label: "Blueprint", desc: "LLM plans file tree & dependencies", icon: "M4 4h16v16H4z" },
              { label: "Generate", desc: "Sequential file generation with context", icon: "M12 2v20M2 12h20" },
              { label: "Validate", desc: "Auto-correct compilation errors", icon: "M9 12l2 2 4-4" },
            ].map((feat) => (
              <motion.div
                key={feat.label}
                className="rounded-xl p-3.5"
                style={{
                  background: "color-mix(in srgb, var(--surface-hover) 40%, transparent)",
                  border: "1px solid var(--border)",
                }}
                whileHover={{
                  y: -2,
                  borderColor: "color-mix(in srgb, var(--accent) 20%, transparent)",
                }}
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round">
                  <path d={feat.icon} />
                </svg>
                <p className="text-xs font-semibold mt-2" style={{ color: "var(--text-primary)" }}>{feat.label}</p>
                <p className="text-[10px] mt-0.5" style={{ color: "var(--text-subtle)" }}>{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    );
  }

  /* ── Pipeline Running / Done / Error Screen ── */
  return (
    <div className="flex h-full flex-col px-6 py-8">
      <motion.div
        className="mx-auto flex w-full max-w-2xl flex-col gap-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
              {isDone ? projectName || "Generation Complete" : "Generating Project"}
            </h1>
            <p className="text-xs mt-0.5" style={{ color: "var(--text-subtle)" }}>
              {prompt.slice(0, 80)}{prompt.length > 80 ? "..." : ""}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {isRunning && (
              <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                {formatDuration(elapsedMs)}
              </span>
            )}
            {isRunning && (
              <button
                type="button"
                onClick={cancelGeneration}
                className="press flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium"
                style={{
                  border: "1px solid var(--border)",
                  color: "var(--text-muted)",
                }}
              >
                Cancel
              </button>
            )}
            {(isDone || isError) && (
              <button
                type="button"
                onClick={reset}
                className="press flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold"
                style={{
                  background: "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                  color: "white",
                  boxShadow: "0 0 16px color-mix(in srgb, var(--accent) 25%, transparent)",
                }}
              >
                New Project
              </button>
            )}
          </div>
        </div>

        {/* ── Pipeline Stages ── */}
        <div className="flex flex-col gap-2">
          {stages.map((stage, i) => {
            const isActive = stage.status === "running";
            const isFinished = stage.status === "done" || stage.status === "error";

            return (
              <motion.div
                key={stage.name}
                className="relative rounded-xl p-4 transition-all duration-300"
                style={{
                  background: isActive
                    ? "color-mix(in srgb, var(--accent) 6%, var(--surface))"
                    : "var(--surface)",
                  border: `1px solid ${
                    isActive
                      ? "color-mix(in srgb, var(--accent) 25%, transparent)"
                      : stage.status === "error"
                        ? "color-mix(in srgb, var(--error) 25%, transparent)"
                        : isFinished
                          ? "color-mix(in srgb, var(--success) 15%, transparent)"
                          : "var(--border)"
                  }`,
                  opacity: stage.status === "pending" ? 0.6 : 1,
                }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="flex items-start gap-3">
                  <StageIcon status={stage.status} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-sm font-semibold"
                        style={{ color: "var(--text-primary)" }}
                      >
                        Stage {stage.index}: {stage.name}
                      </span>
                      {stage.duration_s !== undefined && stage.duration_s > 0 && (
                        <span className="text-[10px] font-mono" style={{ color: "var(--text-quiet)" }}>
                          {stage.duration_s.toFixed(1)}s
                        </span>
                      )}
                    </div>
                    {stage.detail && (
                      <p className="text-xs mt-1" style={{ color: "var(--text-subtle)" }}>
                        {stage.detail}
                      </p>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* ── File Progress ── */}
        {files.length > 0 && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
              Files ({files.length})
            </p>
            <div
              className="rounded-xl p-1"
              style={{
                border: "1px solid var(--border)",
                background: "color-mix(in srgb, var(--surface-hover) 30%, transparent)",
              }}
            >
              {files.map((file, i) => (
                <motion.div
                  key={file.path}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                >
                  <FileStatusIcon status={file.status as FileStatus["status"]} />
                  <span
                    className="text-xs font-mono truncate flex-1"
                    style={{
                      color:
                        file.status === "error"
                          ? "var(--error)"
                          : file.status === "done"
                            ? "var(--text-primary)"
                            : "var(--text-muted)",
                    }}
                  >
                    {file.path}
                  </span>
                  {file.error && (
                    <span
                      className="text-[9px] shrink-0 max-w-[120px] truncate"
                      style={{ color: "var(--error)" }}
                      title={file.error}
                    >
                      {file.error}
                    </span>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* ── Error Banner ── */}
        <AnimatePresence>
          {error && (
            <motion.div
              className="rounded-xl p-4"
              style={{
                background: "color-mix(in srgb, var(--error) 10%, transparent)",
                border: "1px solid color-mix(in srgb, var(--error) 25%, transparent)",
              }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <div className="flex items-start gap-2.5">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="var(--error)" strokeWidth="1.5" strokeLinecap="round" className="mt-0.5 shrink-0">
                  <circle cx="7" cy="7" r="6" />
                  <path d="M7 4.5v3M7 10h.01" />
                </svg>
                <div>
                  <p className="text-xs font-semibold" style={{ color: "var(--error)" }}>Error</p>
                  <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{error}</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Result Summary ── */}
        {isDone && result && (
          <motion.div
            className="rounded-xl p-5"
            style={{
              background: "color-mix(in srgb, var(--success) 8%, var(--surface))",
              border: "1px solid color-mix(in srgb, var(--success) 20%, transparent)",
            }}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <span
                className="flex h-8 w-8 items-center justify-center rounded-full"
                style={{ background: "color-mix(in srgb, var(--success) 20%, transparent)" }}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="var(--success)" strokeWidth="2" strokeLinecap="round">
                  <path d="M4 8l3 3 5-5" />
                  <circle cx="8" cy="8" r="7" />
                </svg>
              </span>
              <div>
                <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                  Project "{result.project_name}" generated successfully
                </p>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {result.files.length} files · {result.total_duration_s.toFixed(1)}s total
                </p>
              </div>
            </div>

            <div
              className="rounded-lg p-3 text-xs font-mono"
              style={{
                background: "color-mix(in srgb, #000 25%, transparent)",
                border: "1px solid var(--border)",
              }}
            >
              <span style={{ color: "var(--success)" }}>$</span>{" "}
              <span style={{ color: "var(--text-muted)" }}>cd</span>{" "}
              <span style={{ color: "var(--accent)" }}>{result.output_dir}</span>
            </div>

            {/* File list in result */}
            <div className="mt-4 flex flex-col gap-1">
              {result.files.slice(0, 10).map((f) => (
                <div key={f.path} className="flex items-center gap-2">
                  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke={f.success ? "var(--success)" : "var(--error)"} strokeWidth="1.5">
                    <path d={f.success ? "M2 5l2 2 4-4" : "M3 3l4 4M7 3l-4 4"} />
                  </svg>
                  <span className="text-xs font-mono" style={{ color: f.success ? "var(--text-muted)" : "var(--error)" }}>
                    {f.path}
                  </span>
                </div>
              ))}
              {result.files.length > 10 && (
                <p className="text-[10px] mt-1" style={{ color: "var(--text-quiet)" }}>
                  +{result.files.length - 10} more files
                </p>
              )}
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
