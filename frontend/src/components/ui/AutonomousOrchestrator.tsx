/* Autonomous Orchestrator — Full end-to-end execution without user intervention */
import { useEffect, useState } from "react";
import { PlanView } from "./PlanView";
import { ReviewWorkspace } from "./ReviewWorkspace";
import { StackTraceViewer } from "./StackTraceViewer";
import { IDEWorkspace } from "../ide/IDEWorkspace";

interface OrchestrationStep {
  id: string;
  type: "plan" | "execute" | "review" | "debug";
  status: "pending" | "running" | "done" | "error";
  title: string;
  detail?: string;
}

interface AutonomousOrchestratorProps {
  goal: string; // The user's original request
  files: Array<{ path: string; type: "file" | "folder"; children?: string[] }>;
  timelineEvents: Array<{
    id: string;
    type: "action" | "observation" | "message" | "error" | "status";
    title: string;
    status: "running" | "done" | "error" | "skipped";
  }>;
  terminalLines: Array<{ id: string; type: "input" | "output" | "system"; text: string; timestamp: number }>;
  diffs: Array<{ path: string; diff: string; status: "pending" | "accepted" | "rejected"; comments: { id: string; line: number; text: string }[] }>;
}

export function AutonomousOrchestrator({ goal, files, timelineEvents, terminalLines, diffs }: AutonomousOrchestratorProps) {
  const [phase, setPhase] = useState<"planning" | "executing" | "reviewing" | "debugging">("planning");
  const [planSteps, setPlanSteps] = useState([
    { id: "1", type: "plan" as const, status: "running" as const, title: "Analyze requirements" },
    { id: "2", type: "execute" as const, status: "pending" as const, title: "Implement changes" },
    { id: "3", type: "review" as const, status: "pending" as const, title: "Self-review & fix" },
    { id: "4", type: "execute" as const, status: "pending" as const, title: "Final verification" },
  ]);

  // Progress phase based on timeline events
  useEffect(() => {
    const lastEvent = timelineEvents[timelineEvents.length - 1];
    if (!lastEvent) return;
    if (lastEvent.type === "error") {
      setPhase("debugging");
    } else if (diffs.length > 0 && lastEvent.status === "done") {
      setPhase("reviewing");
    } else if (lastEvent.type === "action" && lastEvent.status === "running") {
      setPhase("executing");
    }
  }, [timelineEvents, diffs]);

  const progressPct = () => {
    switch (phase) {
      case "planning": return 25;
      case "executing": return 50;
      case "reviewing": return 75;
      case "debugging": return 40;
      default: return 0;
    }
  };

  return (
    <div className="flex h-full flex-col" data-testid="autonomous-orchestrator">
      {/* Header with goal and progress */}
      <div
        className="shrink-0 border-b px-4 py-3"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
            </svg>
            <div>
              <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                Autonomous Agent
              </h2>
              <p className="text-xs truncate" style={{ color: "var(--text-subtle)" }}>
                {goal.slice(0, 80)}{goal.length > 80 ? "..." : ""}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium" style={{ color: "var(--text-quiet)" }}>
              {progressPct()}% complete
            </span>
            <div className="h-1.5 w-24 rounded-full" style={{ background: "var(--border)" }}>
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPct()}%`, background: "var(--accent)" }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main content - phases */}
      <div className="flex-1 overflow-hidden">
        {phase === "planning" && (
          <div className="p-4">
            <PlanView
              steps={planSteps.map((s) => ({
                id: s.id,
                title: s.title,
                description: s.detail || "Working...",
                files: [],
                riskLevel: "low",
              }))}
              onApprove={() => setPhase("executing")}
              onReject={() => setPhase("planning")}
            />
          </div>
        )}

        {phase === "executing" && (
          <IDEWorkspace
            files={files}
            timelineEvents={timelineEvents}
            terminalLines={terminalLines}
          />
        )}

        {phase === "reviewing" && (
          <div className="p-4">
            <ReviewWorkspace
              files={diffs.map((d) => ({
                path: d.path,
                diff: d.diff,
                status: d.status,
                comments: d.comments,
              }))}
              onApproveAll={() => setPhase("executing")}
              onRejectAll={() => setPhase("executing")}
            />
          </div>
        )}

        {phase === "debugging" && (
          <div className="p-4">
            <StackTraceViewer
              errorMessage={timelineEvents.find((e) => e.type === "error")?.title || "Runtime error"}
              errorType="RuntimeError"
            />
          </div>
        )}
      </div>

      {/* Footer with controls */}
      <div
        className="shrink-0 border-t px-4 py-2 flex items-center justify-between"
        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
      >
        <div className="flex items-center gap-4 text-xs">
          <button
            type="button"
            className="flex items-center gap-1.5 press transition-opacity hover:opacity-80"
            style={{ color: "var(--text-quiet)" }}
          >
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M2 1.5h6a1 1 0 011 1v11a1 1 0 01-1 1H2a1 1 0 01-1-1v-11a1 1 0 011-1z" />
              <path d="M5 4v2M4 5h2" />
            </svg>
            Pause
          </button>
          <button
            type="button"
            className="flex items-center gap-1.5 press transition-opacity hover:opacity-80"
            style={{ color: "var(--error)" }}
          >
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M2 2l6 6M8 2l-6 6" />
            </svg>
            Stop
          </button>
        </div>
        <span className="text-xs" style={{ color: "var(--text-quiet)" }}>
          {phase === "planning" && "Analyzing..."}
          {phase === "executing" && "Implementing changes..."}
          {phase === "reviewing" && "Reviewing output..."}
          {phase === "debugging" && "Debugging..."}
        </span>
      </div>
    </div>
  );
}