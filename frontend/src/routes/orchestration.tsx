import { useState } from "react";
import { motion } from "framer-motion";
import { AutonomousOrchestrator } from "#/components/ui/AutonomousOrchestrator";
import { OrchestrationApi } from "#/api/orchestration-service/orchestration-service.api";

export default function OrchestrationPage() {
  const [goal, setGoal] = useState("");
  const [submittedGoal, setSubmittedGoal] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);

  const handleSubmit = async () => {
    if (!goal.trim()) return;
    setIsInitializing(true);
    try {
      await OrchestrationApi.managerInit(goal.trim());
      setSubmittedGoal(goal.trim());
    } catch {
      // fallback — proceed anyway
      setSubmittedGoal(goal.trim());
    } finally {
      setIsInitializing(false);
    }
  };

  if (submittedGoal) {
    return (
      <div className="flex h-full flex-col" data-testid="orchestration-screen">
        <AutonomousOrchestrator goal={submittedGoal} />
      </div>
    );
  }

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
            <circle cx="12" cy="12" r="10" />
            <path d="M12 6v6l4 2" />
          </svg>
        </div>

        <div className="text-center">
          <h1
            className="text-xl font-bold"
            style={{ color: "var(--text-primary)" }}
          >
            Autonomous Orchestration
          </h1>
          <p className="text-sm mt-2" style={{ color: "var(--text-subtle)" }}>
            Set a high-level goal. Wren will decompose it into sub-tasks,
            execute them, review results, and learn from outcomes.
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
            placeholder="e.g., Build a complete authentication system with login, register, and password reset..."
            rows={3}
            className="w-full resize-none border-none bg-transparent px-4 py-3 text-sm leading-relaxed outline-none"
            style={{
              color: "var(--text-primary)",
              caretColor: "var(--accent)",
            }}
          />
          <div className="flex items-center justify-between px-3 pb-3">
            <span
              className="text-[10px]"
              style={{ color: "var(--text-quiet)" }}
            >
              Press Enter to start
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
                    <path d="M4 6l2 2 2-2" />
                    <circle cx="6" cy="6" r="5" />
                  </svg>
                  Start Orchestration
                </>
              )}
            </button>
          </div>
        </div>

        {/* Feature list */}
        <div className="grid grid-cols-2 gap-3 w-full">
          {[
            {
              label: "Goal Decomposition",
              desc: "Break down complex goals into ordered sub-tasks",
              icon: "M4 4h16v16H4z",
            },
            {
              label: "Sub-agent Execution",
              desc: "Spawn agents to work on tasks in parallel",
              icon: "M12 2a3 3 0 00-3 3v7a3 3 0 006 0V5a3 3 0 00-3-3z",
            },
            {
              label: "Self-Memory Loop",
              desc: "Learn from outcomes and improve over time",
              icon: "M12 6v6l4 2",
            },
            {
              label: "Working Memory",
              desc: "Track decisions, progress, and reflections",
              icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2",
            },
          ].map((feat) => (
            <motion.div
              key={feat.label}
              className="rounded-xl p-3.5"
              style={{
                background:
                  "color-mix(in srgb, var(--surface-hover) 40%, transparent)",
                border: "1px solid var(--border)",
              }}
              whileHover={{
                y: -2,
                borderColor:
                  "color-mix(in srgb, var(--accent) 20%, transparent)",
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 14 14"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="1.5"
                strokeLinecap="round"
              >
                <path d={feat.icon} />
              </svg>
              <p
                className="text-xs font-semibold mt-2"
                style={{ color: "var(--text-primary)" }}
              >
                {feat.label}
              </p>
              <p
                className="text-[10px] mt-0.5"
                style={{ color: "var(--text-subtle)" }}
              >
                {feat.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
