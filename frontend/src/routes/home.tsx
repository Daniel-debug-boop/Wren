import { useCallback, useState } from "react";
import { useNavigate } from "react-router";

/* ── Data ───────────────────────────────────────────────────── */
const CAPABILITIES = [
  {
    title: "Architect → Plan → Write → Review",
    desc: "Four specialized AI agents work in sequence: Architect designs the system, Planner creates the blueprint, Writer generates code, Reviewer catches bugs.",
    accent: "#E86C4A",
    stat: "4-stage pipeline",
  },
  {
    title: "Smart Model Routing",
    desc: "OmniRoute automatically selects the best LLM for each task — coding vs architecture vs review. With automatic failover and cost tracking.",
    accent: "#6366F1",
    stat: "Auto failover",
  },
  {
    title: "Zero External Dependencies",
    desc: "The generation engine uses ONLY Python stdlib — no pip install, no npm, no heavy frameworks. Runs anywhere Python 3.12+ runs.",
    accent: "#22C55E",
    stat: "Pure stdlib",
  },
  {
    title: "3D & WebGL Expertise",
    desc: "Deep knowledge of Three.js, React-Three-Fiber, WebGL context management, GPU memory lifecycle, shaders, and physics.",
    accent: "#F59E0B",
    stat: "GPU-aware",
  },
];

const GENERATION_FLOW = [
  { step: 1, label: "Architect", desc: "Designs full system — components, data models, routes, stack, auth strategy" },
  { step: 2, label: "Planner", desc: "Produces step-by-step implementation plan with dependency ordering" },
  { step: 3, label: "Writer", desc: "Generates complete, production-grade code with context awareness" },
  { step: 4, label: "Reviewer", desc: "Audits code for bugs, security issues, and quality scoring 0-100" },
];

const PROJECT_TYPES = [
  { label: "3D Web", color: "#6366F1" },
  { label: "Game", color: "#22C55E" },
  { label: "API", color: "#F59E0B" },
  { label: "Mobile", color: "#E86C4A" },
  { label: "CLI", color: "#A78BFA" },
  { label: "Desktop", color: "#38BDF8" },
  { label: "Fullstack", color: "#34D399" },
  { label: "Portfolio", color: "#F472B6" },
];

/* ── Floating Particles Background ── */
function ParticlesBg() {
  return (
    <canvas
      id="particles-canvas"
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden="true"
    />
  );
}

/* ── Floating Navigation ── */
function FloatingNav({ onLaunch }: { onLaunch: () => void }) {
  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(24px) saturate(180%)",
        WebkitBackdropFilter: "blur(24px) saturate(180%)",
        borderBottom: "1px solid var(--color-border-muted)",
      }}
    >
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <a href="/" className="flex items-center gap-2.5 group">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-md text-white text-xs font-bold transition-transform group-hover:scale-110"
            style={{ background: "var(--accent)" }}
          >
            W
          </div>
          <span
            className="text-sm font-semibold tracking-tight"
            style={{ color: "var(--color-text-primary)" }}
          >
            Wren
          </span>
        </a>

        <div className="hidden md:flex items-center gap-8">
          {["Features", "Pipeline", "GitHub"].map((item) => (
            <a
              key={item}
              href={
                item === "GitHub"
                  ? "https://github.com/Daniel-debug-boop/Wren"
                  : `#${item.toLowerCase()}`
              }
              className="text-sm transition-colors"
              style={{ color: "var(--color-text-tertiary)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--color-text-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--color-text-tertiary)")}
            >
              {item}
            </a>
          ))}
        </div>

        <button type="button" onClick={onLaunch} className="accent-button h-9 px-5 text-xs">
          <span>Launch Wren</span>
          <span className="icon-ring w-5 h-5">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </span>
        </button>
      </div>
    </nav>
  );
}

/* ── Tech Marquee ── */
function TechMarquee() {
  const items = [
    "Python 3.12+", "TypeScript", "React 19", "Three.js", "WebGL 2.0",
    "Tailwind v4", "Vite 8", "FastAPI", "PostgreSQL", "Docker",
    "OpenAI", "Anthropic", "OpenRouter",
  ];

  return (
    <div className="relative overflow-hidden py-6" style={{ background: "var(--color-surface-raised)" }}>
      <div className="flex animate-marquee gap-16 whitespace-nowrap" style={{ animationDuration: "40s" }}>
        {[...items, ...items].map((item, i) => (
          <span key={i} className="text-xs font-medium uppercase tracking-[0.15em]" style={{ color: "var(--color-text-tertiary)" }}>
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── Main Landing Page ── */
export default function HomeScreen() {
  const navigate = useNavigate();
  const [isLaunching, setIsLaunching] = useState(false);

  const handleLaunch = useCallback(() => {
    if (isLaunching) return;
    setIsLaunching(true);
    setTimeout(() => navigate("/generation"), 400);
  }, [navigate, isLaunching]);

  const handleScroll = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, []);

  return (
    <div className="relative min-h-screen" style={{ background: "var(--color-surface-base)" }}>
      {/* Ambient Background */}
      <ParticlesBg />

      {/* Aurora Orbs */}
      <div className="aurora-glow -top-40 -left-40 h-[500px] w-[500px]"
        style={{ background: "radial-gradient(circle, rgba(232,108,74,0.08), transparent 70%)" }}
        aria-hidden="true"
      />
      <div className="aurora-glow -bottom-40 -right-40 h-[600px] w-[600px]"
        style={{ background: "radial-gradient(circle, rgba(99,102,241,0.06), transparent 70%)" }}
        aria-hidden="true"
      />

      {/* Navigation */}
      <FloatingNav onLaunch={handleLaunch} />

      {/* ════════════════════════════════════════════
          HERO
          ════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pt-32 md:pt-40 pb-16">
        <div className="flex justify-center mb-8">
          <span
            className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-[10px] font-medium uppercase tracking-[0.22em]"
            style={{
              background: "color-mix(in srgb, var(--accent) 10%, transparent)",
              border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
              color: "var(--accent)",
            }}
          >
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse-glow" />
            Open Source AI Engineering Platform
          </span>
        </div>

        <div className="glass-shell-outer">
          <div className="glass-shell-inner p-8 md:p-16 lg:p-20">
            <div className="mb-6">
              <span
                className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-[0.22em]"
                style={{
                  background: "color-mix(in srgb, var(--accent) 10%, transparent)",
                  border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
                  color: "var(--accent)",
                }}
              >
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse-glow" />
                Multi-Agent Generation Engine
              </span>
            </div>

            <h1
              className="text-[clamp(2.5rem,6vw,4.5rem)] font-semibold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: "var(--color-text-primary)", letterSpacing: "-0.03em" }}
            >
              Build with an AI engineer that{" "}
              <span
                className="bg-clip-text text-transparent"
                style={{
                  backgroundImage: "linear-gradient(135deg, var(--accent), #F59E0B, #6366F1)",
                  backgroundSize: "200% auto",
                }}
              >
                runs code
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
              Wren spins up real sandboxes, connects to your repos, and writes production-ready code
              using a revolutionary multi-agent architecture — from a single conversation.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={handleLaunch}
                disabled={isLaunching}
                className="accent-button"
              >
                <span>{isLaunching ? "Starting..." : "Start Building"}</span>
                <span className="icon-ring">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              </button>

              <a
                href="https://github.com/Daniel-debug-boop/Wren"
                target="_blank"
                rel="noopener noreferrer"
                className="ghost-button"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                <span>View on GitHub</span>
              </a>
            </div>

            {/* Stats */}
            <div className="mt-12 flex flex-wrap gap-8 md:gap-12">
              {[
                { value: "4", label: "AI Agents" },
                { value: "130K+", label: "Lines of Code" },
                { value: "25", label: "Backend Modules" },
                { value: "0", label: "External Deps", accent: true },
              ].map((stat) => (
                <div key={stat.label}>
                  <span
                    className="text-2xl font-bold"
                    style={{ color: stat.accent ? "var(--accent)" : "var(--color-text-primary)" }}
                  >
                    {stat.value}
                  </span>
                  <span className="block text-xs mt-1" style={{ color: "var(--color-text-tertiary)" }}>
                    {stat.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          CAPABILITIES
          ════════════════════════════════════════════ */}
      <section id="features" className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16">
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-[0.22em] mb-4"
            style={{
              background: "color-mix(in srgb, var(--accent) 10%, transparent)",
              border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
              color: "var(--accent)",
            }}
          >
            Capabilities
          </span>
          <h2
            className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]"
            style={{ color: "var(--color-text-primary)" }}
          >
            What makes Wren different
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
          {CAPABILITIES.map((cap, i) => (
            <div
              key={cap.title}
              className={`premium-card p-6 md:p-8 ${
                i === 0 ? "md:col-span-3" :
                i === 1 ? "md:col-span-3" :
                i === 2 ? "md:col-span-2" :
                "md:col-span-4"
              }`}
            >
              <div className="flex items-start gap-4">
                <div
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl"
                  style={{
                    background: `${cap.accent}12`,
                    border: `1px solid ${cap.accent}20`,
                    color: cap.accent,
                  }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2a10 10 0 0 1 10 10c0 2.5-1 4.7-2.5 6.3L12 12V2z" />
                    <path d="M12 12l6.3 6.3A10 10 0 1 1 12 2z" />
                  </svg>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-base font-semibold" style={{ color: "var(--color-text-primary)" }}>
                      {cap.title}
                    </h3>
                    <span
                      className="text-[10px] font-medium uppercase tracking-[0.12em] px-2 py-0.5 rounded-full shrink-0"
                      style={{
                        background: `${cap.accent}10`,
                        color: cap.accent,
                        border: `1px solid ${cap.accent}15`,
                      }}
                    >
                      {cap.stat}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                    {cap.desc}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ════════════════════════════════════════════
          PIPELINE
          ════════════════════════════════════════════ */}
      <section id="pipeline" className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16">
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-[0.22em] mb-4"
            style={{
              background: "color-mix(in srgb, var(--accent) 10%, transparent)",
              border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
              color: "var(--accent)",
            }}
          >
            Pipeline
          </span>
          <h2 className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]" style={{ color: "var(--color-text-primary)" }}>
            Four agents, one pipeline
          </h2>
          <p className="mt-4 max-w-xl text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
            Each stage feeds into the next. The result: production-grade code that&apos;s been
            designed, planned, written, and reviewed before you even see it.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {GENERATION_FLOW.map((step, i) => (
            <div key={step.label} className="premium-card p-6 relative overflow-hidden">
              <div className="flex items-center gap-3 mb-4">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold"
                  style={{
                    background: "var(--accent-subtle)",
                    border: "1px solid var(--border-accent)",
                    color: "var(--accent)",
                  }}
                >
                  {step.step}
                </div>
                {i < GENERATION_FLOW.length - 1 && (
                  <div className="hidden md:block flex-1 h-px" style={{ background: "var(--border)" }} />
                )}
              </div>
              <h3 className="text-base font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
                {step.label}
              </h3>
              <p className="text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                {step.desc}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-12 glass-pane p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full" style={{ background: "var(--success)" }} />
            <span className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
              Pipeline Status
            </span>
          </div>
          <div className="flex items-center gap-3 md:gap-6 overflow-x-auto pb-2">
            {[
              { label: "User Prompt", active: true, done: false },
              { label: "Architect", active: true, done: false },
              { label: "Planner", active: false, done: false },
              { label: "Writer", active: false, done: false },
              { label: "Reviewer", active: false, done: false },
              { label: "Complete Project", active: false, done: false },
            ].map((step, i) => (
              <div key={step.label} className="flex items-center gap-3 shrink-0">
                <div className={`step-dot ${step.active ? "active" : ""} ${step.done ? "done" : ""}`} />
                <span className="text-xs whitespace-nowrap" style={{
                  color: step.active ? "var(--color-text-primary)" : "var(--color-text-tertiary)",
                }}>
                  {step.label}
                </span>
                {i < 5 && <div className="w-6 h-px" style={{ background: "var(--border)" }} />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          PROJECT TYPES
          ════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="mb-12 text-center">
          <h2 className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]" style={{ color: "var(--color-text-primary)" }}>
            Build any type of project
          </h2>
          <p className="mt-4 text-sm" style={{ color: "var(--color-text-secondary)" }}>
            From 3D scenes to production APIs — the pipeline adapts
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-3">
          {PROJECT_TYPES.map((type) => (
            <div
              key={type.label}
              className="premium-card px-5 py-3 flex items-center gap-3"
            >
              <span style={{ color: type.color, fontSize: "16px" }}>◆</span>
              <span className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                {type.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ════════════════════════════════════════════
          CTA
          ════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-32 text-center">
        <h2 className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]" style={{ color: "var(--color-text-primary)" }}>
          Ready to build something
          <br />
          <span className="bg-clip-text text-transparent"
            style={{ backgroundImage: "linear-gradient(135deg, var(--accent), #F59E0B)" }}
          >
            extraordinary?
          </span>
        </h2>
        <p className="mt-6 text-sm max-w-md mx-auto" style={{ color: "var(--color-text-secondary)" }}>
          Open source, zero dependencies, multi-agent pipeline.
          Generate production-grade apps from a single prompt.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <button type="button" onClick={handleLaunch} disabled={isLaunching} className="accent-button">
            <span>{isLaunching ? "Starting..." : "Start Building Free"}</span>
            <span className="icon-ring">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </span>
          </button>
        </div>
      </section>

      {/* ── Tech Marquee ── */}
      <TechMarquee />

      {/* ════════════════════════════════════════════
          FOOTER
          ════════════════════════════════════════════ */}
      <footer className="relative z-10 border-t" style={{ borderColor: "var(--color-border-muted)", background: "var(--color-surface-raised)" }}>
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-md text-white text-[10px] font-bold"
                style={{ background: "var(--accent)" }}
              >
                W
              </div>
              <span className="text-xs font-medium" style={{ color: "var(--color-text-tertiary)" }}>
                Wren — Open Source AI Engineering Platform
              </span>
            </div>
            <div className="flex items-center gap-6">
              <a href="https://github.com/Daniel-debug-boop/Wren" target="_blank" rel="noopener noreferrer"
                className="text-xs transition-colors" style={{ color: "var(--color-text-tertiary)" }}
              >
                GitHub
              </a>
              <span className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
                Built with ❤️ by the Wren team
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
