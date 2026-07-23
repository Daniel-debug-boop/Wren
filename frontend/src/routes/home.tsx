import { useCallback, useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { motion, useScroll, useTransform, useReducedMotion } from "motion/react";

type LaunchTarget = "header" | "cta" | null;

/* ── Configuration ──────────────────────────────────────────── */
const WREN_REPO = "https://github.com/Daniel-debug-boop/Wren";

/* ── Animation Variants ─────────────────────────────────────── */
const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 32, filter: "blur(4px)" },
  visible: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1] },
  },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] },
  },
};

/* ── Data ───────────────────────────────────────────────────── */
const CAPABILITIES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2a10 10 0 0 1 10 10c0 2.5-1 4.7-2.5 6.3L12 12V2z" />
        <path d="M12 12l6.3 6.3A10 10 0 1 1 12 2z" />
      </svg>
    ),
    title: "Architect → Plan → Write → Review",
    desc: "Four specialized AI agents work in sequence: Architect designs the system, Planner creates the blueprint, Writer generates code, Reviewer catches bugs.",
    accent: "#E86C4A",
    stat: "4-stage pipeline",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
    title: "Smart Model Routing",
    desc: "OmniRoute automatically selects the best LLM for each task — coding vs architecture vs review. With automatic failover, cost tracking, and compression.",
    accent: "#6366F1",
    stat: "Auto failover",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
      </svg>
    ),
    title: "Zero External Dependencies",
    desc: "The generation engine uses ONLY Python stdlib — no pip install, no npm, no heavy frameworks. Runs anywhere Python 3.12+ runs.",
    accent: "#22C55E",
    stat: "Pure stdlib",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
    title: "3D & WebGL Expertise",
    desc: "Deep knowledge of Three.js, React-Three-Fiber, WebGL context management, GPU memory lifecycle, shaders, and physics. Unmatched by any other coding tool.",
    accent: "#F59E0B",
    stat: "GPU-aware",
  },
];

const GENERATION_FLOW = [
  { step: 1, label: "Architect", desc: "Designs full system — components, data models, routes, stack, auth strategy" },
  { step: 2, label: "Planner", desc: "Produces step-by-step implementation plan with dependency ordering and risk assessment" },
  { step: 3, label: "Writer", desc: "Generates complete, production-grade code with context awareness and symbol tracking" },
  { step: 4, label: "Reviewer", desc: "Audits code for bugs, security issues, GPU leaks, placeholders. Quality scoring 0-100" },
];

const PROJECT_TYPES = [
  { label: "3D Web", icon: "◈", color: "#6366F1" },
  { label: "Game", icon: "◆", color: "#22C55E" },
  { label: "API", icon: "▣", color: "#F59E0B" },
  { label: "Mobile", icon: "◎", color: "#E86C4A" },
  { label: "CLI", icon: "▸", color: "#A78BFA" },
  { label: "Desktop", icon: "▢", color: "#38BDF8" },
  { label: "Fullstack", icon: "⬡", color: "#34D399" },
  { label: "Portfolio", icon: "✦", color: "#F472B6" },
];

/* ── Floating Particles Background ──────────────────────────── */
function ParticlesBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let particles: Array<{ x: number; y: number; vx: number; vy: number; size: number; alpha: number }> = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    // Create particles
    for (let i = 0; i < 60; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2 + 0.5,
        alpha: Math.random() * 0.3 + 0.1,
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(232, 108, 74, ${p.alpha})`;
        ctx.fill();

        // Draw connections
        particles.slice(i + 1).forEach((p2) => {
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(232, 108, 74, ${0.05 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        });
      });

      animationId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
    };
  }, [reduce]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden="true"
    />
  );
}

/* ── Floating Navigation ────────────────────────────────────── */
function FloatingNav({ onLaunch }: { onLaunch: () => void }) {
  const { scrollY } = useScroll();
  const navBg = useTransform(
    scrollY,
    [0, 200],
    ["rgba(7, 7, 8, 0)", "rgba(7, 7, 8, 0.85)"]
  );

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-[var(--z-nav)] border-b border-transparent transition-[border-color] duration-500"
      style={{
        background: navBg,
        backdropFilter: "blur(24px) saturate(180%)",
        WebkitBackdropFilter: "blur(24px) saturate(180%)",
      }}
    >
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)] text-white text-xs font-bold transition-transform duration-500 group-hover:scale-110" style={{ transitionTimingFunction: "var(--ease-smooth)" }}>
            W
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>
            Wren
          </span>
        </a>

        {/* Center links */}
        <div className="hidden md:flex items-center gap-8">
          {["Features", "Pipeline", "CLI", "GitHub"].map((item) => (
            <a
              key={item}
              href={
                item === "GitHub"
                  ? WREN_REPO
                  : `#${item.toLowerCase()}`
              }
              className="text-sm transition-colors duration-300"
              style={{ color: "var(--text-tertiary)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
            >
              {item}
            </a>
          ))}
        </div>

        {/* CTA */}
        <button
          type="button"
          onClick={onLaunch}
          className="accent-button h-9 px-5 text-xs"
        >
          <span>Launch Wren</span>
          <span className="icon-ring w-5 h-5">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </span>
        </button>
      </div>
    </motion.nav>
  );
}

/* ── Marquee ────────────────────────────────────────────────── */
function TechMarquee() {
  const items = [
    "Python 3.12+", "TypeScript", "React 19", "Three.js", "WebGL 2.0",
    "Tailwind v4", "Vite 8", "FastAPI", "PostgreSQL", "Docker",
    "GitHub Actions", "Kotlin", "OpenAI", "Anthropic", "OpenRouter",
  ];

  return (
    <div className="relative overflow-hidden py-6" style={{ background: "var(--bg-surface)" }}>
      <div className="flex animate-marquee gap-16 whitespace-nowrap" style={{ animationDuration: "40s" }}>
        {[...items, ...items].map((item, i) => (
          <span
            key={i}
            className="text-xs font-medium uppercase tracking-[0.15em]"
            style={{ color: "var(--text-tertiary)" }}
          >
            {item}
          </span>
        ))}
      </div>
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 40s linear infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .animate-marquee { animation: none; }
        }
      `}</style>
    </div>
  );
}

/* ── Main Landing Page ──────────────────────────────────────── */
export default function HomeScreen() {
  const navigate = useNavigate();
  const reduce = useReducedMotion();
  const [isLaunching, setIsLaunching] = useState(false);

  const handleLaunch = useCallback(() => {
    if (isLaunching) return;
    setIsLaunching(true);
    setTimeout(() => navigate("/generation"), 400);
  }, [navigate, isLaunching]);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={container}
      className="relative min-h-screen noise-overlay"
      style={{ background: "var(--bg-deep)" }}
    >
      {/* ── Ambient Background ── */}
      <ParticlesBg />

      {/* ── Aurora Orbs ── */}
      <div
        className="aurora-glow -top-40 -left-40 h-[500px] w-[500px]"
        style={{
          background: "radial-gradient(circle, rgba(232,108,74,0.08), transparent 70%)",
        }}
        aria-hidden="true"
      />
      <div
        className="aurora-glow -bottom-40 -right-40 h-[600px] w-[600px]"
        style={{
          background: "radial-gradient(circle, rgba(99,102,241,0.06), transparent 70%)",
        }}
        aria-hidden="true"
      />

      {/* ── Navigation ── */}
      <FloatingNav onLaunch={handleLaunch} />

      {/* ════════════════════════════════════════════════════════════
          HERO SECTION — Double-Bezel Glass Shell
          ════════════════════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pt-32 md:pt-40 pb-16">
        <motion.div variants={fadeUp} className="flex justify-center mb-8">
          <span
            className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-[10px] font-medium uppercase tracking-[0.22em]"
            style={{
              background: "var(--accent-subtle)",
              border: "1px solid var(--border-accent)",
              color: "var(--accent)",
            }}
          >
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse-glow" />
            v1.0.0 — Open Source AI Engineering Platform
          </span>
        </motion.div>

        {/* Outer Glass Shell */}
        <div className="glass-shell-outer">
          <div className="glass-shell-inner p-8 md:p-16 lg:p-20">
            {/* Eyebrow */}
            <motion.div variants={fadeUp} className="mb-6">
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
            </motion.div>

            {/* Headline */}
            <motion.h1
              variants={fadeUp}
              className="text-[clamp(2.5rem,6vw,4.5rem)] font-semibold tracking-tight leading-[1.05] max-w-4xl"
              style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}
            >
              Generate complete apps with a{" "}
              <span
                className="bg-clip-text text-transparent"
                style={{
                  backgroundImage: "linear-gradient(135deg, var(--accent), #F59E0B, #6366F1)",
                  backgroundSize: "200% auto",
                }}
              >
                4-agent AI pipeline
              </span>
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="mt-6 max-w-2xl text-lg leading-relaxed"
              style={{ color: "var(--text-secondary)" }}
            >
              Wren uses a revolutionary multi-agent architecture — Architect, Planner, Writer, 
              and Reviewer — to build complete, production-grade apps from a single prompt. 
              From 3D websites to full-stack APIs, it generates zero-placeholder code.
            </motion.p>

            {/* CTA Row */}
            <motion.div variants={fadeUp} className="mt-10 flex flex-wrap items-center gap-4">
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
                href={WREN_REPO}
                target="_blank"
                rel="noopener noreferrer"
                className="ghost-button"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                <span>View on GitHub</span>
              </a>
            </motion.div>

            {/* Stats row */}
            <motion.div variants={fadeUp} className="mt-12 flex flex-wrap gap-8 md:gap-12">
              {[
                { value: "4", label: "AI Agents" },
                { value: "130K+", label: "Lines of Code" },
                { value: "25", label: "Backend Modules" },
                { value: "0", label: "External Deps", accent: true },
              ].map((stat) => (
                <div key={stat.label}>
                  <span
                    className="text-2xl font-bold"
                    style={{
                      color: stat.accent ? "var(--accent)" : "var(--text-primary)",
                    }}
                  >
                    {stat.value}
                  </span>
                  <span className="block text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
                    {stat.label}
                  </span>
                </div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
          CAPABILITIES — Asymmetrical Bento Grid
          ════════════════════════════════════════════════════════════ */}
      <section id="features" className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <motion.div variants={fadeUp} className="mb-16">
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
            style={{ color: "var(--text-primary)" }}
          >
            What makes Wren different
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-6 gap-3">
          {CAPABILITIES.map((cap, i) => (
            <motion.div
              key={cap.title}
              variants={scaleIn}
              className={`premium-card p-6 md:p-8 ${
                i === 0 ? "md:col-span-3 md:row-span-1" :
                i === 1 ? "md:col-span-3 md:row-span-1" :
                i === 2 ? "md:col-span-2 md:row-span-1" :
                "md:col-span-4 md:row-span-1"
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
                  {cap.icon}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-base font-semibold" style={{ color: "var(--text-primary)" }}>
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
                  <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                    {cap.desc}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
          PIPELINE — The 4-Agent Flow
          ════════════════════════════════════════════════════════════ */}
      <section id="pipeline" className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <motion.div variants={fadeUp} className="mb-16">
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
          <h2
            className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]"
            style={{ color: "var(--text-primary)" }}
          >
            Four agents, one pipeline
          </h2>
          <p className="mt-4 max-w-xl text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            Each stage feeds into the next. The result: production-grade code that&apos;s been
            designed, planned, written, and reviewed before you even see it.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {GENERATION_FLOW.map((step, i) => (
            <motion.div
              key={step.label}
              variants={scaleIn}
              className="premium-card p-6 relative overflow-hidden"
            >
              {/* Step number */}
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
                  <div className="hidden md:block flex-1 h-px" style={{ background: "var(--border-default)" }} />
                )}
              </div>

              <h3 className="text-base font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
                {step.label}
              </h3>
              <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                {step.desc}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Pipeline visualization */}
        <motion.div variants={scaleIn} className="mt-12 glass-pane p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-[var(--success)]" />
            <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
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
                <div
                  className={`step-dot ${step.active ? "active" : ""} ${step.done ? "done" : ""}`}
                />
                <span
                  className="text-xs whitespace-nowrap"
                  style={{
                    color: step.active ? "var(--text-primary)" : "var(--text-tertiary)",
                  }}
                >
                  {step.label}
                </span>
                {i < 5 && (
                  <div className="w-6 h-px" style={{ background: "var(--border-default)" }} />
                )}
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ════════════════════════════════════════════════════════════
          PROJECT TYPES
          ════════════════════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <motion.div variants={fadeUp} className="mb-12 text-center">
          <h2
            className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]"
            style={{ color: "var(--text-primary)" }}
          >
            Build any type of project
          </h2>
          <p className="mt-4 text-sm" style={{ color: "var(--text-secondary)" }}>
            From 3D scenes to production APIs — the pipeline adapts
          </p>
        </motion.div>

        <div className="flex flex-wrap justify-center gap-3">
          {PROJECT_TYPES.map((type) => (
            <motion.div
              key={type.label}
              variants={scaleIn}
              className="premium-card px-5 py-3 flex items-center gap-3 cursor-default"
            >
              <span style={{ color: type.color, fontSize: "16px" }}>{type.icon}</span>
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                {type.label}
              </span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
          CLI SECTION
          ════════════════════════════════════════════════════════════ */}
      <section id="cli" className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="glass-shell-outer">
          <div className="glass-shell-inner p-8 md:p-12">
            <motion.div variants={fadeUp} className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
              <div className="max-w-xl">
                <h2
                  className="text-2xl md:text-4xl font-semibold tracking-tight leading-[1.15]"
                  style={{ color: "var(--text-primary)" }}
                >
                  One command to build anything
                </h2>
                <p className="mt-4 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                  Zero dependencies. Pure Python stdlib. Works with any OpenAI-compatible API.
                </p>
              </div>

              <button
                type="button"
                onClick={handleLaunch}
                disabled={isLaunching}
                className="accent-button shrink-0"
              >
                <span>{isLaunching ? "Starting..." : "Try it now"}</span>
                <span className="icon-ring">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              </button>
            </motion.div>

            {/* Code block */}
            <motion.div variants={fadeUp} className="mt-8">
              <div className="code-block">
                <div className="flex items-center gap-2 mb-3 pb-3 border-b" style={{ borderColor: "var(--border-subtle)" }}>
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
                    <div className="w-2.5 h-2.5 rounded-full bg-[#22C55E]" />
                  </div>
                  <span className="text-xs ml-2" style={{ color: "var(--text-tertiary)" }}>terminal</span>
                </div>
                <pre className="text-xs leading-relaxed">
                  <span style={{ color: "var(--accent)" }}>$</span>{" "}
                  <span style={{ color: "var(--text-primary)" }}>python run_app_builder.py \</span>
                  {"\n"}  <span style={{ color: "var(--text-secondary)" }}>--prompt</span>{" "}
                  <span style={{ color: "#22C55E" }}>"Build a 3D solar system explorer"</span>{" "}
                  {"\n"}  <span style={{ color: "var(--text-secondary)" }}>--api-key</span>{" "}
                  <span style={{ color: "#6366F1" }}>"sk-..."</span>{" "}
                  {"\n"}  <span style={{ color: "var(--text-secondary)" }}>--output</span>{" "}
                  <span style={{ color: "var(--text-tertiary)" }}>./my-project</span>
                  {"\n\n"}
                  <span style={{ color: "var(--text-tertiary)" }}># Wren generates a complete project with:</span>
                  {"\n"}
                  <span style={{ color: "var(--text-tertiary)" }}># • package.json, tsconfig.json, vite.config.ts</span>
                  {"\n"}
                  <span style={{ color: "var(--text-tertiary)" }}># • Three.js scene with orbit controls, lighting, shadows</span>
                  {"\n"}
                  <span style={{ color: "var(--text-tertiary)" }}># • Planet data, animation loop, WebGL context handling</span>
                  {"\n"}
                  <span style={{ color: "var(--text-tertiary)" }}># • Dockerfile, README.md, .env.example</span>
                </pre>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════════
          CTA SECTION
          ════════════════════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-32 text-center">
        <motion.div variants={fadeUp}>
          <h2
            className="text-3xl md:text-5xl font-semibold tracking-tight leading-[1.1]"
            style={{ color: "var(--text-primary)" }}
          >
            Ready to build something
            <br />
            <span
              className="bg-clip-text text-transparent"
              style={{
                backgroundImage: "linear-gradient(135deg, var(--accent), #F59E0B)",
              }}
            >
              extraordinary?
            </span>
          </h2>
          <p className="mt-6 text-sm max-w-md mx-auto" style={{ color: "var(--text-secondary)" }}>
            Open source, zero dependencies, multi-agent pipeline.
            Generate production-grade apps from a single prompt.
          </p>

          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <button
              type="button"
              onClick={handleLaunch}
              disabled={isLaunching}
              className="accent-button"
            >
              <span>{isLaunching ? "Starting..." : "Start Building Free"}</span>
              <span className="icon-ring">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </span>
            </button>

            <a
              href={WREN_REPO}
              target="_blank"
              rel="noopener noreferrer"
              className="ghost-button"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
              <span>Star on GitHub</span>
            </a>
          </div>
        </motion.div>
      </section>

      {/* ── Tech Marquee ── */}
      <TechMarquee />

      {/* ════════════════════════════════════════════════════════════
          FOOTER
          ════════════════════════════════════════════════════════════ */}
      <footer
        className="relative z-10 border-t"
        style={{ borderColor: "var(--border-subtle)", background: "var(--bg-surface)" }}
      >
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-md bg-[var(--accent)] text-white text-[10px] font-bold"
              >
                W
              </div>
              <span className="text-xs font-medium" style={{ color: "var(--text-tertiary)" }}>
                Wren — Open Source AI Engineering Platform
              </span>
            </div>

            <div className="flex items-center gap-6">
              <a
                href={WREN_REPO}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs transition-colors duration-300"
                style={{ color: "var(--text-tertiary)" }}
              >
                GitHub
              </a>
              <span className="text-xs" style={{ color: "var(--border-strong)" }}>/</span>
              <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Built with ❤️ by the Wren team
              </span>
            </div>
          </div>
        </div>
      </footer>
    </motion.div>
  );
}
