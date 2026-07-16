import { useState } from "react";
import { Button } from "./Button";

interface PlanStep {
  id: string;
  title: string;
  description: string;
  files: string[];
  estimatedTokens?: string;
  riskLevel?: "low" | "medium" | "high";
}

interface PlanViewProps {
  steps: PlanStep[];
  onApprove: () => void;
  onReject: () => void;
  onEditStep?: (stepId: string, description: string) => void;
}

export function PlanView({
  steps,
  onApprove,
  onReject,
  onEditStep,
}: PlanViewProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(
    steps[0]?.id ?? null,
  );
  const [editingStep, setEditingStep] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  const totalFiles = new Set(steps.flatMap((s) => s.files)).size;
  const highRiskCount = steps.filter((s) => s.riskLevel === "high").length;

  const handleEditStart = (step: PlanStep) => {
    setEditingStep(step.id);
    setEditText(step.description);
  };

  const handleEditSave = (stepId: string) => {
    onEditStep?.(stepId, editText);
    setEditingStep(null);
  };

  return (
    <div className="flex flex-col gap-4 animate-fade-in-up">
      {/* Plan header */}
      <div
        className="rounded-xl p-4"
        style={{
          background: "color-mix(in srgb, var(--accent) 6%, var(--surface))",
          border:
            "1px solid color-mix(in srgb, var(--accent) 15%, transparent)",
        }}
      >
        <div className="flex items-center gap-3 mb-3">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-lg"
            style={{
              background:
                "linear-gradient(135deg, var(--accent), var(--accent-hover))",
              boxShadow:
                "0 0 16px color-mix(in srgb, var(--accent) 20%, transparent)",
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="white"
              stroke="none"
            >
              <path d="M8 0L16 8L8 16L0 8L8 0Z" />
            </svg>
          </div>
          <div>
            <h3
              className="text-sm font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              Plan
            </h3>
            <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
              {steps.length} step{steps.length > 1 ? "s" : ""} · {totalFiles}{" "}
              file{totalFiles > 1 ? "s" : ""}
              {highRiskCount > 0 && ` · ${highRiskCount} high-risk`}
            </p>
          </div>
        </div>

        {/* Stats row */}
        <div className="flex gap-3 flex-wrap">
          <StatBadge label="Steps" value={String(steps.length)} />
          <StatBadge label="Files" value={String(totalFiles)} />
          <StatBadge
            label="Risk"
            value={highRiskCount > 0 ? "⚠ High" : "✓ Low"}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-2">
        {steps.map((step, idx) => (
          <div
            key={step.id}
            className="rounded-xl transition-all duration-200"
            style={{
              background: "var(--surface)",
              border: `1px solid ${expandedStep === step.id ? "color-mix(in srgb, var(--accent) 20%, transparent)" : "var(--border)"}`,
            }}
          >
            {/* Step header */}
            <button
              type="button"
              onClick={() =>
                setExpandedStep(expandedStep === step.id ? null : step.id)
              }
              className="flex w-full items-center gap-3 px-4 py-3 press text-left"
            >
              {/* Step number */}
              <span
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-xs font-bold"
                style={{
                  background:
                    "color-mix(in srgb, var(--accent) 12%, transparent)",
                  color: "var(--accent)",
                }}
              >
                {idx + 1}
              </span>

              {/* Step title + risk */}
              <div className="flex-1 min-w-0">
                <span
                  className="text-sm font-medium"
                  style={{ color: "var(--text-primary)" }}
                >
                  {step.title}
                </span>
              </div>

              {/* Risk indicator */}
              {step.riskLevel === "high" && (
                <span
                  className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium"
                  style={{
                    background:
                      "color-mix(in srgb, var(--diff-del) 15%, transparent)",
                    color: "var(--diff-del-text)",
                  }}
                >
                  High
                </span>
              )}
              {step.riskLevel === "medium" && (
                <span
                  className="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium"
                  style={{
                    background: "color-mix(in srgb, #f59e0b 15%, transparent)",
                    color: "#f59e0b",
                  }}
                >
                  Medium
                </span>
              )}

              {/* Estimated tokens */}
              {step.estimatedTokens && (
                <span
                  className="shrink-0 text-[10px]"
                  style={{ color: "var(--text-quiet)" }}
                >
                  ~{step.estimatedTokens}
                </span>
              )}

              {/* Expand */}
              <svg
                width="12"
                height="12"
                viewBox="0 0 12 12"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                style={{
                  color: "var(--text-quiet)",
                  transform:
                    expandedStep === step.id
                      ? "rotate(0deg)"
                      : "rotate(-90deg)",
                  transition: "transform 0.2s",
                }}
              >
                <path d="M3 4.5l3 3 3-3" />
              </svg>
            </button>

            {/* Expanded content */}
            {expandedStep === step.id && (
              <div
                className="border-t px-4 py-3"
                style={{ borderColor: "var(--border)" }}
              >
                {editingStep === step.id ? (
                  <div className="flex flex-col gap-2">
                    <textarea
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="w-full rounded-lg border bg-transparent p-2 text-xs leading-relaxed"
                      style={{
                        color: "var(--text-primary)",
                        borderColor: "var(--border-strong)",
                        minHeight: "80px",
                        fontFamily: "var(--font-mono)",
                      }}
                    />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => handleEditSave(step.id)}>
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditingStep(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p
                    className="text-xs leading-relaxed"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {step.description}
                  </p>
                )}

                {/* Files to touch */}
                {step.files.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {step.files.map((f) => (
                      <span
                        key={f}
                        className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10.5px] font-mono"
                        style={{
                          background:
                            "color-mix(in srgb, var(--accent) 6%, transparent)",
                          color: "var(--accent)",
                          border:
                            "1px solid color-mix(in srgb, var(--accent) 10%, transparent)",
                        }}
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                )}

                {/* Edit button */}
                {onEditStep && (
                  <button
                    type="button"
                    onClick={() => handleEditStart(step)}
                    className="mt-2 text-[10px] font-medium press"
                    style={{ color: "var(--text-quiet)" }}
                  >
                    Edit step
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 pt-2">
        <Button onClick={onApprove} size="md" className="flex-1">
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M2 7l3.5 3.5L12 3" />
          </svg>
          Approve & Execute
        </Button>
        <Button onClick={onReject} variant="ghost" size="md">
          Revise
        </Button>
      </div>
    </div>
  );
}

function StatBadge({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5"
      style={{
        background: "color-mix(in srgb, var(--accent) 5%, transparent)",
      }}
    >
      <span
        className="text-[10px] font-medium"
        style={{ color: "var(--text-subtle)" }}
      >
        {label}
      </span>
      <span
        className="text-xs font-semibold"
        style={{ color: "var(--text-primary)" }}
      >
        {value}
      </span>
    </div>
  );
}
