"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { generationApi } from "#/api/endpoints";
import type { PipelineStage } from "#/types/api";

/* ── Generation Pipeline Page ────────────────────────────────────────────────
 * Full AI generation pipeline UI with stage-by-stage progress,
 * real-time status polling, and results display.
 */

const PIPELINE_STAGES: { key: PipelineStage; label: string; icon: string; desc: string }[] = [
  { key: "architect", label: "Architect", icon: "🏗️", desc: "Designing system architecture" },
  { key: "planner", label: "Planner", icon: "📋", desc: "Creating implementation plan" },
  { key: "writer", label: "Writer", icon: "✍️", desc: "Generating code" },
  { key: "reviewer", label: "Reviewer", icon: "🔍", desc: "Reviewing for quality" },
  { key: "complete", label: "Complete", icon: "✅", desc: "Generation finished" },
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
  const [pollInterval, setPollInterval] = useState<ReturnType<typeof setInterval> | null>(null);
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
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          AI Project Generator
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-tertiary)" }}>
          Describe your project and Wren's AI pipeline will architect, plan, write, and review it.
        </p>
      </div>

      {/* Input Section */}
      <div className="card p-6 mb-6">
        <textarea
          ref={textareaRef}
          className="input w-full min-h-[120px] mb-3 resize-y"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe what you want to build..."
          disabled={isRunning}
        />
        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-1.5">
            {SAMPLES.slice(0, 4).map((sample) => (
              <button
                key={sample}
                onClick={() => handleSampleClick(sample)}
                disabled={isRunning}
                className="rounded-full px-3 py-1 text-xs transition-all hover:opacity-80"
                style={{
                  background: "var(--surface)",
                  color: "var(--text-tertiary)",
                  border: "1px solid var(--border)",
                }}
              >
                {sample.length > 30 ? sample.slice(0, 30) + "..." : sample}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            {taskId && (
              <button onClick={handleReset} className="rounded-lg px-4 py-2 text-xs transition-colors hover:bg-white/5" style={{ color: "var(--text-secondary)", border: "1px solid var(--border)" }}>
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
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
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
        <div className="card p-6 mb-6">
          <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
            Pipeline Progress
          </h2>
          <div className="space-y-3">
            {PIPELINE_STAGES.map((stage, idx) => {
              const stageIdx = getStageIndex(currentStage);
              const isActive = idx <= stageIdx && stage.key !== "complete";
              const isComplete = idx < stageIdx || (result && stage.key === "complete");
              const isCurrent = stage.key === currentStage;

              return (
                <div
                  key={stage.key}
                  className="flex items-center gap-3 rounded-lg px-4 py-3 transition-all"
                  style={{
                    background: isCurrent ? "rgba(139,92,246,0.08)" : "var(--surface)",
                    border: isCurrent ? "1px solid var(--accent)" : "1px solid transparent",
                    opacity: isActive ? 1 : 0.4,
                  }}
                >
                  <span className="text-lg">{stage.icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {stage.label}
                      </span>
                      {isComplete && <span className="text-xs text-emerald-400">✓ Complete</span>}
                      {isCurrent && (
                        <span className="flex items-center gap-1 text-xs" style={{ color: "var(--accent)" }}>
                          <span className="h-2 w-2 animate-pulse rounded-full" style={{ background: "var(--accent)" }} />
                          {statusData?.message || stage.desc}
                        </span>
                      )}
                    </div>
                    {/* Progress bar */}
                    <div className="mt-1.5 h-1 w-full rounded-full" style={{ background: "var(--border)" }}>
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: isComplete ? "100%" : isCurrent ? "60%" : "0%",
                          background: isComplete ? "rgb(52,211,153)" : "var(--accent)",
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
        <div className="space-y-4">
          {result.error && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4">
              <p className="text-sm text-red-400">{result.error}</p>
            </div>
          )}

          {result.architecture && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                🏗️ Architecture
              </h3>
              <pre className="whitespace-pre-wrap text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {result.architecture}
              </pre>
            </div>
          )}

          {result.plan && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                📋 Implementation Plan
              </h3>
              <pre className="whitespace-pre-wrap text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {result.plan}
              </pre>
            </div>
          )}

          {result.code && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                ✍️ Generated Code
              </h3>
              <pre className="whitespace-pre-wrap text-xs leading-relaxed" style={{ color: "var(--text-secondary)", fontFamily: "ui-monospace, monospace" }}>
                {result.code}
              </pre>
            </div>
          )}

          {result.review && (
            <div className="card p-6">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                🔍 Code Review
              </h3>
              <pre className="whitespace-pre-wrap text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {result.review}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
