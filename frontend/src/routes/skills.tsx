import { useState, useEffect, useMemo } from "react";
import SkillsApi, { type SkillInfo } from "#/api/skills-service/skills-service.api";
import { Button } from "#/components/ui/Button";
import { Input } from "#/components/ui/Input";

/* ── Category definitions ── */

interface SkillCategory {
  id: string;
  label: string;
  description: string;
  keywords: string[];
}

const CATEGORIES: SkillCategory[] = [
  {
    id: "all",
    label: "All Skills",
    description: "Every skill available",
    keywords: [],
  },
  {
    id: "frontend",
    label: "Frontend",
    description: "React, UI, CSS, design systems",
    keywords: [
      "react", "vue", "angular", "css", "ui", "frontend", "design",
      "component", "tailwind", "typescript", "javascript", "jsx", "tsx",
    ],
  },
  {
    id: "backend",
    label: "Backend",
    description: "APIs, databases, servers, Python",
    keywords: [
      "api", "backend", "python", "database", "sql", "server",
      "fastapi", "django", "flask", "node", "graphql",
    ],
  },
  {
    id: "devops",
    label: "DevOps",
    description: "Docker, CI/CD, cloud, infrastructure",
    keywords: [
      "docker", "kubernetes", "ci", "cd", "deploy", "devops",
      "infrastructure", "terraform", "github actions", "pipeline",
    ],
  },
  {
    id: "design",
    label: "Design",
    description: "UI/UX, branding, animations, taste",
    keywords: [
      "design", "branding", "animation", "ui", "ux", "taste",
      "framer", "motion", "gsap", "layout", "typography",
    ],
  },
  {
    id: "game-dev",
    label: "Game Dev",
    description: "Godot, Unity, game mechanics",
    keywords: [
      "godot", "unity", "game", "3d", "meshy", "tripo",
    ],
  },
  {
    id: "tools",
    label: "Tools & Integrations",
    description: "Git, GitHub, CLI, MCP, scraping",
    keywords: [
      "git", "github", "gitlab", "cli", "mcp", "scraping",
      "terminal", "ssh", "docker", "integration",
    ],
  },
  {
    id: "other",
    label: "Other",
    description: "Miscellaneous skills",
    keywords: [],
  },
];

/* ── Helpers ── */

function categorizeSkill(name: string, triggers: string[] | null): string {
  const lower = `${name} ${(triggers || []).join(" ")}`.toLowerCase();

  for (const cat of CATEGORIES) {
    if (cat.id === "all" || cat.id === "other") continue;
    if (cat.keywords.some((kw) => lower.includes(kw))) return cat.id;
  }

  return "other";
}

function getSkillEmoji(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes("design") || lower.includes("taste") || lower.includes("brand")) return "🎨";
  if (lower.includes("react") || lower.includes("component") || lower.includes("ui")) return "⚛️";
  if (lower.includes("python") || lower.includes("backend") || lower.includes("api")) return "🐍";
  if (lower.includes("docker") || lower.includes("deploy") || lower.includes("devops")) return "🐳";
  if (lower.includes("git") || lower.includes("github") || lower.includes("pr")) return "🔀";
  if (lower.includes("test") || lower.includes("qa") || lower.includes("bug")) return "🧪";
  if (lower.includes("godot") || lower.includes("game") || lower.includes("3d")) return "🎮";
  if (lower.includes("mobile") || lower.includes("ios") || lower.includes("android")) return "📱";
  if (lower.includes("security") || lower.includes("auth")) return "🔒";
  if (lower.includes("mcp") || lower.includes("tool") || lower.includes("cli")) return "🔧";
  if (lower.includes("terminal") || lower.includes("shell")) return "💻";
  if (lower.includes("animation") || lower.includes("motion")) return "✨";
  if (lower.includes("documentation") || lower.includes("doc")) return "📝";
  return "📦";
}

/* ── Page Component ── */

export default function SkillsPage() {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const data = await SkillsApi.searchSkills(200);
        if (!cancelled) setSkills(data.items);
      } catch (err) {
        if (!cancelled) setError("Failed to load skills. Is the backend running?");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    let result = skills;

    // Filter by search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          (s.triggers || []).some((t) => t.toLowerCase().includes(q)),
      );
    }

    // Filter by category
    if (activeCategory !== "all") {
      result = result.filter((s) => categorizeSkill(s.name, s.triggers) === activeCategory);
    }

    return result;
  }, [skills, search, activeCategory]);

  /* ── Category counts ── */
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: skills.length };
    for (const cat of CATEGORIES) {
      if (cat.id === "all") continue;
      counts[cat.id] = skills.filter((s) => categorizeSkill(s.name, s.triggers) === cat.id).length;
    }
    return counts;
  }, [skills]);

  return (
    <div className="flex h-full flex-col overflow-hidden" data-testid="skills-screen">
      <main className="flex-1 overflow-y-auto pt-8">
        <div className="mx-auto max-w-5xl px-6 py-12 animate-fade-in-up">
          {/* Header */}
          <header className="mb-8">
            <h1
              className="text-3xl md:text-4xl font-semibold tracking-tight mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Skills
            </h1>
            <p className="text-lg" style={{ color: "var(--text-subtle)" }}>
              {skills.length} skills available — search and filter to find what you need
            </p>
          </header>

          {/* Search Bar */}
          <div className="relative mb-6">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="absolute left-3 top-1/2 -translate-y-1/2"
              style={{ color: "var(--text-quiet)" }}
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skills by name or trigger keyword..."
              className="w-full pl-10"
            />
          </div>

          {/* Category Pills */}
          <div className="flex flex-wrap gap-2 mb-8">
            {CATEGORIES.map((cat) => {
              const count = categoryCounts[cat.id] || 0;
              const selected = cat.id === activeCategory;
              return (
                <button
                  key={cat.id}
                  type="button"
                  onClick={() => setActiveCategory(cat.id)}
                  className="press flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-medium transition-all duration-200"
                  style={{
                    background: selected
                      ? "var(--accent)"
                      : "color-mix(in srgb, var(--border) 40%, transparent)",
                    color: selected ? "white" : "var(--text-secondary)",
                  }}
                  aria-pressed={selected}
                >
                  {cat.label}
                  <span
                    className="inline-flex items-center justify-center min-w-[1.1rem] h-[1.1rem] rounded-full px-1 text-[9px] font-bold"
                    style={{
                      background: selected
                        ? "rgba(255,255,255,0.2)"
                        : "color-mix(in srgb, var(--text-quiet) 20%, transparent)",
                    }}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Content */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="flex flex-col items-center gap-4">
                <div
                  className="h-8 w-8 animate-spin rounded-full border-2"
                  style={{
                    borderColor: "var(--border)",
                    borderTopColor: "var(--accent)",
                  }}
                />
                <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
                  Loading skills...
                </p>
              </div>
            </div>
          ) : error ? (
            <div
              className="card p-8 text-center"
              style={{ borderColor: "color-mix(in srgb, var(--error) 30%, transparent)" }}
            >
              <p style={{ color: "var(--error)" }}>{error}</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="card p-12 text-center animate-fade-in-up">
              <p className="text-4xl mb-4">🔍</p>
              <h3
                className="text-lg font-medium mb-1"
                style={{ color: "var(--text-primary)" }}
              >
                No skills found
              </h3>
              <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
                {search
                  ? `No skills match "${search}". Try a different search term.`
                  : "No skills in this category."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filtered.map((skill) => (
                <SkillCard key={`${skill.source}-${skill.name}`} skill={skill} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

/* ── Skill Card ── */

function SkillCard({ skill }: { skill: SkillInfo }) {
  const category = categorizeSkill(skill.name, skill.triggers);
  const cat = CATEGORIES.find((c) => c.id === category);

  return (
    <div
      className="card p-4 hover:card-hover transition-all duration-200 animate-fade-in-up group"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-start gap-3">
        {/* Emoji icon */}
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-lg"
          style={{
            background: "color-mix(in srgb, var(--accent) 8%, transparent)",
          }}
        >
          {getSkillEmoji(skill.name)}
        </div>

        <div className="flex-1 min-w-0">
          {/* Name + source badge */}
          <div className="flex items-center gap-2 mb-0.5">
            <h3
              className="text-sm font-medium truncate"
              style={{ color: "var(--text-primary)" }}
            >
              {skill.name}
            </h3>
            <span
              className="shrink-0 text-[9px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wider"
              style={{
                background:
                  skill.source === "global"
                    ? "color-mix(in srgb, var(--accent) 10%, transparent)"
                    : "color-mix(in srgb, var(--text-quiet) 15%, transparent)",
                color:
                  skill.source === "global"
                    ? "var(--accent)"
                    : "var(--text-quiet)",
              }}
            >
              {skill.source === "global" ? "built-in" : skill.source}
            </span>
          </div>

          {/* Category + Type */}
          <div className="flex items-center gap-2 mb-2">
            {cat && cat.id !== "other" && (
              <span
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{
                  background: "color-mix(in srgb, var(--text-quiet) 10%, transparent)",
                  color: "var(--text-quiet)",
                }}
              >
                {cat.label}
              </span>
            )}
            <span
              className="text-[10px]"
              style={{ color: "var(--text-quiet)" }}
            >
              {skill.type}
            </span>
          </div>

          {/* Triggers */}
          {skill.triggers && skill.triggers.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {skill.triggers.slice(0, 4).map((trigger) => (
                <span
                  key={trigger}
                  className="text-[9px] px-1.5 py-0.5 rounded font-mono"
                  style={{
                    background: "color-mix(in srgb, var(--border) 30%, transparent)",
                    color: "var(--text-muted)",
                  }}
                >
                  {trigger}
                </span>
              ))}
              {skill.triggers.length > 4 && (
                <span
                  className="text-[9px]"
                  style={{ color: "var(--text-quiet)" }}
                >
                  +{skill.triggers.length - 4}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
