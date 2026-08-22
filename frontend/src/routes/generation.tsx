"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { generationApi } from "#/api/endpoints";
import type { PipelineStage } from "#/types/api";

/* ── Generation Pipeline Page ────────────────────────────────────────────────
 * Full AI generation pipeline UI with stage-by-stage progress,
 * real-time status polling, and results display.
 */

const PIPELINE_STAGES: {
  key: PipelineStage;
  label: string;
  icon: React.ReactNode;
  desc: string;
}[] = [
  {
    key: "architect",
    label: "Architect",
    desc: "Designing system architecture",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 2L2 7l10 5 10-5-10-5Z" />
        <path d="m2 17 10 5 10-5" />
        <path d="m2 12 10 5 10-5" />
      </svg>
    ),
  },
  {
    key: "planner",
    label: "Planner",
    desc: "Creating implementation plan",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <line x1="8" y1="6" x2="21" y2="6" />
        <line x1="8" y1="12" x2="21" y2="12" />
        <line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" />
        <line x1="3" y1="12" x2="3.01" y2="12" />
        <line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
  {
    key: "writer",
    label: "Writer",
    desc: "Generating code",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
      </svg>
    ),
  },
  {
    key: "reviewer",
    label: "Reviewer",
    desc: "Reviewing for quality",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    key: "complete",
    label: "Complete",
    desc: "Generation finished",
    icon: (
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
  },
];

const SAMPLES = [
  "Build a 3D solar system explorer with Three.js",
  "Create a real-time chat app with WebSocket and React",
  "Build a markdown blog with Next.js and Tailwind CSS",
  "Create a REST API for a task management app",
  "Build a portfolio website with dark mode and animations",
  "Create an AI-powered image gallery with search",
];

export default function GenerationPage() {
  const [prompt, setPrompt] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [pollInterval, setPollInterval] = useState<ReturnType<
    typeof setInterval
  > | null>(null);
  const [result, setResult] = useState<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Start generation
  const startMutation = useMutation({
    mutationFn: (prompt: string) => generationApi.start({ prompt }),
    onSuccess: (data) => {
      setTaskId(data.task_id);
      setResult(null);
    },
  });

  // Poll status
  const { data: statusData, refetch: refetchStatus } = useQuery({
    queryKey: ["generation-status", taskId],
    queryFn: () => (taskId ? generationApi.status(taskId) : null),
    enabled: false, // We'll manually trigger via interval
  });

  // Fetch final result
  const { data: resultData } = useQuery({
    queryKey: ["generation-result", taskId],
    queryFn: () => (taskId ? generationApi.result(taskId) : null),
    enabled: false,
  });

  // Poll for status updates
  useEffect(() => {
    if (taskId && !pollInterval) {
      const interval = setInterval(async () => {
        try {
          const res = await generationApi.status(taskId);
          if (res.status === "completed" || res.status === "error") {
            clearInterval(interval);
            setPollInterval(null);
            // Fetch result
            try {
              const resultRes = await generationApi.result(taskId);
              setResult(resultRes);
            } catch {}
          }
        } catch {}
      }, 2000);
      setPollInterval(interval);
    }
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [taskId]);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    if (pollInterval) clearInterval(pollInterval);
    setPollInterval(null);
    startMutation.mutate(prompt.trim());
  };

  const handleSampleClick = (sample: string) => {
    setPrompt(sample);
    if (textareaRef.current) textareaRef.current.focus();
  };

  const handleReset = () => {
    if (pollInterval) clearInterval(pollInterval);
    setPollInterval(null);
    setTaskId(null);
    setResult(null);
    startMutation.reset();
  };

  const isRunning = !!(startMutation.isPending || (taskId && !result));
  const currentStatus = statusData;
  const currentStage = currentStatus?.stage || "";

  const getStageIndex = (stage: string) => {
    const idx = PIPELINE_STAGES.findIndex((s) => s.key === stage);
    return idx >= 0 ? idx : -1;
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 md:px-6 md:py-12">
      {/* Header */}
      <div className="animate-fade-up mb-8">
        <h1
          className="font-display text-xl font-semibold tracking-tight md:text-2xl"
          style={{ color: "var(--text-primary)" }}
        >
          AI Project Generator
        </h1>
        <p
          className="mt-1.5 text-sm leading-relaxed"
          style={{ color: "var(--text-tertiary)" }}
        >
          Describe your project and Wren's AI pipeline will architect, plan,
          write, and review it.
        </p>
      </div>

      {/* Input Section */}
      <div
        className="card animate-fade-up mb-6 p-5 transition-shadow duration-300 ease-out focus-within:border-[var(--accent)] focus-within:shadow-md md:p-6"
        style={{ transitionDelay: "40ms" }}
      >
        <textarea
          ref={textareaRef}
          className="input min-h-[120px] mb-4 w-full resize-y !border-[var(--border)]"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what you want to build..."
          disabled={isRunning}
        />
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-1.5">
            {SAMPLES.slice(0, 4).map((sample) => (
              <button
                key={sample}
                onClick={() => handleSampleClick(sample)}
                disabled={isRunning}
                className="rounded-full border px-3 py-1 text-xs transition-all duration-200 ease-out hover:-translate-y-px disabled:opacity-50"
                style={{
                  background: "var(--bg-elevated)",
                  color: "var(--text-secondary)",
                  borderColor: "var(--border-strong)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "var(--accent-subtle)";
                  e.currentTarget.style.color = "var(--accent-strong)";
                  e.currentTarget.style.borderColor = "rgba(217,119,87,0.30)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "var(--bg-elevated)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                  e.currentTarget.style.borderColor = "var(--border-strong)";
                }}
              >
                {sample.length > 30 ? `${sample.slice(0, 30)}...` : sample}
              </button>
            ))}
          </div>
          <div className="flex shrink-0 gap-2">
            {taskId && (
              <button
                onClick={handleReset}
                className="rounded-lg border px-4 py-2 text-xs font-medium transition-all duration-200 ease-out hover:-translate-y-px"
                style={{
                  color: "var(--text-secondary)",
                  borderColor: "var(--border-strong)",
                  background: "var(--bg-elevated)",
                }}
              >
                Reset
              </button>
            )}
            <button
              onClick={handleGenerate}
              disabled={!prompt.trim() || isRunning}
              className="accent-button text-xs"
            >
              {startMutation.isPending ? (
                <span className="flex items-center gap-2">
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Starting...
                </span>
              ) : isRunning ? (
                <span className="flex items-center gap-2">
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Running...
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  Generate Project
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  >
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Pipeline Progress */}
      {(isRunning || result) && (
        <div className="card animate-fade-up mb-6 p-5 md:p-6">
          <h2
            className="font-display mb-5 text-sm font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            Pipeline Progress
          </h2>
          <div className="space-y-2.5">
            {PIPELINE_STAGES.map((stage, idx) => {
              const stageIdx = getStageIndex(currentStage);
              const isActive = idx <= stageIdx && stage.key !== "complete";
              const isComplete =
                idx < stageIdx || (result && stage.key === "complete");
              const isCurrent = stage.key === currentStage;

              return (
                <div
                  key={stage.key}
                  className="flex items-center gap-3.5 rounded-xl border px-4 py-3 transition-all duration-300 ease-out"
                  style={{
                    background: isCurrent
                      ? "var(--accent-subtle)"
                      : "var(--bg-deep)",
                    borderColor: isCurrent
                      ? "rgba(217,119,87,0.35)"
                      : "transparent",
                    opacity: isActive ? 1 : 0.45,
                    boxShadow: isCurrent ? "var(--shadow-sm)" : "none",
                  }}
                >
                  <span
                    className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors duration-300"
                    style={{
                      background: isComplete
                        ? "rgba(74,124,89,0.10)"
                        : "var(--accent-subtle)",
                      color: isComplete
                        ? "var(--status-success)"
                        : "var(--accent-strong)",
                    }}
                  >
                    {isComplete ? (
                      <svg
                        width="15"
                        height="15"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      stage.icon
                    )}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-y-1">
                      <span
                        className="text-sm font-medium"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {stage.label}
                      </span>
                      {isComplete && (
                        <span
                          className="text-xs font-medium"
                          style={{ color: "var(--status-success)" }}
                        >
                          ✓ Complete
                        </span>
                      )}
                      {isCurrent && (
                        <span
                          className="flex items-center gap-1.5 text-xs font-medium"
                          style={{ color: "var(--accent-strong)" }}
                        >
                          <span
                            className="animate-pulse-dot h-2 w-2 rounded-full"
                            style={{ background: "var(--accent)" }}
                          />
                          {statusData?.message || stage.desc}
                        </span>
                      )}
                    </div>
                    {/* Progress bar */}
                    <div
                      className="mt-2 h-1 w-full overflow-hidden rounded-full"
                      style={{ background: "var(--border)" }}
                    >
                      <div
                        className="h-full rounded-full transition-all duration-500 ease-out"
                        style={{
                          width: isComplete ? "100%" : isCurrent ? "60%" : "0%",
                          background: isComplete
                            ? "var(--status-success)"
                            : "linear-gradient(90deg, var(--accent), var(--accent-hover))",
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="animate-fade-up space-y-4">
          {result.error && (
            <div
              className="rounded-xl border p-4"
              style={{
                borderColor: "rgba(191,66,64,0.25)",
                background: "rgba(191,66,64,0.05)",
              }}
            >
              <p className="text-sm" style={{ color: "var(--status-error)" }}>
                {result.error}
              </p>
            </div>
          )}

          {/* File Results */}
          {result.total_files !== undefined && result.total_files > 0 && (
            <div className="card p-5 md:p-6">
              <h3
                className="mb-4 flex items-center gap-2 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-lg"
                  style={{
                    background: "var(--accent-subtle)",
                    color: "var(--accent-strong)",
                  }}
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  >
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                  </svg>
                </span>
                Generated Files
                <span
                  className="ml-auto text-[10px] font-normal"
                  style={{ color: "var(--text-muted)" }}
                >
                  {result.total_files} files, {result.total_lines} lines
                </span>
              </h3>
              <div className="space-y-1">
                {result.files.map((file: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs transition-colors duration-150 hover:bg-black/[0.03]"
                    style={{ background: "var(--bg-deep)" }}
                  >
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      style={{ color: "var(--accent-strong)" }}
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                    <span
                      className="truncate font-mono"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {file.path}
                    </span>
                    <span
                      className="ml-auto shrink-0 text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {file.lines} lines
                    </span>
                  </div>
                ))}
              </div>
              {result.project_path && (
                <div
                  className="mt-3 px-3 text-[10px]"
                  style={{ color: "var(--text-muted)" }}
                >
                  Saved to:{" "}
                  <span className="font-mono">{result.project_path}</span>
                </div>
              )}
            </div>
          )}

          {/* Architecture */}
          {result.architecture && (
            <details className="card group">
              <summary
                className="acc-summary flex list-none items-center gap-2 p-4 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-lg"
                  style={{
                    background: "var(--accent-subtle)",
                    color: "var(--accent-strong)",
                  }}
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  >
                    <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                    <path d="m2 17 10 5 10-5" />
                  </svg>
                </span>
                Architecture
                <svg
                  className="acc-chevron ml-auto"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--text-muted)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </summary>
              <div
                className="border-t px-5 pb-5 pt-4"
                style={{ borderColor: "var(--border)" }}
              >
                <pre
                  className="whitespace-pre-wrap font-sans text-[13px] leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {result.architecture}
                </pre>
              </div>
            </details>
          )}

          {/* Plan */}
          {result.plan && (
            <details className="card group">
              <summary
                className="acc-summary flex list-none items-center gap-2 p-4 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-lg"
                  style={{
                    background: "var(--accent-subtle)",
                    color: "var(--accent-strong)",
                  }}
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  >
                    <line x1="8" y1="6" x2="21" y2="6" />
                    <line x1="8" y1="12" x2="21" y2="12" />
                    <line x1="8" y1="18" x2="21" y2="18" />
                    <line x1="3" y1="6" x2="3.01" y2="6" />
                    <line x1="3" y1="12" x2="3.01" y2="12" />
                    <line x1="3" y1="18" x2="3.01" y2="18" />
                  </svg>
                </span>
                Implementation Plan
                <svg
                  className="acc-chevron ml-auto"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--text-muted)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </summary>
              <div
                className="border-t px-5 pb-5 pt-4"
                style={{ borderColor: "var(--border)" }}
              >
                <pre
                  className="whitespace-pre-wrap font-sans text-[13px] leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {result.plan}
                </pre>
              </div>
            </details>
          )}

          {/* Review */}
          {result.review && (
            <details className="card group">
              <summary
                className="acc-summary flex list-none items-center gap-2 p-4 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-lg"
                  style={{
                    background: "var(--accent-subtle)",
                    color: "var(--accent-strong)",
                  }}
                >
                  <svg
                    width="13"
                    height="13"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </span>
                Code Review
                <svg
                  className="acc-chevron ml-auto"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--text-muted)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </summary>
              <div
                className="border-t px-5 pb-5 pt-4"
                style={{ borderColor: "var(--border)" }}
              >
                <pre
                  className="whitespace-pre-wrap font-sans text-[13px] leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {result.review}
                </pre>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
