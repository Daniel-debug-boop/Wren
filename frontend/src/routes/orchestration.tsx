"use client";

import { useState } from "react";

/* ── Orchestration Page ─────────────────────────────────────────────────────
 * Agent pipeline visualization with status indicators and data flow.
 */

const PIPELINE = [
  {
    stage: "Architect",
    icon: (
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      >
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
      <svg
        width="18"
        height="18"
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
    ),
    desc: "Breaks architecture into concrete implementation steps with dependencies, estimates, and file assignments.",
    input: "Architecture document",
    output: "Implementation plan",
  },
  {
    stage: "Writer",
    icon: (
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      >
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
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      >
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
    <div className="mx-auto max-w-4xl animate-fade-up px-4 py-8 md:px-6 md:py-12">
      {/* Header */}
      <div className="mb-10">
        <h1
          className="font-display text-xl font-semibold tracking-tight md:text-2xl"
          style={{ color: "var(--text-primary)" }}
        >
          Agent Pipeline
        </h1>
        <p
          className="mt-1.5 text-sm leading-relaxed"
          style={{ color: "var(--text-tertiary)" }}
        >
          Wren's AI pipeline works in 4 stages. Each agent specializes in a
          distinct role, passing output to the next.
        </p>
      </div>

      {/* Pipeline Visualization */}
      <div className="mb-14">
        <div className="relative">
          <div
            className="absolute bottom-0 left-[23px] top-0 w-px"
            style={{
              background:
                "linear-gradient(180deg, var(--accent), var(--border))",
              opacity: 0.4,
            }}
          />

          <div className="space-y-5">
            {PIPELINE.map((agent, idx) => {
              const isActive = activeStage === idx;
              return (
                <div
                  key={agent.stage}
                  className="relative flex cursor-pointer gap-4 md:gap-5"
                  onMouseEnter={() => setActiveStage(idx)}
                  onMouseLeave={() => setActiveStage(null)}
                >
                  {/* Step node */}
                  <div
                    className="relative z-10 flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-xl transition-all duration-300 ease-out"
                    style={{
                      background: isActive
                        ? "var(--accent-strong)"
                        : "var(--bg-elevated)",
                      border: `1px solid ${isActive ? "var(--accent-strong)" : "rgba(217,119,87,0.30)"}`,
                      color: isActive ? "#fffaf7" : "var(--accent-strong)",
                      boxShadow: isActive
                        ? "var(--shadow-glow)"
                        : "var(--shadow-sm)",
                      transform: isActive ? "scale(1.06)" : "scale(1)",
                    }}
                  >
                    {isActive ? (
                      agent.icon
                    ) : (
                      <span className="font-display text-sm font-bold">
                        {idx + 1}
                      </span>
                    )}
                  </div>

                  {/* Content card */}
                  <div
                    className="flex-1 p-4 transition-all duration-300 ease-out"
                    style={{
                      border: `1px solid ${isActive ? "rgba(217,119,87,0.35)" : "var(--border)"}`,
                      borderRadius: "var(--radius-lg)",
                      background: isActive
                        ? "var(--bg-elevated)"
                        : "var(--bg-card)",
                      boxShadow: isActive
                        ? "var(--shadow-md)"
                        : "var(--shadow-sm)",
                      transform: isActive ? "translateX(2px)" : "translateX(0)",
                    }}
                  >
                    <div className="mb-1 flex flex-wrap items-center gap-2">
                      <span
                        className="font-display text-sm font-semibold"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {agent.stage}
                      </span>
                      <span
                        className="rounded-full px-2 py-0.5 text-[9px] font-medium tracking-wide"
                        style={{
                          background: "var(--accent-subtle)",
                          color: "var(--accent-strong)",
                        }}
                      >
                        Stage {idx + 1}
                      </span>
                    </div>
                    <p
                      className="text-xs leading-relaxed"
                      style={{ color: "var(--text-secondary)" }}
                    >
                      {agent.desc}
                    </p>
                    {isActive && (
                      <div
                        className="animate-fade-in mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t pt-2.5 text-[10px]"
                        style={{
                          borderColor: "var(--border)",
                          color: "var(--text-muted)",
                        }}
                      >
                        <span>
                          <span style={{ color: "var(--text-tertiary)" }}>
                            Input:
                          </span>{" "}
                          {agent.input}
                        </span>
                        <span>
                          <span style={{ color: "var(--text-tertiary)" }}>
                            Output:
                          </span>{" "}
                          {agent.output}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Connector arrow */}
                  {idx < PIPELINE.length - 1 && (
                    <div
                      className="absolute -bottom-2.5 left-[36px] z-20"
                      style={{ color: "var(--text-muted)" }}
                      aria-hidden="true"
                    >
                      <svg
                        width="10"
                        height="10"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M12 5v14M5 12l7 7 7-7" />
                      </svg>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* System Components */}
      <div className="mb-8">
        <h2
          className="font-display mb-5 text-lg font-semibold"
          style={{ color: "var(--text-primary)" }}
        >
          System Components
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {COMPONENTS.map((comp) => (
            <div key={comp.name} className="bento-card !p-4">
              <div className="mb-2 flex items-center gap-2">
                <span
                  className="h-1.5 w-1.5 shrink-0 rounded-full animate-pulse-dot"
                  style={{ background: "var(--status-success)" }}
                />
                <span
                  className="font-display text-[13px] font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  {comp.name}
                </span>
                <span
                  className="ml-auto rounded-full px-2 py-0.5 text-[9px] font-medium capitalize"
                  style={{
                    background: "rgba(74,124,89,0.08)",
                    color: "var(--status-success)",
                  }}
                >
                  {comp.status}
                </span>
              </div>
              <p
                className="text-[11px] leading-relaxed"
                style={{ color: "var(--text-tertiary)" }}
              >
                {comp.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
