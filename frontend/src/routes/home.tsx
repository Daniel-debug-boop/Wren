"use client";

import { Link } from "react-router";

/* ── Landing Page ───────────────────────────────────────────────────────────
 * Honest, clean landing page that accurately represents Wren's capabilities.
 * Warm ivory canvas, terracotta accent, serif display voice. Bento features.
 */

const FEATURES = [
  {
    title: "AI Chat",
    description:
      "Real-time streaming responses from OpenAI, Anthropic, OpenRouter, or any OpenAI-compatible API. Multi-turn conversations with context.",
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
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    tag: "Core",
  },
  {
    title: "Code Generation Pipeline",
    description:
      "4-stage pipeline: Architect, Planner, Writer, Reviewer. Generates real files written to your workspace -- not just text output.",
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
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    tag: "AI Pipeline",
  },
  {
    title: "Real Terminal",
    description:
      "Interactive PTY shell via xterm.js. Run bash/zsh, install packages, execute scripts -- a real terminal, not a simulation.",
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
        <polyline points="4 17 10 11 4 5" />
        <line x1="12" y1="19" x2="20" y2="19" />
      </svg>
    ),
    tag: "Terminal",
  },
  {
    title: "Monaco Editor",
    description:
      "Full VS Code editor in your browser. Syntax highlighting for 16+ languages, IntelliSense, multi-file editing, Ctrl+S save.",
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
    tag: "Editor",
  },
  {
    title: "File Explorer",
    description:
      "Browse, read, and write files directly from the browser. Workspace-aware with path traversal protection.",
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
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
    ),
    tag: "Files",
  },
  {
    title: "Git Integration",
    description:
      "Initialize repos, clone repositories, commit changes, view diffs and logs -- all from the UI or terminal.",
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
        <circle cx="18" cy="18" r="3" />
        <circle cx="6" cy="6" r="3" />
        <path d="M13 6h3a2 2 0 0 1 2 2v7" />
        <line x1="6" y1="9" x2="6" y2="21" />
      </svg>
    ),
    tag: "Git",
  },
];

export default function HomePage() {
  return (
    <div style={{ background: "var(--bg-deep)" }}>
      {/* ── Navigation ── */}
      <nav
        className="glass fixed top-0 left-0 right-0 z-50"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="group flex items-center gap-2.5">
            <div
              className="flex h-7 w-7 items-center justify-center rounded-lg transition-transform duration-300 ease-spring group-hover:scale-105"
              style={{ background: "var(--accent)" }}
            >
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#fffaf7"
                strokeWidth="2.5"
                strokeLinecap="round"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                <path d="m2 17 10 5 10-5" />
                <path d="m2 12 10 5 10-5" />
              </svg>
            </div>
            <span
              className="font-display text-[17px] font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              Wren
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a
              href="#features"
              className="text-xs font-medium transition-colors duration-200 ease-out hover:text-[var(--text-primary)]"
              style={{ color: "var(--text-tertiary)" }}
            >
              Features
            </a>
            <a
              href="#how-it-works"
              className="text-xs font-medium transition-colors duration-200 ease-out hover:text-[var(--text-primary)]"
              style={{ color: "var(--text-tertiary)" }}
            >
              How It Works
            </a>
            <a
              href="https://github.com/Daniel-debug-boop/Wren"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-medium transition-colors duration-200 ease-out hover:text-[var(--text-primary)]"
              style={{ color: "var(--text-tertiary)" }}
            >
              GitHub
            </a>
          </div>

          <Link
            to="/workspace"
            className="btn-primary !px-4"
            style={{ height: 34, fontSize: 12 }}
          >
            Open Workspace
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="mx-auto flex min-h-[70vh] max-w-6xl items-center px-6 pt-28 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center w-full">
          <div className="animate-fade-up">
            <div className="section-tag mb-6">
              <span
                className="h-1.5 w-1.5 rounded-full animate-pulse-dot"
                style={{ background: "var(--accent)" }}
              />
              Open Source AI Engineering
            </div>
            <h1
              className="font-display text-[clamp(2.6rem,5vw,4.2rem)] font-semibold leading-[1.06] tracking-[-0.02em]"
              style={{ color: "var(--text-primary)" }}
            >
              Ship production code
              <br />
              <em className="gradient-text not-italic font-display italic">
                from a conversation
              </em>
            </h1>
            <p
              className="mt-6 text-[15px] max-w-md leading-relaxed"
              style={{ color: "var(--text-secondary)" }}
            >
              Wren is a self-hosted AI engineering platform. Describe what you
              want, and the AI pipeline architects, plans, writes, and reviews
              the code. Connect your own LLM. Keep your data private.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link to="/workspace" className="btn-primary">
                Open Workspace
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </Link>
              <a
                href="https://github.com/Daniel-debug-boop/Wren"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                View on GitHub
              </a>
            </div>

            <div
              className="mt-12 flex divide-x"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="pr-8">
                <div
                  className="font-display text-xl font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  4
                </div>
                <div
                  className="mt-0.5 text-xs"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  Pipeline stages
                </div>
              </div>
              <div className="px-8" style={{ borderColor: "var(--border)" }}>
                <div
                  className="font-display text-xl font-semibold"
                  style={{ color: "var(--text-primary)" }}
                >
                  16+
                </div>
                <div
                  className="mt-0.5 text-xs"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  Languages
                </div>
              </div>
              <div className="pl-8" style={{ borderColor: "var(--border)" }}>
                <div
                  className="font-display text-xl font-semibold"
                  style={{ color: "var(--accent-strong)" }}
                >
                  100%
                </div>
                <div
                  className="mt-0.5 text-xs"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  Self-hosted
                </div>
              </div>
            </div>
          </div>

          {/* Right: Product Mockup */}
          <div
            className="hidden lg:block animate-fade-in"
            style={{ animationDelay: "120ms" }}
          >
            <div className="mockup-frame">
              <div className="mockup-header">
                <div className="mockup-dot" style={{ background: "#FF5F56" }} />
                <div className="mockup-dot" style={{ background: "#FFBD2E" }} />
                <div className="mockup-dot" style={{ background: "#27C93F" }} />
                <span
                  className="ml-2 font-mono text-[10px]"
                  style={{ color: "var(--text-muted)" }}
                >
                  wren -- workspace
                </span>
                <span
                  className="ml-auto flex items-center gap-1.5 text-[10px] font-medium"
                  style={{ color: "var(--accent-strong)" }}
                >
                  <span
                    className="animate-pulse-dot h-1.5 w-1.5 rounded-full"
                    style={{ background: "var(--accent)" }}
                  />
                  Ready
                </span>
              </div>
              <div className="mockup-body">
                <div className="mockup-sidebar">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div
                      key={i}
                      className="mockup-sidebar-item"
                      style={{ width: `${85 - i * 9}%` }}
                    />
                  ))}
                </div>
                <div className="mockup-editor">
                  <div className="mockup-line mockup-line-highlight">
                    // app.py
                  </div>
                  <div className="mockup-line" style={{ marginTop: 8 }}>
                    &nbsp;
                  </div>
                  <div className="mockup-line">
                    <span style={{ color: "#8250DF" }}>from</span>{" "}
                    <span style={{ color: "#0550AE" }}>fastapi</span>{" "}
                    <span style={{ color: "#8250DF" }}>import</span>{" "}
                    <span style={{ color: "#1A7F37" }}>FastAPI</span>
                  </div>
                  <div className="mockup-line">
                    <span style={{ color: "var(--accent-strong)" }}>app</span> ={" "}
                    <span style={{ color: "#1A7F37" }}>FastAPI</span>()
                  </div>
                  <div className="mockup-line" style={{ marginTop: 8 }}>
                    &nbsp;
                  </div>
                  <div className="mockup-line">
                    <span style={{ color: "#9A6700" }}>@app.get</span>
                    <span style={{ color: "var(--text-secondary)" }}>(</span>
                    <span style={{ color: "#1A7F37" }}>"/"</span>
                    <span style={{ color: "var(--text-secondary)" }}>)</span>
                  </div>
                  <div className="mockup-line">
                    <span style={{ color: "#8250DF" }}>async def</span>{" "}
                    <span style={{ color: "#0550AE" }}>root</span>():
                  </div>
                  <div className="mockup-line">
                    &nbsp;&nbsp;<span style={{ color: "#8250DF" }}>return</span>{" "}
                    {"{"}
                    <span style={{ color: "#1A7F37" }}>message</span>:{" "}
                    <span style={{ color: "#1A7F37" }}>"Hello, World!"</span>
                    {"}"}
                  </div>
                </div>
                <div className="mockup-panel">
                  <div className="mockup-panel-item" style={{ width: "60%" }} />
                  <div className="mockup-panel-item" style={{ width: "80%" }} />
                  <div className="mockup-panel-item" style={{ width: "45%" }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="divider-glow" />

      {/* ── Features Bento Grid ── */}
      <section
        id="features"
        className="mx-auto max-w-6xl scroll-mt-20 px-6 py-20"
      >
        <div className="mb-12 text-center">
          <h2
            className="font-display text-2xl font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            What you can do
          </h2>
          <p
            className="mx-auto mt-2 max-w-lg text-sm leading-relaxed"
            style={{ color: "var(--text-tertiary)" }}
          >
            Everything you need to go from idea to running code, in a single
            self-hosted platform.
          </p>
        </div>

        <div className="bento-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="bento-card">
              <div className="mb-4 flex items-start justify-between">
                <span
                  className="flex h-9 w-9 items-center justify-center rounded-lg"
                  style={{
                    background: "var(--accent-subtle)",
                    color: "var(--accent-strong)",
                  }}
                >
                  {f.icon}
                </span>
                <span
                  className="rounded-full px-2 py-0.5 text-[9px] font-medium tracking-wide"
                  style={{
                    background: "var(--bg-surface)",
                    color: "var(--text-tertiary)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {f.tag}
                </span>
              </div>
              <h3
                className="font-display mb-1.5 text-[15px] font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {f.title}
              </h3>
              <p
                className="text-[13px] leading-relaxed"
                style={{ color: "var(--text-secondary)" }}
              >
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="divider-glow" />

      {/* ── How It Works ── */}
      <section
        id="how-it-works"
        className="mx-auto max-w-6xl scroll-mt-20 px-6 py-20"
      >
        <div className="mb-14 text-center">
          <h2
            className="font-display text-2xl font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            How it works
          </h2>
        </div>

        <div className="relative grid grid-cols-1 gap-10 sm:grid-cols-2 md:grid-cols-4 md:gap-4">
          <div
            className="absolute left-0 right-0 top-5 hidden h-px md:block"
            style={{
              background:
                "linear-gradient(90deg, transparent, var(--border-strong), var(--border-strong), transparent)",
            }}
          />
          {[
            {
              step: "1",
              title: "Describe",
              desc: "Tell Wren what you want to build in plain English",
            },
            {
              step: "2",
              title: "Architect",
              desc: "AI designs the system architecture and component layout",
            },
            {
              step: "3",
              title: "Generate",
              desc: "Code is written, reviewed, and saved as real files",
            },
            {
              step: "4",
              title: "Run",
              desc: "Execute your project in the built-in terminal and editor",
            },
          ].map((s) => (
            <div key={s.step} className="relative text-center">
              <div
                className="font-display relative z-10 mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full border text-sm font-bold shadow-sm"
                style={{
                  background: "var(--bg-card)",
                  borderColor: "rgba(217,119,87,0.35)",
                  color: "var(--accent-strong)",
                }}
              >
                {s.step}
              </div>
              <h3
                className="font-display mb-1.5 text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {s.title}
              </h3>
              <p
                className="mx-auto max-w-[220px] text-xs leading-relaxed"
                style={{ color: "var(--text-tertiary)" }}
              >
                {s.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      <div className="divider-glow" />

      {/* ── Tech Stack ── */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12 text-center">
          <h2
            className="font-display text-2xl font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            Built with
          </h2>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { name: "React 19", role: "Frontend" },
            { name: "FastAPI", role: "Backend" },
            { name: "xterm.js", role: "Terminal" },
            { name: "Monaco", role: "Editor" },
          ].map((t) => (
            <div key={t.name} className="bento-card py-7 text-center">
              <div
                className="font-display text-sm font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {t.name}
              </div>
              <div
                className="mt-1 text-[10px] uppercase tracking-[0.08em]"
                style={{ color: "var(--text-muted)" }}
              >
                {t.role}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer
        className="border-t py-8"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div
              className="flex h-5 w-5 items-center justify-center rounded text-[8px] font-bold"
              style={{ background: "var(--accent)", color: "#fffaf7" }}
            >
              W
            </div>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Wren — MIT License
            </span>
          </div>
          <a
            href="https://github.com/Daniel-debug-boop/Wren"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs transition-colors duration-200 ease-out hover:text-[var(--text-primary)]"
            style={{ color: "var(--text-muted)" }}
          >
            GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
