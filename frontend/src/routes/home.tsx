"use client";

import { Link } from "react-router";

/* ── Landing Page ───────────────────────────────────────────────────────────
 * Restrained, dark, amber-accented design.
 * No glassmorphism overload, no fake terminal animations.
 * Product mockup hero + restrained bento grid + simple pricing.
 */

export default function HomePage() {
  return (
    <div style={{ background: "var(--bg-deep)" }}>
      {/* ── Navigation ── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50"
        style={{
          background: "rgba(10, 10, 12, 0.9)",
          borderBottom: "1px solid var(--border)",
          backdropFilter: "blur(16px)",
        }}
      >
        <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6">
          <Link to="/" className="flex items-center gap-2">
            <div
              className="flex h-7 w-7 items-center justify-center rounded-md text-white text-[10px] font-bold"
              style={{ background: "var(--accent)" }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0A0A0C" strokeWidth="2.5" strokeLinecap="round">
                <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                <path d="m2 17 10 5 10-5" />
                <path d="m2 12 10 5 10-5" />
              </svg>
            </div>
            <span className="text-sm font-semibold" style={{ color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
              Wren
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Features
            </a>
            <a href="#architecture" className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Architecture
            </a>
            <a href="#pricing" className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Pricing
            </a>
          </div>

          <Link to="/settings" className="btn-primary" style={{ height: 32, fontSize: 12, padding: "0 16px" }}>
            Open Workspace
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section
        className="mx-auto flex min-h-[70vh] max-w-6xl items-center px-6 pt-24 pb-16"
        style={{ animation: "fade-in 0.6s ease" }}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center w-full">
          {/* Left: Copy */}
          <div>
            <div className="section-tag mb-6">
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: "var(--accent)", boxShadow: "0 0 8px var(--accent-glow)" }}
              />
              Open Source AI Engineering
            </div>
            <h1
              className="text-[clamp(2.5rem,5vw,4rem)] font-semibold leading-[1.08] tracking-[-0.03em]"
              style={{ color: "var(--text-primary)" }}
            >
              Ship production code
              <br />
              <span className="gradient-text">from a conversation</span>
            </h1>
            <p className="mt-5 text-sm max-w-md leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              Wren is an open-source AI software engineer. It architects, plans, writes,
              and reviews code — all from a single prompt. Self-host your models.
              Keep your data private.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/generation" className="btn-primary">
                Open Workspace
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </Link>
              <a
                href="https://github.com/Daniel-debug-boop/Wren"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
                Self-host Docs
              </a>
            </div>

            <div className="mt-10 flex gap-8">
              <div>
                <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>4</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>Agent pipeline</div>
              </div>
              <div>
                <div className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>250+</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>LLM providers</div>
              </div>
              <div>
                <div className="text-lg font-semibold" style={{ color: "var(--accent)" }}>100%</div>
                <div className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>Self-hosted</div>
              </div>
            </div>
          </div>

          {/* Right: Product Mockup */}
          <div className="hidden lg:block" style={{ animation: "slide-in-right 0.8s ease" }}>
            <div className="mockup-frame">
              <div className="mockup-header">
                <div className="mockup-dot" style={{ background: "#FF5F56" }} />
                <div className="mockup-dot" style={{ background: "#FFBD2E" }} />
                <div className="mockup-dot" style={{ background: "#27C93F" }} />
                <span className="text-[10px] ml-2" style={{ color: "var(--text-muted)" }}>wren — agent:active</span>
                <span className="ml-auto flex items-center gap-1.5 text-[10px]" style={{ color: "var(--accent)" }}>
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--accent)" }} />
                  Agent running
                </span>
              </div>
              <div className="mockup-body">
                <div className="mockup-sidebar">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="mockup-sidebar-item" />
                  ))}
                </div>
                <div className="mockup-editor">
                  <div className="mockup-line mockup-line-highlight">// wren-generation.tsx</div>
                  <div className="mockup-line" style={{ marginTop: 8 }}>&nbsp;</div>
                  <div className="mockup-line"><span style={{ color: "var(--text-muted)" }}>import</span> <span style={{ color: "var(--text-secondary)" }}>{'{ useState }'}</span> <span style={{ color: "var(--text-muted)" }}>from</span> <span style={{ color: "#A3E635" }}>"react"</span></div>
                  <div className="mockup-line"><span style={{ color: "var(--text-muted)" }}>import</span> <span style={{ color: "var(--text-secondary)" }}>{'{ OrbitControls }'}</span> <span style={{ color: "var(--text-muted)" }}>from</span> <span style={{ color: "#A3E635" }}>"@react-three/drei"</span></div>
                  <div className="mockup-line">&nbsp;</div>
                  <div className="mockup-line"><span style={{ color: "var(--text-muted)" }}>function</span> <span style={{ color: "var(--accent)" }}>SolarSystem</span><span style={{ color: "var(--text-secondary)" }}>() {'{'}</span></div>
                  <div className="mockup-line">  <span style={{ color: "var(--text-muted)" }}>const</span> [hovered, setHovered] = <span style={{ color: "var(--text-muted)" }}>useState</span><span style={{ color: "var(--text-secondary)" }}>(null)</span></div>
                  <div className="mockup-line">&nbsp;</div>
                  <div className="mockup-line">  <span style={{ color: "var(--text-muted)" }}>return</span> (</div>
                  <div className="mockup-line mockup-line-accent">    &lt;Canvas camera=&#123;&#123; position: [0, 0, 15] &#125;&#125;&gt;</div>
                  <div className="mockup-line">      &lt;ambientLight intensity=&#123;0.5&#125; /&gt;</div>
                  <div className="mockup-line">      &lt;OrbitControls /&gt;</div>
                  <div className="mockup-line">      &lt;Planet position=&#123;[-4, 0, 0]&#125; color="#F59E0B" /&gt;</div>
                  <div className="mockup-line">      &lt;Planet position=&#123;[4, 1, 0]&#125; color="#2DD4BF" /&gt;</div>
                  <div className="mockup-line" style={{ color: "var(--accent)" }}>    &lt;/Canvas&gt;</div>
                  <div className="mockup-line"><span style={{ color: "var(--text-secondary)" }}>{'}'}</span></div>
                </div>
                <div className="mockup-panel">
                  <div className="flex items-center gap-2">
                    <div style={{ width: 20, height: 20, borderRadius: 4, background: "var(--bg-card)" }} />
                    <div className="flex-1">
                      <div className="mockup-panel-item" style={{ width: "60%" }} />
                      <div className="mockup-panel-item" style={{ width: "40%", marginTop: 4 }} />
                    </div>
                  </div>
                  <div className="divider" />
                  <div className="mockup-panel-item" style={{ width: "90%" }} />
                  <div className="mockup-panel-item" style={{ width: "75%" }} />
                  <div className="mockup-panel-item" style={{ width: "50%", background: "var(--accent-subtle)", border: "1px solid rgba(245,158,11,0.15)" }} />
                  <div className="divider" />
                  <div className="mockup-panel-item" style={{ width: "80%" }} />
                  <div className="mockup-panel-item" style={{ width: "60%" }} />
                </div>
              </div>
            </div>

            {/* Ambient nodes */}
            <div className="hero-ambient" style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: -1 }}>
              <div className="hero-ambient-glow" />
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="hero-node" />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Feature Grid ── */}
      <section id="features" style={{ padding: "80px 0" }}>
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col items-center text-center mb-14">
            <div className="section-tag mb-4">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--accent)" }} />
              Features
            </div>
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
              Everything you need to ship faster
            </h2>
            <p className="mt-3 text-sm max-w-md" style={{ color: "var(--text-secondary)" }}>
              A complete AI engineering platform that respects your privacy and infrastructure.
            </p>
          </div>

          <div className="bento-grid">
            <div className="bento-card col-span-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg mb-4" style={{ background: "var(--accent-subtle)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M12 2a10 10 0 0 1 10 10c0 2.5-1 4.7-2.5 6.3L12 12V2z" />
                  <path d="M12 12l6.3 6.3A10 10 0 1 1 12 2z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                Multi-Agent Pipeline
              </h3>
              <p className="text-sm leading-relaxed mb-5" style={{ color: "var(--text-secondary)" }}>
                Four specialized agents — Architect, Planner, Writer, Reviewer — collaborate
                to produce production-quality code from a single prompt.
              </p>
              <div className="flex flex-wrap gap-2">
                {["Architect", "Planner", "Writer", "Reviewer"].map((agent, i) => (
                  <span
                    key={agent}
                    className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[11px] font-medium"
                    style={{
                      background: i === 0 ? "var(--accent-subtle)" : "var(--bg-card)",
                      border: `1px solid ${i === 0 ? "rgba(245,158,11,0.15)" : "var(--border)"}`,
                      color: i === 0 ? "var(--accent)" : "var(--text-tertiary)",
                    }}
                  >
                    {agent}
                  </span>
                ))}
              </div>
            </div>

            <div className="bento-card">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg mb-4" style={{ background: "var(--accent-subtle)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M4 20h16M4 4h16v12H4z" />
                  <path d="M9 8h6M9 12h4" />
                </svg>
              </div>
              <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                OmniRoute Gateway
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                Routes across 250+ LLM providers with auto-fallback, token compression, and cost tracking.
              </p>
            </div>

            <div className="bento-card">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg mb-4" style={{ background: "var(--accent-subtle)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                Template Kits
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                Pre-built generators for Three.js 3D, full-stack apps, APIs, and more.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Divider ── */}
      <div className="mx-auto max-w-4xl px-6">
        <div className="divider-glow" />
      </div>

      {/* ── Architecture / Privacy Section ── */}
      <section id="architecture" style={{ padding: "80px 0" }}>
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="section-tag mb-4">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--accent)" }} />
                Architecture
              </div>
              <h2 className="text-3xl md:text-4xl font-semibold tracking-tight leading-[1.1]" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
                Your models.
                <br />
                Your data.
                <br />
                <span className="gradient-text">Your infrastructure.</span>
              </h2>
              <p className="mt-4 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                Unlike Cursor or Claude Code, Wren runs entirely on your infrastructure.
                Your code never leaves your network. Your API keys never touch a third-party server.
              </p>
            </div>
            <div>
              <div className="card p-8">
                <div className="flex flex-col gap-4">
                  {[
                    { label: "Your LLM Models", desc: "OpenAI, Anthropic, OpenRouter, local models" },
                    { label: "Your Codebase", desc: "Never leaves your network" },
                    { label: "Your Infrastructure", desc: "Self-hosted, Docker, or bare metal" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="flex items-start gap-3 rounded-lg p-3"
                      style={{ background: "var(--bg-card)", border: "1px solid var(--border)" }}
                    >
                      <div
                        className="flex h-6 w-6 items-center justify-center rounded mt-0.5"
                        style={{ background: "var(--accent-subtle)" }}
                      >
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round">
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                      </div>
                      <div>
                        <div className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{item.label}</div>
                        <div className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Divider ── */}
      <div className="mx-auto max-w-4xl px-6">
        <div className="divider-glow" />
      </div>

      {/* ── Pricing ── */}
      <section id="pricing" style={{ padding: "80px 0" }}>
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col items-center text-center mb-14">
            <div className="section-tag mb-4">Pricing</div>
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
              Start free. Scale on your terms.
            </h2>
            <p className="mt-3 text-sm" style={{ color: "var(--text-secondary)" }}>
              Open-source community edition. Enterprise features when you need them.
            </p>
          </div>

          <div className="pricing-grid">
            {/* Community */}
            <div className="pricing-card">
              <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Community</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-3xl font-semibold" style={{ color: "var(--text-primary)" }}>Free</span>
              </div>
              <p className="text-xs mb-6" style={{ color: "var(--text-secondary)" }}>
                For individuals exploring AI-powered development.
              </p>
              <ul className="space-y-2.5 mb-8">
                {["Full agent pipeline", "All LLM providers", "Community support", "Self-hosted"].map((feat) => (
                  <li key={feat} className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    {feat}
                  </li>
                ))}
              </ul>
              <Link to="/generation" className="btn-primary w-full justify-center text-xs" style={{ height: 40 }}>
                Get Started
              </Link>
            </div>

            {/* Pro */}
            <div className="pricing-card featured">
              <div
                className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-semibold"
                style={{ background: "var(--accent)", color: "#0A0A0C" }}
              >
                Most Popular
              </div>
              <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Pro</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-3xl font-semibold" style={{ color: "var(--text-primary)" }}>$29</span>
                <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>/month</span>
              </div>
              <p className="text-xs mb-6" style={{ color: "var(--text-secondary)" }}>
                For professional developers building at scale.
              </p>
              <ul className="space-y-2.5 mb-8">
                {["Unlimited projects", "Priority support", "Private sandboxes", "Custom model routing", "Team collaboration"].map((feat) => (
                  <li key={feat} className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    {feat}
                  </li>
                ))}
              </ul>
              <button className="btn-primary w-full justify-center text-xs" style={{ height: 40 }}>
                Upgrade to Pro
              </button>
            </div>

            {/* Enterprise */}
            <div className="pricing-card">
              <h3 className="text-base font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Enterprise</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-3xl font-semibold" style={{ color: "var(--text-primary)" }}>$99</span>
                <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>/month</span>
              </div>
              <p className="text-xs mb-6" style={{ color: "var(--text-secondary)" }}>
                For teams and organizations requiring advanced control.
              </p>
              <ul className="space-y-2.5 mb-8">
                {["Everything in Pro", "Dedicated agents", "SSO & SAML", "Audit logs", "SLA guarantee", "On-premise option"].map((feat) => (
                  <li key={feat} className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                    {feat}
                  </li>
                ))}
              </ul>
              <button className="btn-secondary w-full justify-center text-xs" style={{ height: 40 }}>
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA Section ── */}
      <section style={{ padding: "60px 0 80px" }}>
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div
            className="relative rounded-2xl p-12 md:p-16 overflow-hidden"
            style={{
              border: "1px solid var(--border)",
              background: "linear-gradient(135deg, rgba(245,158,11,0.03) 0%, transparent 100%)",
            }}
          >
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight" style={{ color: "var(--text-primary)", letterSpacing: "-0.03em" }}>
              Ready to ship faster?
            </h2>
            <p className="mt-3 text-sm max-w-sm mx-auto" style={{ color: "var(--text-secondary)" }}>
              Deploy Wren on your infrastructure. Your data stays yours.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Link to="/generation" className="btn-primary">
                Open Workspace
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </Link>
              <a
                href="https://github.com/Daniel-debug-boop/Wren"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
              >
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer style={{ borderTop: "1px solid var(--border)" }}>
        <div className="mx-auto max-w-6xl px-6 py-10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-md" style={{ background: "var(--accent)" }}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#0A0A0C" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5Z" />
                  <path d="m2 17 10 5 10-5" />
                  <path d="m2 12 10 5 10-5" />
                </svg>
              </div>
              <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Wren</span>
            </div>

            <div className="flex flex-wrap items-center gap-6">
              <a href="#" className="text-xs" style={{ color: "var(--text-tertiary)" }}>Documentation</a>
              <a href="#" className="text-xs" style={{ color: "var(--text-tertiary)" }}>API Reference</a>
              <a href="https://github.com/Daniel-debug-boop/Wren" className="text-xs" style={{ color: "var(--text-tertiary)" }}>GitHub</a>
              <a href="#" className="text-xs" style={{ color: "var(--text-tertiary)" }}>Privacy</a>
              <a href="#" className="text-xs" style={{ color: "var(--text-tertiary)" }}>Terms</a>
            </div>
          </div>

          <div className="mt-8 pt-6 flex flex-col md:flex-row items-center justify-between gap-4" style={{ borderTop: "1px solid var(--border)" }}>
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              © 2026 Wren. Open source AI engineering platform.
            </span>
            <span className="text-xs flex items-center gap-2" style={{ color: "var(--text-muted)" }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--accent)" }} />
              Self-hosted. Private. Yours.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
