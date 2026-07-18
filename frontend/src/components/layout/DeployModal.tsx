/* ── DeployModal — Frosted glass deploy flow ──
 *  Step-by-step animated deployment progress
 */
import { useState, useEffect, useCallback } from "react";

interface DeployModalProps {
  open: boolean;
  onClose: () => void;
}

const STEPS = [
  { label: "Validating configuration", icon: "✓" },
  { label: "Building project", icon: "📦" },
  { label: "Running tests", icon: "🧪" },
  { label: "Deploying to production", icon: "🚀" },
  { label: "Health check", icon: "💓" },
];

export function DeployModal({ open, onClose }: DeployModalProps) {
  const [currentStep, setCurrentStep] = useState(-1);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    if (!open) {
      setCurrentStep(-1);
      setComplete(false);
      return;
    }
    setCurrentStep(0);
  }, [open]);

  useEffect(() => {
    if (currentStep < 0 || currentStep >= STEPS.length) return;
    const delay = 1200 + Math.random() * 800;
    const timer = setTimeout(() => {
      if (currentStep === STEPS.length - 1) {
        setComplete(true);
      } else {
        setCurrentStep((s) => s + 1);
      }
    }, delay);
    return () => clearTimeout(timer);
  }, [currentStep]);

  const handleClose = useCallback(() => {
    setCurrentStep(-1);
    setComplete(false);
    onClose();
  }, [onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(8px)" }}
      onClick={handleClose}
    >
      <div
        className="w-full max-w-md rounded-2xl p-6"
        style={{
          background: "rgba(17,17,19,0.92)",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow:
            "0 32px 64px -16px rgba(0,0,0,0.8), inset 0 1px 0 rgba(255,255,255,0.04)",
          backdropFilter: "blur(24px)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h3
            className="text-sm font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            Deploy Project
          </h3>
          <button
            type="button"
            onClick={handleClose}
            className="flex h-6 w-6 items-center justify-center rounded-md transition-colors"
            style={{ color: "var(--text-quiet)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.06)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M4 4l6 6M10 4l-6 6" />
            </svg>
          </button>
        </div>

        {/* Steps */}
        <div className="flex flex-col gap-2">
          {STEPS.map((step, i) => {
            const isActive = i === currentStep && !complete;
            const isDone = i < currentStep || complete;
            const isPending = i > currentStep && !complete;

            return (
              <div
                key={step.label}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-all duration-300"
                style={{
                  background: isActive
                    ? "color-mix(in srgb, var(--accent) 8%, transparent)"
                    : "transparent",
                  border: isActive
                    ? "1px solid color-mix(in srgb, var(--accent) 12%, transparent)"
                    : "1px solid transparent",
                }}
              >
                {/* Status indicator */}
                <span
                  className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px]"
                  style={{
                    background: isDone
                      ? "color-mix(in srgb, var(--success) 15%, transparent)"
                      : isActive
                        ? "color-mix(in srgb, var(--accent) 15%, transparent)"
                        : "rgba(255,255,255,0.04)",
                    color: isDone
                      ? "var(--success)"
                      : isActive
                        ? "var(--accent)"
                        : "var(--text-quiet)",
                    boxShadow: isActive
                      ? "0 0 8px color-mix(in srgb, var(--accent) 20%, transparent)"
                      : "none",
                  }}
                >
                  {isDone ? (
                    "✓"
                  ) : isActive ? (
                    <span
                      className="inline-block h-2 w-2 rounded-full animate-pulse"
                      style={{ background: "var(--accent)" }}
                    />
                  ) : (
                    <span
                      className="inline-block h-1.5 w-1.5 rounded-full"
                      style={{ background: "var(--text-quiet)" }}
                    />
                  )}
                </span>

                {/* Label */}
                <span
                  className="text-xs"
                  style={{
                    color: isDone
                      ? "var(--text-subtle)"
                      : isActive
                        ? "var(--text-primary)"
                        : "var(--text-quiet)",
                    fontWeight: isActive ? 500 : 400,
                  }}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        {complete && (
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-200"
              style={{
                background:
                  "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                color: "white",
                boxShadow:
                  "0 0 16px color-mix(in srgb, var(--accent) 25%, transparent)",
              }}
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
