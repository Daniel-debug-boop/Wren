"use client";

import { useState } from "react";

/* ── Orchestration Page ─────────────────────────────────────────────────────
 * Agent pipeline visualization with status indicators and data flow.
 */

const PIPELINE = [
  {
    stage: "Architect",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <path d="M12 2L2 7l10 5 10-5-10-5Z" />
        <path d="m2 17 10 5 10-5" />
        <path d="m2 12 10 5 10-5" />
      </svg>
    ),
    desc: "Analyzes requirements and designs system architecture, component hierarchy, data models, and API contracts.",
    input: "User prompt",
    output: "Architecture document",
  },
  {
    stage: "Planner",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <line x1="8" y1="6" x2="21" y2="6" />
        <line x1="8" y1="12" x2="21" y2="12" />
        <line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" />
        <line x1="3" y1="12" x2="3.01" y2="12" />
        <line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
    desc: "Breaks architecture into concrete implementation steps with dependencies, estimates, and file assignments.",
    input: "Architecture document",
    output: "Implementation plan",
  },
  {
    stage: "Writer",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
      </svg>
    ),
    desc: "Generates production code for each step, following the plan and maintaining consistency across files.",
    input: "Implementation plan",
    output: "Code files (written to disk)",
  },
  {
    stage: "Reviewer",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
    desc: "Audits generated code for bugs, security vulnerabilities, edge cases, and adherence to best practices.",
    input: "Generated code",
    output: "Review report + quality score",
  },
];

const COMPONENTS = [
  {
    name: "LLM Gateway",
    desc: "Routes requests to your configured provider (OpenAI, Anthropic, OpenRouter, etc.)",
    status: "active",
  },
  {
    name: "Code Extractor",
    desc: "Parses LLM output, extracts fenced code blocks, and writes them as real files",
    status: "active",
  },
  {
    name: "PTY Terminal",
    desc: "Real pseudo-terminal via Python pty module, connected to xterm.js in the browser",
    status: "active",
  },
  {
    name: "File Storage",
    desc: "JSON-based persistence for conversations, settings, and API keys",
    status: "active",
  },
];

export default function OrchestrationPage() {
  const [activeStage, setActiveStage] = useState<number | null>(null);

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          Agent Pipeline
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-tertiary)" }}>
          Wren's AI pipeline works in 4 stages. Each agent specializes in a distinct role, passing output to the next.
        </p>
      </div>

      {/* Pipeline Visualization */}
      <div className="mb-12">
        <div className="relative">
          <div className="absolute left-[23px] top-0 bottom-0 w-px" style={{ background: "var(--border)" }} />

          <div className="space-y-4">
            {PIPELINE.map((agent, idx) => (
              <div
                key={agent.stage}
                className="relative flex gap-5 cursor-pointer"
                onMouseEnter={() => setActiveStage(idx)}
                onMouseLeave={() => setActiveStage(null)}
              >
                {/* Step number */}
                <div
                  className="relative z-10 flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-xl transition-all"
                  style={{
                    background: activeStage === idx ? "var(--accent)" : "var(--accent-subtle)",
                    border: `1px solid ${activeStage === idx ? "var(--accent)" : "rgba(245,158,11,0.2)"}`,
                    color: activeStage === idx ? "#0A0A0C" : "var(--accent)",
                  }}
                >
                  {activeStage === idx ? agent.icon : (
                    <span className="text-sm font-bold">{idx + 1}</span>
                  )}
                </div>

                {/* Content card */}
                <div
                  className="flex-1 p-4 transition-all"
                  style={{
                    border: `1px solid ${activeStage === idx ? "rgba(245,158,11,0.2)" : "var(--border)"}`,
                    borderRadius: "12px",
                    background: activeStage === idx ? "var(--bg-elevated)" : "var(--bg-card)",
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                      {agent.stage}
                    </span>
                    <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ background: "var(--accent-subtle)", color: "var(--accent)" }}>
                      Stage {idx + 1}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                    {agent.desc}
                  </p>
                  {activeStage === idx && (
                    <div className="mt-3 flex gap-4 text-[10px]" style={{ color: "var(--text-muted)" }}>
                      <span>Input: {agent.input}</span>
                      <span>Output: {agent.output}</span>
                    </div>
                  )}
                </div>

                {/* Arrow */}
                {idx < PIPELINE.length - 1 && (
                  <div className="absolute left-[36px] -bottom-2 z-20 text-[10px]" style={{ color: "var(--text-muted)" }}>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 5v14M5 12l7 7 7-7" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System Components */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
          System Components
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {COMPONENTS.map((comp) => (
            <div key={comp.name} className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: "var(--status-success, #22C55E)" }} />
                <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>
                  {comp.name}
                </span>
              </div>
              <p className="text-[11px] leading-relaxed" style={{ color: "var(--text-tertiary)" }}>
                {comp.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
