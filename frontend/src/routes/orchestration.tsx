"use client";

/* ── Orchestration Page ─────────────────────────────────────────────────────
 * Multi-agent workflow orchestration — configure how Wren's pipeline
 * agents interact, share context, and hand off between stages.
 */

const PIPELINE = [
  {
    stage: "Architect",
    icon: "🏗️",
    desc: "Analyzes requirements and designs system architecture, component hierarchy, data models, and API contracts.",
    color: "amber",
  },
  {
    stage: "Planner",
    icon: "📋",
    desc: "Breaks architecture into concrete implementation steps with dependencies, estimates, and file assignments.",
    color: "amber",
  },
  {
    stage: "Writer",
    icon: "✍️",
    desc: "Generates production code for each step, following the plan and maintaining consistency across files.",
    color: "amber",
  },
  {
    stage: "Reviewer",
    icon: "🔍",
    desc: "Audits generated code for bugs, security vulnerabilities, edge cases, and adherence to best practices.",
    color: "amber",
  },
];

export default function OrchestrationPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          Agent Orchestration
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-tertiary)" }}>
          Wren's multi-agent pipeline works in stages — each agent specializes in a distinct role.
        </p>
      </div>

      <div className="relative">
        {/* Pipeline flow line */}
        <div className="absolute left-[23px] top-0 bottom-0 w-px" style={{ background: "var(--border)" }} />

        <div className="space-y-8">
          {PIPELINE.map((agent, idx) => (
            <div key={agent.stage} className="relative flex gap-5">
              {/* Icon circle */}
              <div className="relative z-10 flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-xl text-lg" style={{ background: "var(--accent-subtle)", border: "1px solid rgba(245,158,11,0.2)" }}>
                {agent.icon}
              </div>
              {/* Content */}
              <div className="card flex-1 p-5">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    {agent.stage}
                  </span>
                  <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ background: "var(--accent-subtle)", color: "var(--accent)" }}>
                    Agent {idx + 1} of {PIPELINE.length}
                  </span>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                  {agent.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
