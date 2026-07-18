import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { motion } from "framer-motion";
import GitService from "#/api/git-service/git-service.api";
import type { GitRepository } from "#/types/git";
import { Button } from "#/components/ui/Button";
import { Nav } from "#/components/ui/Nav";

type LaunchTarget = "header" | "repo" | null;

/* ── Stagger fade-up for children ── */
const containerVariants = {
  hidden: { opacity: 0 } as const,
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const } },
};

/* ── Quick action cards data ── */
const ACTIONS = [
  {
    id: "new",
    title: "New Conversation",
    desc: "Start fresh with the AI",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
    ),
    gradient: "#E86C4A",
  },
  {
    id: "import",
    title: "Import Project",
    desc: "Clone a repo to work on",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
      </svg>
    ),
    gradient: "#6366F1",
  },
  {
    id: "skills",
    title: "Browse Skills",
    desc: "44+ capabilities available",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
      </svg>
    ),
    gradient: "#F59E0B",
  },
  {
    id: "orchestrate",
    title: "Orchestrate",
    desc: "Multi-agent workflows",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="8" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
    gradient: "#22C55E",
  },
];

export default function HomeScreen() {
  const navigate = useNavigate();
  const [selectedRepo, setSelectedRepo] = useState<GitRepository | null>(null);
  const [repositories, setRepositories] = useState<GitRepository[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [launchTarget, setLaunchTarget] = useState<LaunchTarget>(null);

  const isLaunching = launchTarget !== null;

  /* ── Load repos on mount ── */
  useEffect(() => {
    setLoadingRepos(true);
    GitService.retrieveUserGitRepositories()
      .then((res) => { setRepositories(res.items ?? []); setLoadingRepos(false); })
      .catch(() => setLoadingRepos(false));
  }, []);

  useEffect(() => {
    if (!selectedRepo) return;
    GitService.getRepositoryBranches({ repository_id: selectedRepo.id })
      .then((res) => {
        const main = res.items?.find((b) => b.name === "main" || b.name === "master");
        if (main) setSelectedBranch(main.name);
      })
      .catch(() => {});
  }, [selectedRepo]);

  const handleLaunch = useCallback(
    (target: LaunchTarget) => { setLaunchTarget(target); setTimeout(() => navigate("/conversations/new"), 300); },
    [navigate],
  );

  const handleAction = useCallback((id: string) => {
    if (id === "skills") navigate("/skills");
    else if (id === "orchestrate") navigate("/orchestration");
    else handleLaunch("header");
  }, [handleLaunch, navigate]);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
      className="flex min-h-screen flex-col"
    >
      <main id="main" className="flex-1" />

      {/* ── Floating Nav ── */}
      <Nav />

      {/* ════════════════════════════════════════
          HERO — Double-bezel glass architecture
          ════════════════════════════════════════ */}
      <section className="relative mx-auto mt-28 w-full max-w-5xl px-6">
        {/* Outer shell */}
        <div
          className="relative p-[2px] rounded-[2.5rem]"
          style={{
            background: "linear-gradient(135deg, rgba(232,108,74,0.15), rgba(99,102,241,0.08), transparent 60%)",
          }}
        >
          {/* Inner core */}
          <div
            className="relative overflow-hidden rounded-[calc(2.5rem-2px)] p-12 md:p-16"
            style={{
              background: "linear-gradient(160deg, rgba(24,24,27,0.95), rgba(17,17,19,0.98))",
              boxShadow: "inset 0 1px 1px rgba(255,255,255,0.06), 0 8px 48px rgba(0,0,0,0.4)",
            }}
          >
            {/* Aurora glow */}
            <div
              className="absolute -top-40 -right-40 h-[600px] w-[600px] rounded-full opacity-30"
              style={{
                background: "radial-gradient(circle, rgba(232,108,74,0.12), transparent 70%)",
                filter: "blur(80px)",
              }}
              aria-hidden="true"
            />

            {/* Eyebrow badge */}
            <motion.div variants={itemVariants} className="mb-6">
              <span
                className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em]"
                style={{
                  background: "color-mix(in srgb, var(--accent) 10%, transparent)",
                  border: "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
                  color: "var(--accent)",
                }}
              >
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-current animate-pulse-glow" />
                AI Engineering Platform
              </span>
            </motion.div>

            {/* Main heading */}
            <motion.h1
              variants={itemVariants}
              className="text-4xl md:text-6xl lg:text-7xl font-semibold tracking-tight leading-[1.05] max-w-3xl"
              style={{ color: "var(--text)" }}
            >
              Build with an AI engineer that{" "}
              <span
                className="bg-clip-text text-transparent"
                style={{
                  backgroundImage: "linear-gradient(135deg, var(--accent), #F59E0B)",
                }}
              >
                runs code
              </span>
            </motion.h1>

            <motion.p
              variants={itemVariants}
              className="mt-6 max-w-2xl text-lg leading-relaxed"
              style={{ color: "var(--text-muted)" }}
            >
              Wren spins up real sandboxes, connects to your repos, and writes production-ready code — all from a single conversation.
            </motion.p>

            {/* CTA row — Button-in-Button pattern */}
            <motion.div variants={itemVariants} className="mt-10 flex flex-wrap items-center gap-4">
              <button
                type="button"
                onClick={() => handleLaunch("header")}
                className="group relative inline-flex h-12 items-center gap-3 rounded-full px-7 text-sm font-semibold text-white transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.98]"
                style={{
                  background: "var(--accent)",
                  boxShadow: "0 4px 24px color-mix(in srgb, var(--accent) 30%, transparent)",
                }}
              >
                <span>Launch Wren</span>
                {/* Nested icon circle */}
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-full transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:translate-x-0.5 group-hover:-translate-y-[1px] group-hover:scale-105"
                  style={{ background: "rgba(0,0,0,0.2)" }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              </button>

              <button
                type="button"
                onClick={() => navigate("/docs")}
                className="inline-flex h-12 items-center gap-2 rounded-full px-6 text-sm font-medium transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:bg-white/5 active:scale-[0.98]"
                style={{ color: "var(--text-muted)", border: "1px solid var(--border)" }}
              >
                Read the docs
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M7 17l9.2-9.2M17 17V7H7" />
                </svg>
              </button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          QUICK ACTIONS — Asymmetrical Bento Grid
          ════════════════════════════════════════ */}
      <motion.section
        variants={containerVariants}
        className="mx-auto mt-12 w-full max-w-5xl px-6 pb-8"
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {ACTIONS.map((action, i) => (
            <motion.button
              key={action.id}
              variants={itemVariants}
              type="button"
              onClick={() => handleAction(action.id)}
              className="group relative overflow-hidden rounded-2xl p-5 text-left transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] hover:-translate-y-0.5 active:scale-[0.98]"
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              {/* Gradient accent on hover */}
              <div
                className="absolute inset-0 opacity-0 transition-opacity duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:opacity-100"
                style={{
                  background: `linear-gradient(135deg, ${action.gradient}08, transparent 60%)`,
                }}
                aria-hidden="true"
              />

              {/* Icon with double-bezel */}
              <div
                className="relative mb-3 flex h-10 w-10 items-center justify-center rounded-xl"
                style={{
                  background: `linear-gradient(135deg, ${action.gradient}15, transparent)`,
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                <span style={{ color: action.gradient === "#E86C4A" ? "var(--accent)" : undefined }}>
                  {action.icon}
                </span>
              </div>

              <h3 className="text-sm font-medium mb-0.5" style={{ color: "var(--text)" }}>{action.title}</h3>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>{action.desc}</p>
            </motion.button>
          ))}
        </div>
      </motion.section>

      {/* ════════════════════════════════════════
          REPO CONNECTOR — Glass card
          ════════════════════════════════════════ */}
      <motion.section
        variants={itemVariants}
        className="mx-auto w-full max-w-5xl px-6 pb-20"
        aria-label="Connect repository"
      >
        <div
          className="relative rounded-2xl p-6"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
          }}
        >
          <h2 className="text-sm font-semibold tracking-tight mb-5" style={{ color: "var(--text)" }}>
            Connect a repository
          </h2>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            {/* Repo select */}
            <div className="flex flex-1 flex-col gap-1.5">
              <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Repository</label>
              <select
                value={selectedRepo?.id || ""}
                onChange={(e) => {
                  const repo = repositories.find((r) => r.id === e.target.value);
                  setSelectedRepo(repo || null);
                }}
                className="input h-10"
                style={{ color: "var(--text)" }}
              >
                <option value="">Select a repository...</option>
                {repositories.map((r) => (
                  <option key={r.id} value={r.id}>{r.full_name}</option>
                ))}
              </select>
            </div>

            {/* Branch */}
            <div className="flex flex-col gap-1.5 sm:w-36">
              <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>Branch</label>
              <input
                type="text"
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                disabled={!selectedRepo}
                className="input h-10 disabled:opacity-40"
                placeholder="main"
              />
            </div>

            {/* Launch */}
            <Button
              size="md"
              disabled={!selectedRepo || isLaunching}
              onClick={() => handleLaunch("repo")}
              className="h-10"
              rightIcon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              }
            >
              Launch
            </Button>
          </div>

          {/* Recent repos */}
          {repositories.length > 0 && (
            <div className="mt-4 pt-4 border-t" style={{ borderColor: "var(--border)" }}>
              <div className="flex flex-wrap gap-2">
                {repositories.slice(0, 5).map((repo) => (
                  <button
                    key={repo.id}
                    type="button"
                    onClick={() => setSelectedRepo(repo)}
                    className="press rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-300"
                    style={{
                      background: selectedRepo?.id === repo.id ? "var(--accent-subtle)" : "rgba(255,255,255,0.03)",
                      color: selectedRepo?.id === repo.id ? "var(--accent)" : "var(--text-muted)",
                      border: `1px solid ${selectedRepo?.id === repo.id ? "color-mix(in srgb, var(--accent) 20%, transparent)" : "var(--border)"}`,
                    }}
                  >
                    {repo.full_name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.section>

      {/* ════════════════════════════════════════
          FEATURES — Editorial bento
          ════════════════════════════════════════ */}
      <motion.section
        variants={containerVariants}
        className="mx-auto w-full max-w-5xl px-6 pb-24"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            {
              span: "md:col-span-2 md:row-span-1",
              title: "Real sandboxes, real execution",
              desc: "Every conversation spins up an isolated sandbox with full shell access, file system, and network. Your code runs before you review it.",
              accent: "var(--accent)",
            },
            {
              span: "md:col-span-1",
              title: "44+ skills",
              desc: "Auto-triggering microagents for design, DevOps, backend, mobile, and more. The AI adapts to your workflow.",
              accent: "#22C55E",
            },
            {
              span: "md:col-span-1",
              title: "Git-native",
              desc: "Connect any repo. Automatic granular commits, PR creation, and Issue→PR workflow built in.",
              accent: "#6366F1",
            },
            {
              span: "md:col-span-2",
              title: "Multi-agent orchestration",
              desc: "Decompose complex tasks into sub-agents with working memory, self-reflection, and error recovery. Like having a team of engineers.",
              accent: "#F59E0B",
            },
          ].map((feat) => (
            <motion.div
              key={feat.title}
              variants={itemVariants}
              className={`relative overflow-hidden rounded-2xl p-6 group ${feat.span}`}
              style={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              <div
                className="absolute inset-0 opacity-0 transition-opacity duration-700 ease-[cubic-bezier(0.32,0.72,0,1)] group-hover:opacity-100"
                style={{
                  background: `linear-gradient(135deg, ${feat.accent}06, transparent 60%)`,
                }}
                aria-hidden="true"
              />
              <div className="relative">
                <div
                  className="mb-3 h-1 w-8 rounded-full"
                  style={{ background: feat.accent }}
                />
                <h3 className="text-base font-semibold mb-2" style={{ color: "var(--text)" }}>{feat.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>{feat.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.section>
    </motion.div>
  );
}
