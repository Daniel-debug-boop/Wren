"use client";

/* ── Skills & Capabilities Page ────────────────────────────────────────────
 * Browse available AI skills — domain-specific tools that enhance Wren's
 * pipeline for app building, 3D design, game dev, and more.
 */

const SKILLS = [
  {
    name: "Three.js 3D Engine",
    desc: "Generates complete Three.js scenes with React Three Fiber, shaders, orbit controls, and lighting.",
    icon: "🎮",
    count: "12 templates",
  },
  {
    name: "App Builder",
    desc: "Full-stack application generator with SQLAlchemy, JWT auth, Docker Compose, and Zustand stores.",
    icon: "🏗️",
    count: "8 templates",
  },
  {
    name: "Monaco Editor Integration",
    desc: "Integrates Monaco code editor with syntax highlighting, autocomplete, and multi-file support.",
    icon: "📝",
    count: "6 templates",
  },
  {
    name: "Browser Automation",
    desc: "Chrome DevTools-based testing, screenshots, form filling, and network monitoring for QA.",
    icon: "🕸️",
    count: "5 templates",
  },
  {
    name: "API Generator",
    desc: "REST and GraphQL API generation with OpenAPI specs, validation, and error handling.",
    icon: "🔌",
    count: "9 templates",
  },
  {
    name: "Scraping Engine",
    desc: "Anti-bot web scraping via Scrapling — bypasses Cloudflare, extracts content from protected sites.",
    icon: "🕷️",
    count: "4 templates",
  },
];

export default function SkillsPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
          Skills & Capabilities
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-tertiary)" }}>
          Domain-specific generators and tools that power Wren's AI pipeline.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {SKILLS.map((skill) => (
          <div key={skill.name} className="card p-5 hover:border-[var(--border-strong)] transition-all">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xl">{skill.icon}</span>
              <span className="rounded-full px-2 py-0.5 text-[10px] font-medium" style={{ background: "var(--accent-subtle)", color: "var(--accent)" }}>
                {skill.count}
              </span>
            </div>
            <h3 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
              {skill.name}
            </h3>
            <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {skill.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
