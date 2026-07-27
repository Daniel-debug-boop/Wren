import { useCallback, useState } from "react";
import { useNavigate } from "react-router";

/* ── DATA ─────────────────────────────────────────────────── */
const NAV_ITEMS = [
  { label: "Features", href: "#features" },
  { label: "Workspace", href: "#workspace" },
  { label: "Pricing", href: "#pricing" },
];

const BENTO_FEATURES = [
  {
    title: "Autonomous Task Automation",
    desc: "Self-orchestrating agent pipeline that plans, codes, tests, and deploys — all from a single prompt.",
    span: "col-span-2",
    nodes: [
      { label: "Prompt Received", status: "done" },
      { label: "Architect Analysis", status: "done" },
      { label: "Code Generation", status: "active" },
      { label: "Test Suite", status: "pending" },
      { label: "Deployment", status: "pending" },
    ],
    accent: "violet",
  },
  {
    title: "Speed Benchmark",
    desc: "Sub-second inference routing. 4.7x faster than baseline pipeline execution.",
    span: "col-span-1",
    stat: "4.7x",
    statLabel: "Faster Pipeline",
    accent: "teal",
  },
  {
    title: "Multi-Platform Integrations",
    desc: "Seamlessly connects with your entire stack — no configuration headaches.",
    span: "col-span-1",
    platforms: ["GitHub", "Slack", "VSCode", "Docker", "AWS", "Vercel"],
    accent: "violet",
  },
];

const PRICING_TIERS = [
  {
    name: "Starter",
    price: "Free",
    desc: "For individuals exploring AI-powered development.",
    features: ["5 projects/month", "Basic agent pipeline", "Community support", "Public sandboxes"],
    cta: "Get Started",
    featured: false,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    desc: "For professional developers building production apps.",
    features: ["Unlimited projects", "Advanced agent pipeline", "Priority support", "Private sandboxes", "Custom model routing", "Team collaboration"],
    cta: "Upgrade to Pro",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "$99",
    period: "/month",
    desc: "For teams and organizations at scale.",
    features: ["Everything in Pro", "Dedicated agents", "SSO & SAML", "Audit logs", "SLA guarantee", "On-premise option"],
    cta: "Contact Sales",
    featured: false,
  },
];

const FOOTER_LINKS = [
  { label: "Documentation", href: "#" },
  { label: "API Reference", href: "#" },
  { label: "GitHub", href: "https://github.com/Daniel-debug-boop/Wren" },
  { label: "Status", href: "#" },
  { label: "Privacy", href: "#" },
  { label: "Terms", href: "#" },
];

/* ── COMPONENTS ───────────────────────────────────────────── */

function FloatingNav({ onLaunch }: { onLaunch: () => void }) {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50" style={{ background: "rgba(13, 13, 17, 0.85)", backdropFilter: "blur(32px) saturate(200%)", WebkitBackdropFilter: "blur(32px) saturate(200%)", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2.5 group">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-lg text-white text-xs font-bold transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg"
            style={{ background: "linear-gradient(135deg, #8B5CF6, #A78BFA)" }}
          >
            F
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>
            Freebuff
          </span>
          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full" style={{ background: "rgba(139,92,246,0.1)", color: "var(--violet)", border: "1px solid rgba(139,92,246,0.15)" }}>
            Agent
          </span>
        </a>

        {/* Nav Links */}
        <div className="hidden md:flex items-center gap-8">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.label}
              href={item.href}
              className="text-sm transition-all duration-200 relative group"
              style={{ color: "var(--text-tertiary)" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
            >
              {item.label}
              <span
                className="absolute -bottom-1 left-0 w-0 h-px transition-all duration-300 group-hover:w-full"
                style={{ background: "var(--violet)" }}
              />
            </a>
          ))}
        </div>

        {/* CTA */}
        <button type="button" onClick={onLaunch} className="btn-primary" style={{ height: 36, fontSize: 12, padding: "0 20px" }}>
          <span>Deploy Agent Now</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </nav>
  );
}

function Hero3DOrb() {
  return (
    <div className="relative flex items-center justify-center">
      {/* Glow behind */}
      <div
        className="absolute rounded-full"
        style={{
          width: 400,
          height: 400,
          background: "radial-gradient(circle, rgba(139,92,246,0.08), transparent 60%)",
          filter: "blur(40px)",
        }}
      />
      {/* 3D Orb */}
      <div className="orb-3d relative">
        {/* Inner rings */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="rounded-full border"
            style={{
              width: 220,
              height: 220,
              borderColor: "rgba(139,92,246,0.08)",
              animation: "ring-pulse 4s ease-in-out infinite 1s",
            }}
          />
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="rounded-full border"
            style={{
              width: 140,
              height: 140,
              borderColor: "rgba(45,212,191,0.1)",
              animation: "ring-pulse 4s ease-in-out infinite 2s",
            }}
          />
        </div>
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div
            className="flex items-center justify-center"
            style={{
              width: 60,
              height: 60,
              borderRadius: 16,
              background: "linear-gradient(135deg, rgba(139,92,246,0.2), rgba(45,212,191,0.1))",
              border: "1px solid rgba(255,255,255,0.06)",
              backdropFilter: "blur(10px)",
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#violetGradient)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <defs>
                <linearGradient id="violetGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#8B5CF6" />
                  <stop offset="100%" stopColor="#2DD4BF" />
                </linearGradient>
              </defs>
              <path d="M12 2a10 10 0 0 1 10 10c0 2.5-1 4.7-2.5 6.3L12 12V2z" />
              <path d="M12 12l6.3 6.3A10 10 0 1 1 12 2z" />
              <circle cx="12" cy="12" r="2" />
            </svg>
          </div>
        </div>
      </div>

      {/* Floating shapes */}
      <div className="shape-cube absolute" style={{ top: "10%", left: "-10%" }} />
      <div className="shape-ring absolute" style={{ bottom: "15%", right: "-8%", animationDelay: "2s" }} />
      <div className="shape-cube absolute" style={{ bottom: "5%", left: "5%", width: 32, height: 32, animationDelay: "3s" }} />
    </div>
  );
}

function BentoSection() {
  return (
    <section id="features" className="section-spacing">
      <div className="mx-auto max-w-6xl px-6">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-16">
          <span className="section-label mb-4">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--violet)", boxShadow: "0 0 8px var(--violet-glow)" }} />
            Feature Showcase
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight leading-[1.1] max-w-2xl" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
            Built for velocity,{" "}
            <span className="gradient-text">engineered for scale</span>
          </h2>
          <p className="mt-4 text-sm max-w-lg" style={{ color: "var(--text-secondary)" }}>
            Every component is designed to minimize friction and maximize output.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="bento-grid">
          {BENTO_FEATURES.map((item, i) => (
            <div key={item.title} className={`bento-card ${item.span}`} style={{ animationDelay: `${0.1 * i}s` }}>
              {/* Grid background effect */}
              <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: "linear-gradient(rgba(139,92,246,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.5) 1px, transparent 1px)", backgroundSize: "32px 32px" }} />

              <div className="relative z-10">
                {/* Icon */}
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-xl mb-5"
                  style={{
                    background: item.accent === "violet" ? "rgba(139,92,246,0.1)" : "rgba(45,212,191,0.1)",
                    border: `1px solid ${item.accent === "violet" ? "rgba(139,92,246,0.15)" : "rgba(45,212,191,0.15)"}`,
                    color: item.accent === "violet" ? "var(--violet)" : "var(--teal)",
                  }}
                >
                  {i === 0 && (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2a10 10 0 0 1 10 10c0 2.5-1 4.7-2.5 6.3L12 12V2z" />
                      <path d="M12 12l6.3 6.3A10 10 0 1 1 12 2z" />
                    </svg>
                  )}
                  {i === 1 && (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 20V10M18 20V4M6 20v-4" />
                    </svg>
                  )}
                  {i === 2 && (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M4 20h16M4 4h16v12H4z" />
                      <path d="M9 8h6M9 12h4" />
                    </svg>
                  )}
                </div>

                <h3 className="text-lg font-semibold mb-2" style={{ color: "var(--text-primary)" }}>{item.title}</h3>
                <p className="text-sm leading-relaxed mb-6" style={{ color: "var(--text-secondary)" }}>{item.desc}</p>

                {/* Content variants */}
                {"nodes" in item && item.nodes && (
                  <div className="node-tree">
                    {item.nodes.map((node) => (
                      <div key={node.label} className={`node-item ${node.status !== "pending" ? node.status : ""}`}>
                        <div className="node-dot" style={{
                          background: node.status === "done" ? "var(--teal)" : node.status === "active" ? "var(--violet)" : "var(--text-quiet)",
                          boxShadow: node.status === "active" ? "0 0 12px var(--violet-glow)" : "none",
                        }} />
                        <span className="text-xs font-medium" style={{
                          color: node.status === "done" ? "var(--teal)" : node.status === "active" ? "var(--text-primary)" : "var(--text-tertiary)",
                        }}>
                          {node.label}
                        </span>
                        {node.status === "active" && (
                          <span className="ml-auto text-[10px] font-medium" style={{ color: "var(--violet)" }}>
                            In progress...
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {"stat" in item && (
                  <div className="mt-4">
                    <div className="flex items-end gap-1 mb-2">
                      <span className="text-4xl font-bold gradient-text">{item.stat}</span>
                    </div>
                    <div
                      className="h-2 rounded-full overflow-hidden"
                      style={{ background: "rgba(255,255,255,0.04)" }}
                    >
                      <div
                        className="h-full rounded-full animate-glow-pulse"
                        style={{
                          width: "78%",
                          background: "linear-gradient(90deg, var(--violet), var(--teal))",
                        }}
                      />
                    </div>
                    <div className="flex justify-between mt-1">
                      <span className="text-[10px]" style={{ color: "var(--text-quiet)" }}>Baseline</span>
                      <span className="text-[10px]" style={{ color: "var(--text-quiet)" }}>Freebuff</span>
                    </div>
                  </div>
                )}

                {"platforms" in item && item.platforms && (
                  <div className="flex flex-wrap gap-2">
                    {item.platforms.map((p) => (
                      <span
                        key={p}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all"
                        style={{
                          background: "rgba(255,255,255,0.03)",
                          border: "1px solid rgba(255,255,255,0.04)",
                          color: "var(--text-tertiary)",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "rgba(139,92,246,0.08)";
                          e.currentTarget.style.borderColor = "rgba(139,92,246,0.15)";
                          e.currentTarget.style.color = "var(--text-primary)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "rgba(255,255,255,0.03)";
                          e.currentTarget.style.borderColor = "rgba(255,255,255,0.04)";
                          e.currentTarget.style.color = "var(--text-tertiary)";
                        }}
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function LiveSimulation() {
  return (
    <section id="workspace" className="section-spacing">
      <div className="mx-auto max-w-5xl px-6">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-12">
          <span className="section-label mb-4">
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--teal)", boxShadow: "0 0 8px var(--teal-glow)" }} />
            Live Simulation
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight leading-[1.1]" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
            Watch it work in{" "}
            <span className="gradient-text">real time</span>
          </h2>
          <p className="mt-4 text-sm max-w-lg" style={{ color: "var(--text-secondary)" }}>
            A live agent pipeline transforming a prompt into a fully generated application.
          </p>
        </div>

        {/* Terminal */}
        <div className="terminal-window">
          <div className="terminal-header">
            <div className="terminal-dot red" />
            <div className="terminal-dot yellow" />
            <div className="terminal-dot green" />
            <span className="text-[11px] ml-2 font-medium" style={{ color: "var(--text-tertiary)" }}>
              freebuff-agent — pipeline:generate
            </span>
            <span className="ml-auto text-[10px] flex items-center gap-1.5" style={{ color: "var(--teal)" }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--teal)", boxShadow: "0 0 6px var(--teal-glow)" }} />
              Active
            </span>
          </div>

          <div className="terminal-body">
            <div className="terminal-line">
              <span className="terminal-prompt">$ </span>
              <span className="terminal-command">freebuff generate "Build a SaaS dashboard with Stripe</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-command">&gt;   integration, user auth, and real-time analytics"</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-output">┌─ Initializing agent pipeline...</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-highlight">│  ○ Architect</span><span className="terminal-output"> analyzing request...</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-highlight">│  ✓ Architect</span><span className="terminal-success"> design complete</span>
              <span className="terminal-output"> (3.2s)</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-highlight">│  ● Planner</span><span className="terminal-output"> generating implementation plan...</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-highlight">│  ✓ Planner</span><span className="terminal-success"> 47 steps mapped</span>
              <span className="terminal-output"> (1.8s)</span>
            </div>
            <div className="terminal-line">
              <span className="terminal-highlight">│  ● Writer</span><span className="terminal-output"> writing code...</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function PricingSection({ onLaunch }: { onLaunch: () => void }) {
  return (
    <section id="pricing" className="section-spacing">
      <div className="mx-auto max-w-6xl px-6">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-16">
          <span className="section-label mb-4">
            Pricing
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight leading-[1.1]" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
            Simple, transparent{" "}
            <span className="gradient-text">pricing</span>
          </h2>
          <p className="mt-4 text-sm max-w-lg" style={{ color: "var(--text-secondary)" }}>
            Start free, upgrade when you need more power.
          </p>
        </div>

        {/* Cards */}
        <div className="pricing-grid">
          {PRICING_TIERS.map((tier) => (
            <div key={tier.name} className={`pricing-card ${tier.featured ? "featured" : ""}`}>
              {tier.featured && (
                <div
                  className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-[10px] font-bold uppercase tracking-[0.15em]"
                  style={{
                    background: "linear-gradient(135deg, var(--violet), #A78BFA)",
                    color: "#fff",
                    boxShadow: "0 4px 16px var(--violet-glow)",
                  }}
                >
                  Most Popular
                </div>
              )}
              <h3 className="text-lg font-semibold mb-1" style={{ color: "var(--text-primary)" }}>{tier.name}</h3>
              <div className="flex items-baseline gap-1 mb-2">
                <span className="text-4xl font-bold" style={{ color: "var(--text-primary)" }}>{tier.price}</span>
                {tier.period && <span className="text-sm" style={{ color: "var(--text-tertiary)" }}>{tier.period}</span>}
              </div>
              <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>{tier.desc}</p>
              <ul className="space-y-3 mb-8">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-center gap-2.5 text-sm" style={{ color: "var(--text-secondary)" }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={tier.featured ? "var(--violet)" : "var(--teal)"} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <button
                type="button"
                onClick={tier.name === "Enterprise" ? undefined : onLaunch}
                className={tier.featured ? "btn-primary w-full justify-center" : "btn-secondary w-full justify-center"}
                style={tier.featured ? {} : { borderColor: "var(--border-default)" }}
              >
                {tier.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TechMarquee() {
  const items = [
    "React 19", "TypeScript", "Python 3.12", "WebGL 2.0", "Three.js",
    "OpenAI", "Anthropic", "OpenRouter", "Node.js", "PostgreSQL",
    "Docker", "Kubernetes", "Redis", "GraphQL", "gRPC",
  ];

  return (
    <div style={{ background: "var(--bg-surface)", borderTop: "1px solid var(--border-default)", borderBottom: "1px solid var(--border-default)" }}>
      <div className="relative overflow-hidden py-5">
        <div
          className="flex animate-marquee gap-20 whitespace-nowrap"
          style={{ animationDuration: "50s" }}
        >
          {[...items, ...items, ...items].map((item, i) => (
            <span
              key={`${item}-${i}`}
              className="inline-flex items-center gap-3 text-xs font-medium uppercase tracking-[0.18em]"
              style={{ color: "var(--text-quiet)" }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: i % 2 === 0 ? "var(--violet)" : "var(--teal)" }}
              />
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── MAIN LANDING PAGE ── */

export default function HomeScreen() {
  const navigate = useNavigate();
  const [isLaunching, setIsLaunching] = useState(false);

  const handleLaunch = useCallback(() => {
    if (isLaunching) return;
    setIsLaunching(true);
    setTimeout(() => navigate("/generation"), 500);
  }, [navigate, isLaunching]);

  return (
    <div className="relative min-h-screen" style={{ background: "var(--bg-deep)" }}>
      {/* Background auroras */}
      <div className="aurora violet" style={{ top: "-10%", left: "-5%", width: 600, height: 600 }} />
      <div className="aurora teal" style={{ bottom: "-5%", right: "-10%", width: 500, height: 500 }} />

      {/* Grid pattern overlay */}
      <div className="fixed inset-0 z-0 bg-grid opacity-30 pointer-events-none" />

      {/* Navigation */}
      <FloatingNav onLaunch={handleLaunch} />

      {/* ═══════════════════════════════════════════════════════════
          HERO
          ═══════════════════════════════════════════════════════════ */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pt-32 md:pt-40 pb-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left: Text */}
          <div>
            <div className="flex items-center gap-2 mb-6">
              <span className="section-label">
                <span className="w-1.5 h-1.5 rounded-full animate-pulse-glow" style={{ background: "var(--violet)", boxShadow: "0 0 8px var(--violet-glow)" }} />
                Introducing Freebuff Agent
              </span>
            </div>

            <h1
              className="text-[clamp(2.5rem,6vw,4.5rem)] font-bold tracking-tight leading-[1.05]"
              style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}
            >
              Your AI engineer{" "}
              <span className="gradient-text">
                that ships
              </span>
              <br />
              production code
            </h1>

            <p className="mt-6 text-base leading-relaxed max-w-lg" style={{ color: "var(--text-secondary)" }}>
              Deploy production-grade applications from a single conversation. Freebuff Agent orchestrates a multi-agent pipeline to architect, plan, write, review, and ship your code.
            </p>

            <div className="mt-10 flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={handleLaunch}
                disabled={isLaunching}
                className="btn-primary"
              >
                <span>{isLaunching ? "Deploying..." : "Deploy Agent Now"}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>

              <a
                href="https://github.com/Daniel-debug-boop/Wren"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style={{ color: "var(--text-secondary)" }}>
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
                { value: "4.7x", label: "Faster Pipeline" },
                { value: "0", label: "External Deps", accent: true },
              ].map((stat) => (
                <div key={stat.label}>
                  <span
                    className="text-2xl font-bold"
                    style={{ color: stat.accent ? "var(--violet)" : "var(--text-primary)" }}
                  >
                    {stat.value}
                  </span>
                  <span className="block text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
                    {stat.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Right: 3D Orb */}
          <div className="hidden lg:flex items-center justify-center">
            <Hero3DOrb />
          </div>
        </div>
      </section>

      {/* Glow line divider */}
      <div className="mx-auto max-w-4xl px-6">
        <div className="glow-line" />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          BENTO FEATURES
          ═══════════════════════════════════════════════════════════ */}
      <BentoSection />

      {/* ═══════════════════════════════════════════════════════════
          TECH MARQUEE
          ═══════════════════════════════════════════════════════════ */}
      <TechMarquee />

      {/* ═══════════════════════════════════════════════════════════
          LIVE SIMULATION
          ═══════════════════════════════════════════════════════════ */}
      <LiveSimulation />

      {/* Glow line divider */}
      <div className="mx-auto max-w-4xl px-6">
        <div className="glow-line" />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          PRICING
          ═══════════════════════════════════════════════════════════ */}
      <PricingSection onLaunch={handleLaunch} />

      {/* ═══════════════════════════════════════════════════════════
          CTA SECTION
          ═══════════════════════════════════════════════════════════ */}
      <section className="section-spacing">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div
            className="relative p-12 md:p-20 rounded-2xl overflow-hidden"
            style={{
              background: "linear-gradient(135deg, rgba(139,92,246,0.05) 0%, rgba(45,212,191,0.03) 100%)",
              border: "1px solid rgba(139,92,246,0.1)",
            }}
          >
            {/* Subtle grid bg */}
            <div className="absolute inset-0 opacity-[0.015]" style={{ backgroundImage: "linear-gradient(rgba(139,92,246,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.5) 1px, transparent 1px)", backgroundSize: "32px 32px" }} />

            <div className="relative z-10">
              <h2 className="text-3xl md:text-5xl font-bold tracking-tight leading-[1.1]" style={{ color: "var(--text-primary)" }}>
                Ready to ship faster?
              </h2>
              <p className="mt-4 text-sm max-w-md mx-auto" style={{ color: "var(--text-secondary)" }}>
                Join the future of AI-powered development. Deploy your first agent in seconds.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-4">
                <button type="button" onClick={handleLaunch} disabled={isLaunching} className="btn-primary">
                  <span>{isLaunching ? "Deploying..." : "Deploy Agent Now"}</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
                <a
                  href="https://github.com/Daniel-debug-boop/Wren"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                >
                  <span>Read the docs</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          FOOTER
          ═══════════════════════════════════════════════════════════ */}
      <footer style={{ borderTop: "1px solid var(--border-default)", background: "var(--bg-surface)" }}>
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8">
            {/* Logo */}
            <div className="flex items-center gap-2.5">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg text-white text-xs font-bold"
                style={{ background: "linear-gradient(135deg, #8B5CF6, #A78BFA)" }}
              >
                F
              </div>
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Freebuff</span>
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full" style={{ background: "rgba(139,92,246,0.1)", color: "var(--violet)", border: "1px solid rgba(139,92,246,0.15)" }}>
                Agent
              </span>
            </div>

            {/* Links */}
            <div className="flex flex-wrap items-center justify-center gap-6">
              {FOOTER_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="text-xs transition-colors duration-200"
                  style={{ color: "var(--text-tertiary)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-tertiary)")}
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          <div className="mt-8 pt-6 flex flex-col md:flex-row items-center justify-between gap-4" style={{ borderTop: "1px solid var(--border-muted)" }}>
            <span className="text-xs" style={{ color: "var(--text-quiet)" }}>
              © 2026 Freebuff Agent. Open source AI engineering platform.
            </span>
            <span className="text-xs flex items-center gap-2" style={{ color: "var(--text-quiet)" }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--teal)", boxShadow: "0 0 6px var(--teal-glow)" }} />
              All systems operational
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
