import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";
import { useAppMode } from "#/hooks/use-app-mode";
import { useConfig } from "#/hooks/query/use-config";
import SettingsService from "#/api/settings-service/settings-service.api";
import GitService from "#/api/git-service/git-service.api";
import type { GitRepository } from "#/types/git";
import { Button } from "#/components/ui/Button";
import { Nav } from "#/components/ui/Nav";
import { Footer } from "#/components/ui/Footer";
import { EmptyState } from "#/components/ui/EmptyState";

type LaunchTarget = "header" | "repo" | "task" | null;

export default function HomeScreen() {
  const navigate = useNavigate();
  const { data: config } = useConfig();
  const { isOss, isSaas, isCloud } = useAppMode();

  const [settings404, setSettings404] = useState(false);
  const [settingsChecked, setSettingsChecked] = useState(false);

  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedRepo, setSelectedRepo] = useState<GitRepository | null>(null);
  const [repositories, setRepositories] = useState<GitRepository[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [branches, setBranches] = useState<
    { name: string; commit_sha: string; protected: boolean }[]
  >([]);
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [providerDropdownOpen, setProviderDropdownOpen] = useState(false);
  const [repoDropdownOpen, setRepoDropdownOpen] = useState(false);

  const [launchTarget, setLaunchTarget] = useState<LaunchTarget>(null);

  const [ctaDismissed, setCtaDismissed] = useState(() => {
    try {
      return localStorage.getItem("homepage_cta_dismissed") === "true";
    } catch {
      return false;
    }
  });

  const showHomepageCta = isCloud && !ctaDismissed;

  const providers = useMemo(
    () => config?.providers_configured ?? ["github", "gitlab"],
    [config],
  );

  // Check settings on mount
  useEffect(() => {
    if (settingsChecked) return;
    let cancelled = false;
    SettingsService.getSettings()
      .then(() => {
        if (!cancelled) setSettingsChecked(true);
      })
      .catch((err) => {
        if (cancelled) return;
        const status = err?.response?.status ?? err?.status;
        if (status === 404 && config?.app_mode === "oss") {
          setSettings404(true);
        }
        setSettingsChecked(true);
      });
    return () => {
      cancelled = true;
    };
  }, [config?.app_mode, settingsChecked]);

  // Load repos on mount
  useEffect(() => {
    setLoadingRepos(true);
    GitService.retrieveUserGitRepositories()
      .then((res) => {
        setRepositories(res.items ?? []);
        setLoadingRepos(false);
      })
      .catch(() => {
        setLoadingRepos(false);
      });
  }, []);

  // Load branches when repo selected
  useEffect(() => {
    if (!selectedRepo) return;
    GitService.getRepositoryBranches({ repository_id: selectedRepo.id })
      .then((res) => {
        setBranches(res.items ?? []);
        const main = res.items?.find(
          (b) => b.name === "main" || b.name === "master",
        );
        if (main) setSelectedBranch(main.name);
      })
      .catch(() => {});
  }, [selectedRepo]);

  const handleLaunch = useCallback(
    (target: LaunchTarget) => {
      setLaunchTarget(target);
      setTimeout(() => {
        navigate("/conversations/new");
      }, 300);
    },
    [navigate],
  );

  const handleDismissCta = useCallback(() => {
    setCtaDismissed(true);
    try {
      localStorage.setItem("homepage_cta_dismissed", "true");
    } catch {}
  }, []);

  const filteredRepos = useMemo(() => {
    if (!selectedRepo) return repositories;
    return repositories.filter((r) => r.id === selectedRepo.id);
  }, [repositories, selectedRepo]);

  const hasConnectedRepo = repositories.length > 0;

  const isLaunching = launchTarget !== null;

  const ProviderIcon = ({ name, className }: { name: string; className?: string }) => {
    const icons: Record<string, React.ReactNode> = {
      github: (
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.536-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
        </svg>
      ),
      gitlab: (
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M21 6H5.071L11.437 1.367l1.89 1.863L7.422 12l5.904 8.77 1.89-1.863L5.071 18H21v-12z" />
        </svg>
      ),
    };
    return icons[name] || icons.github;
  };

  const BranchIcon = (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="6" y1="3" x2="6" y2="15" />
      <circle cx="18" cy="6" r="3" />
      <circle cx="6" cy="18" r="3" />
      <path d="M18 9a9 9 0 0 1 0 18" />
    </svg>
  );

  return (
    <div data-testid="home-screen" className="flex min-h-screen flex-col">
      {/* Skip link target */}
      <main id="main" className="flex-1" />

      {/* ── Floating Nav (N5) ── */}
      <Nav />

      {/* ── Hero ── */}
      <section className="relative mx-auto mt-20 max-w-5xl px-6 pb-20 animate-fade-in-up">
        <div className="gradient-glow" aria-hidden="true" />
        <h1
          className="text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight leading-[1.1] max-w-4xl"
          style={{ color: "var(--text)" }}
        >
          Build with an AI engineer that runs code
        </h1>
        <p
          className="mt-6 max-w-2xl text-lg"
          style={{ color: "var(--text-muted)" }}
        >
          Wren spins up real sandboxes, connects to your repos, and writes
          production-ready code — all from chat.
        </p>
        <div className="mt-10 flex flex-wrap items-center gap-3">
          <Button
            size="lg"
            onClick={() => handleLaunch("header")}
            rightIcon={<span aria-hidden="true">→</span>}
          >
            Launch Wren
          </Button>
          <Button variant="ghost" size="lg" onClick={() => navigate("/docs")}>
            Read the docs
          </Button>
        </div>

        {/* Homepage CTA (Cloud only) */}
        {showHomepageCta && (
          <div className="mt-12 card gradient-accent-border p-4 animate-slide-in-right">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-lg"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                    boxShadow:
                      "0 0 16px color-mix(in srgb, var(--accent) 20%, transparent)",
                  }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="white"
                    aria-hidden="true"
                  >
                    <path d="M8 0L16 8L8 16L0 8L8 0Z" />
                  </svg>
                </div>
                <div>
                  <p
                    className="text-sm font-medium"
                    style={{ color: "var(--text)" }}
                  >
                    Get started faster
                  </p>
                  <p
                    className="text-xs"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    Learn about Wren Cloud features
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href="https://wren.ai/cloud"
                  target="_blank"
                  rel="noreferrer noopener"
                  className="btn-accent rounded-lg px-3 py-1.5 text-xs font-medium"
                >
                  Learn more
                </a>
                <Button variant="ghost" size="sm" onClick={handleDismissCta}>
                  Dismiss
                </Button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* ── Repo Connector ── */}
      <section
        className="mx-auto max-w-5xl px-6 pb-20 animate-fade-in-up"
        style={{ animationDelay: "300ms" }}
        aria-label="Connect repository"
      >
        <div className="card gradient-accent-border p-6">
          <h2
            className="text-sm font-semibold tracking-tight mb-4"
            style={{ color: "var(--text)" }}
          >
            Connect a repository
          </h2>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            {/* Provider */}
            <div className="flex flex-col gap-1.5 sm:flex-1">
              <label
                className="text-xs font-medium"
                style={{ color: "var(--text-muted)" }}
              >
                Provider
              </label>
              <div className="relative">
                <button
                  data-testid="git-provider-dropdown"
                  type="button"
                  onClick={() => setProviderDropdownOpen((o) => !o)}
                  className="input flex h-10 items-center gap-2 px-3 text-sm justify-between"
                  style={{ minWidth: "160px", color: "var(--text)" }}
                  aria-haspopup="listbox"
                  aria-expanded={providerDropdownOpen}
                >
                  <span>
                    {selectedProvider === "github"
                      ? "GitHub"
                      : selectedProvider === "gitlab"
                        ? "GitLab"
                        : selectedProvider
                          ? selectedProvider.charAt(0).toUpperCase() +
                            selectedProvider.slice(1)
                          : "Select provider"}
                  </span>
                  <svg
                    width="14"
                    height="8"
                    viewBox="0 0 14 8"
                    fill="none"
                    className="ml-auto text-subtle"
                    aria-hidden="true"
                  >
                    <path
                      d="M1 1l6 6 6-6"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
                {providerDropdownOpen && (
                  <div
                    className="card absolute left-0 top-full z-50 mt-1 w-full overflow-hidden rounded-lg py-1 shadow-lg"
                    style={{ borderColor: "var(--border-strong)" }}
                    role="listbox"
                  >
                    {providers
                      .filter((p) => p !== selectedProvider)
                      .map((p) => (
                        <button
                          key={p}
                          type="button"
                          role="option"
                          onClick={() => {
                            setSelectedProvider(p);
                            setProviderDropdownOpen(false);
                          }}
                          className="flex w-full px-3 py-2 text-left text-sm press transition-colors"
                          style={{ color: "var(--text)" }}
                        >
                          <ProviderIcon
                            name={p}
                            className="mr-2 w-4 h-4 flex-shrink-0"
                          />
                          {p === "github"
                            ? "GitHub"
                            : p === "gitlab"
                              ? "GitLab"
                              : p.charAt(0).toUpperCase() + p.slice(1)}
                        </button>
                      ))}
                  </div>
                )}
              </div>
            </div>

            {/* Repository */}
            <div className="flex flex-1 flex-col gap-1.5">
              <label
                className="text-xs font-medium"
                style={{ color: "var(--text-muted)" }}
              >
                Repository
              </label>
              <div className="relative">
                <button
                  data-testid="git-repo-dropdown"
                  type="button"
                  onClick={() => {
                    if (selectedProvider) setRepoDropdownOpen((o) => !o);
                  }}
                  disabled={!selectedProvider}
                  className="input flex h-10 w-full items-center gap-2 px-3 text-sm justify-between disabled:opacity-40"
                  style={{ color: "var(--text)" }}
                  aria-haspopup="listbox"
                  aria-expanded={repoDropdownOpen}
                >
                  <span>
                    {loadingRepos
                      ? "Loading..."
                      : selectedRepo
                        ? selectedRepo.full_name
                        : "Select repository"}
                  </span>
                  <svg
                    width="14"
                    height="8"
                    viewBox="0 0 14 8"
                    fill="none"
                    className="ml-auto text-subtle"
                    aria-hidden="true"
                  >
                    <path
                      d="M1 1l6 6 6-6"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
                {repoDropdownOpen && (
                  <div
                    data-testid="git-repo-dropdown-menu"
                    className="card absolute left-0 top-full z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-lg py-1 shadow-lg"
                    style={{ borderColor: "var(--border-strong)" }}
                    role="listbox"
                  >
                    {repositories.map((repo) => (
                      <button
                        key={repo.id}
                        type="button"
                        role="option"
                        onClick={() => {
                          setSelectedRepo(repo);
                          setRepoDropdownOpen(false);
                        }}
                        className="flex w-full px-3 py-2 text-left text-sm press transition-colors"
                        style={{ color: "var(--text)" }}
                      >
                        {repo.full_name}
                      </button>
                    ))}
                    {repositories.length === 0 && !loadingRepos && (
                      <p
                        className="px-3 py-2 text-sm"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        No repositories found
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Branch */}
            <div className="flex flex-col gap-1.5 sm:w-40">
              <label
                className="text-xs font-medium"
                style={{ color: "var(--text-muted)" }}
              >
                Branch
              </label>
              <input
                data-testid="git-branch-dropdown-input"
                type="text"
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                disabled={!selectedRepo}
                className="input flex h-10 items-center px-3 text-sm disabled:opacity-40"
                style={{ color: "var(--text)", minWidth: "120px" }}
                placeholder="main"
              />
            </div>

            {/* Launch button */}
            <Button
              data-testid="repo-launch-button"
              size="md"
              disabled={!selectedRepo || isLaunching}
              onClick={() => handleLaunch("repo")}
              className="h-10"
            >
              Launch
            </Button>
          </div>
        </div>
      </section>

      {/* ── Suggested Tasks ── */}
      {hasConnectedRepo ? (
        <section
          className="mx-auto max-w-5xl px-6 pb-20 animate-fade-in-up"
          style={{ animationDelay: "400ms" }}
          aria-label="Suggested tasks"
        >
          <div className="card gradient-accent-border p-6">
            <h2
              className="text-sm font-semibold tracking-tight mb-4"
              style={{ color: "var(--text)" }}
            >
              Suggested tasks
            </h2>
            <div className="space-y-2">
              {filteredRepos.map((repo, index) => (
                <div
                  key={repo.id}
                  className="card p-3 flex items-center justify-between animate-fade-in-up"
                  style={{ animationDelay: `${index * 60}ms` }}
                >
                  <div className="flex items-center gap-2">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      style={{ color: "var(--accent)" }}
                      aria-hidden="true"
                    >
                      <path
                        d="M8 1C4.134 1 1 4.134 1 8s3.134 7 7 7 7-3.134 7-7-3.134-7-7-7z"
                        stroke="currentColor"
                        strokeWidth="1.5"
                      />
                      <path
                        d="M8 4.5v4M8 11v.5"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                    </svg>
                    <span className="text-sm" style={{ color: "var(--text)" }}>
                      {repo.full_name}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    disabled={isLaunching}
                    onClick={() => handleLaunch("task")}
                  >
                    Launch
                  </Button>
                </div>
              ))}
              {filteredRepos.length === 0 && (
                <p
                  className="text-sm text-center"
                  style={{ color: "var(--text-subtle)" }}
                >
                  Connect a repository to see suggested tasks.
                </p>
              )}
            </div>
          </div>
        </section>
      ) : (
        <section
          className="mx-auto max-w-5xl px-6 pb-20 animate-fade-in-up"
          style={{ animationDelay: "400ms" }}
        >
          <div className="card gradient-accent-border p-6 text-center">
            <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
              Connect a repository to see suggested tasks and recent
              conversations.
            </p>
          </div>
        </section>
      )}

      {/* ── Start Fresh / Import ── */}
      <section
        className="mx-auto max-w-5xl px-6 pb-20 animate-fade-in-up"
        style={{ animationDelay: "500ms" }}
        aria-label="Quick actions"
      >
        <div className="flex flex-col gap-4 md:flex-row">
          <div className="card flex flex-1 flex-col gap-3 p-6">
            <h3
              className="text-sm font-semibold tracking-tight"
              style={{ color: "var(--text)" }}
            >
              Start fresh
            </h3>
            <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
              Begin a new conversation without a repository
            </p>
            <Button
              variant="secondary"
              className="mt-auto h-9 justify-center rounded-lg text-xs font-medium"
              disabled={isLaunching}
              onClick={() => handleLaunch("header")}
            >
              New conversation
            </Button>
          </div>
          <div className="card flex flex-1 flex-col gap-3 p-6">
            <h3
              className="text-sm font-semibold tracking-tight"
              style={{ color: "var(--text)" }}
            >
              Import project
            </h3>
            <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
              Clone a repository to start working
            </p>
            <Button
              variant="secondary"
              className="mt-auto h-9 justify-center rounded-lg text-xs font-medium"
              disabled={isLaunching}
            >
              Import
            </Button>
          </div>
        </div>
      </section>

      {/* ── Recent Conversations ── */}
      {hasConnectedRepo && (
        <section
          className="mx-auto max-w-5xl px-6 pb-20 animate-fade-in-up"
          style={{ animationDelay: "600ms" }}
          aria-label="Recent conversations"
        >
          <div className="flex flex-col gap-4 md:flex-row">
            <div className="card flex flex-1 flex-col gap-3 p-6">
              <h3
                className="text-sm font-medium"
                style={{ color: "var(--text)" }}
              >
                Recent conversations
              </h3>
              <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                Continue where you left off
              </p>
              <EmptyState
                icon={
                  <svg
                    width="48"
                    height="48"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                }
                title="No conversations yet"
                description="Start a new conversation or connect a repository to see history here."
              />
            </div>
          </div>
        </section>
      )}

      {/* ── Footer (Ft2) ── */}
      <Footer version="1.30.0" />

      {/* ── AI Config Modal ── */}
      {settings404 && (
        <div
          data-testid="ai-config-modal"
          className="backdrop-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div className="card-elevated w-full max-w-md rounded-xl p-6 animate-scale-in">
            <h2
              className="text-lg font-semibold tracking-tight"
              style={{ color: "var(--text)" }}
            >
              AI Configuration Required
            </h2>
            <p className="mt-2 text-sm" style={{ color: "var(--text-subtle)" }}>
              Please configure your LLM provider to get started.
            </p>
            <div className="mt-6 flex items-center justify-between">
              <Link
                to="/settings"
                target="_blank"
                rel="noreferrer noopener"
                className="text-sm underline underline-offset-2 transition-opacity hover:opacity-80"
                style={{ color: "var(--accent)" }}
              >
                Advanced settings →
              </Link>
              <Button onClick={() => setSettings404(false)}>Close</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
