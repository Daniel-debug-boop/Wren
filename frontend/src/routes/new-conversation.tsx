import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useConfig } from "#/hooks/query/use-config";
import { useAppMode } from "#/hooks/use-app-mode";
import SettingsService from "#/api/settings-service/settings-service.api";
import GitService from "#/api/git-service/git-service.api";
import type { GitRepository } from "#/types/git";
import { ConversationApi } from "#/api/conversation-service/conversation-service.api";
import type { AppConversationStartRequest } from "#/types/app-conversation";
import { Button } from "#/components/ui/Button";

type LaunchTarget = "header" | "repo" | "task" | null;

export default function NewConversationScreen() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: config } = useConfig();
  const { isCloud } = useAppMode();

  // Pre-fill from search params (e.g., from suggested tasks)
  const initialRepo = searchParams.get("repo");
  const initialBranch = searchParams.get("branch");
  const initialProvider = searchParams.get("provider");
  const initialTask = searchParams.get("task");
  const initialTitle = searchParams.get("title");

  // Settings error state for 404 modal
  const [settings404, setSettings404] = useState(false);
  const [settingsChecked, setSettingsChecked] = useState(false);

  // Repo selection state
  const [selectedProvider, setSelectedProvider] = useState<string | null>(
    initialProvider || null,
  );
  const [selectedRepo, setSelectedRepo] = useState<GitRepository | null>(null);
  const [repositories, setRepositories] = useState<GitRepository[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState(initialBranch || "main");
  const [providerDropdownOpen, setProviderDropdownOpen] = useState(false);
  const [repoDropdownOpen, setRepoDropdownOpen] = useState(false);

  // Launch state
  const [launchTarget, setLaunchTarget] = useState<LaunchTarget>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  const providers = useCallback(
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
        const main = res.items?.find(
          (b) => b.name === "main" || b.name === "master",
        );
        if (main) setSelectedBranch(main.name);
      })
      .catch(() => {});
  }, [selectedRepo]);

  // Pre-select repo from URL
  useEffect(() => {
    if (initialRepo) {
      const repo = repositories.find((r) => r.full_name === initialRepo);
      if (repo) setSelectedRepo(repo);
    }
  }, [initialRepo, repositories]);

  const handleLaunch = useCallback(
    async (target: LaunchTarget) => {
      setLaunchTarget(target);
      setStartError(null);
      setIsStarting(true);

      try {
        const request: AppConversationStartRequest = {
          initial_message:
            target === "task" && initialTask
              ? {
                  role: "user",
                  content: [{ type: "text", text: initialTask }],
                }
              : undefined,
          system_message_suffix: undefined,
          llm_model: undefined,
          selected_repository: selectedRepo?.full_name ?? undefined,
          selected_branch: selectedBranch ?? undefined,
          git_provider: (selectedProvider as any) ?? undefined,
          suggested_task:
            target === "task" && initialTask
              ? {
                  name: initialTitle || "Task",
                  description: "",
                  prompt: initialTask,
                }
              : undefined,
          title: initialTitle || undefined,
          trigger:
            target === "repo"
              ? "gui"
              : target === "task"
                ? "suggested_task"
                : "gui",
          agent_type: "default",
          mode: "code",
        };

        // Start conversation
        const task = await ConversationApi.startConversation(request);

        // Poll until ready
        const readyTask = await ConversationApi.pollUntilReady(
          task.id,
          (status) => {
            /* noop — status updates handled by pollUntilReady */
          },
        );

        if (readyTask.app_conversation_id) {
          navigate(`/conversations/${readyTask.app_conversation_id}`, {
            replace: true,
          });
        } else {
          throw new Error("Conversation started but no ID returned");
        }
      } catch (err) {
        // Detect 500 / sandbox errors and show a helpful message
        const axiosErr = err as {
          response?: { status?: number };
          message?: string;
        };
        const isServerError =
          axiosErr?.response?.status === 500 ||
          axiosErr?.message?.includes("500") ||
          axiosErr?.message?.includes("Network Error");
        if (isServerError) {
          // Check for specific image pull errors
          const msg = axiosErr?.message || "";
          if (
            msg.includes("Docker Image") ||
            msg.includes("docker") ||
            msg.includes("image")
          ) {
            setStartError(
              "⚠️ Agent server Docker image unavailable. Try pulling it manually: `docker pull ghcr.io/wren/agent-server:1.30.0-python`. Or use local runtime: `RUNTIME=local INSTALL_DOCKER=0 make run`",
            );
          } else {
            setStartError(
              "⚠️ Sandbox runtime unavailable. Ensure Docker is running or start the app with: `RUNTIME=local INSTALL_DOCKER=0 make run`",
            );
          }
        } else {
          setStartError(
            err instanceof Error ? err.message : "Failed to start conversation",
          );
        }
        setIsStarting(false);
      }
    },
    [
      navigate,
      selectedRepo,
      selectedBranch,
      selectedProvider,
      initialTask,
      initialTitle,
    ],
  );

  const handleDismissError = useCallback(() => setStartError(null), []);

  const hasConnectedRepo = repositories.length > 0;
  const isLaunching = launchTarget !== null;

  return (
    <div
      data-testid="new-conversation-screen"
      className="flex h-full flex-col overflow-y-auto"
    >
      {/* Ambient gradient background */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background: `
            radial-gradient(ellipse at 15% 25%, color-mix(in srgb, var(--accent) 2.5%, transparent) 0%, transparent 50%),
            radial-gradient(ellipse at 85% 15%, color-mix(in srgb, var(--accent) 1.5%, transparent) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 85%, color-mix(in srgb, var(--accent) 1%, transparent) 0%, transparent 50%)
          `,
        }}
      />
      {/* Dots pattern */}
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.012]"
        style={{
          backgroundImage: `radial-gradient(var(--accent) 1px, transparent 1px)`,
          backgroundSize: `48px 48px`,
        }}
      />

      <div className="relative z-10 mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-8 animate-fade-in-up">
        {/* ── Header ── */}
        <div>
          <h1
            className="text-2xl font-medium tracking-tight"
            style={{ color: "var(--text-primary)" }}
          >
            Start a new conversation
          </h1>
          <p
            className="mt-0.5 text-sm"
            style={{ color: "var(--text-tertiary)" }}
          >
            Choose how you'd like to begin
          </p>
        </div>

        {/* ── Start from Scratch ── */}
        <div
          className="card flex flex-1 flex-col gap-2 p-5 animate-fade-in-up"
          style={{ animationDelay: "100ms" }}
        >
          <h3
            className="text-sm font-semibold tracking-tight"
            style={{ color: "var(--text-primary)" }}
          >
            Start fresh
          </h3>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Begin a new conversation without a repository
          </p>
          <Button
            className="btn-accent mt-auto h-9 justify-center rounded-lg text-sm font-medium"
            disabled={isStarting}
            onClick={() => handleLaunch("header")}
          >
            {isStarting && launchTarget === "header"
              ? "Starting..."
              : "New conversation"}
          </Button>
        </div>

        {/* ── Import Project ── */}
        <div
          className="card flex flex-1 flex-col gap-2 p-5 animate-fade-in-up"
          style={{ animationDelay: "200ms" }}
        >
          <h3
            className="text-sm font-semibold tracking-tight"
            style={{ color: "var(--text-primary)" }}
          >
            Import project
          </h3>
          <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Clone a repository to start working
          </p>
          <Button
            className="mt-auto h-9 justify-center rounded-lg text-sm font-medium"
            disabled={isStarting}
          >
            Import
          </Button>
        </div>

        {/* ── Repo Connector ── */}
        {hasConnectedRepo && (
          <div
            data-testid="repo-connector"
            className="card gradient-accent-border p-5 animate-fade-in-up"
            style={{ animationDelay: "300ms" }}
          >
            <h2
              className="mb-3 text-sm font-semibold tracking-tight"
              style={{ color: "var(--text-primary)" }}
            >
              Continue with a repository
            </h2>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              {/* Provider */}
              <div className="flex flex-col gap-1.5">
                <label
                  className="text-xs font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Provider
                </label>
                <div className="relative">
                  <button
                    data-testid="git-provider-dropdown"
                    type="button"
                    onClick={() => setProviderDropdownOpen((o) => !o)}
                    className="glass-input flex h-9 items-center gap-2 px-3 text-sm"
                    style={{
                      color: "var(--text-primary)",
                      minWidth: "140px",
                    }}
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
                      width="10"
                      height="6"
                      viewBox="0 0 10 6"
                      fill="none"
                      className="ml-auto"
                    >
                      <path
                        d="M1 1l4 4 4-4"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                  {providerDropdownOpen && (
                    <div
                      className="card absolute left-0 top-full z-50 mt-1 w-full overflow-hidden rounded-lg py-1"
                      style={{ borderColor: "var(--border-strong)" }}
                    >
                      {providers()
                        .filter((p) => p !== selectedProvider)
                        .map((p) => (
                          <button
                            key={p}
                            type="button"
                            onClick={() => {
                              setSelectedProvider(p);
                              setProviderDropdownOpen(false);
                            }}
                            className="press flex w-full px-3 py-1.5 text-left text-sm capitalize transition-colors"
                            style={{ color: "var(--text-primary)" }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = "var(--hover)";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = "transparent";
                            }}
                          >
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
                  style={{ color: "var(--text-secondary)" }}
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
                    className="glass-input flex h-9 w-full items-center gap-2 px-3 text-sm disabled:opacity-40"
                    style={{ color: "var(--text-primary)" }}
                  >
                    <span>
                      {loadingRepos
                        ? "Loading..."
                        : selectedRepo
                          ? selectedRepo.full_name
                          : "Select repository"}
                    </span>
                    <svg
                      width="10"
                      height="6"
                      viewBox="0 0 10 6"
                      fill="none"
                      className="ml-auto"
                    >
                      <path
                        d="M1 1l4 4 4-4"
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
                      className="card absolute left-0 top-full z-50 mt-1 max-h-60 w-full overflow-y-auto rounded-lg py-1"
                      style={{ borderColor: "var(--border-strong)" }}
                    >
                      {repositories.map((repo) => (
                        <button
                          key={repo.id}
                          type="button"
                          onClick={() => {
                            setSelectedRepo(repo);
                            setRepoDropdownOpen(false);
                          }}
                          className="press flex w-full px-3 py-1.5 text-left text-sm transition-colors"
                          style={{ color: "var(--text-primary)" }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "var(--hover)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                          }}
                        >
                          {repo.full_name}
                        </button>
                      ))}
                      {repositories.length === 0 && !loadingRepos && (
                        <p
                          className="px-3 py-2 text-sm"
                          style={{ color: "var(--text-tertiary)" }}
                        >
                          No repositories found
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Branch */}
              <div className="flex flex-col gap-1.5">
                <label
                  className="text-xs font-medium"
                  style={{ color: "var(--text-secondary)" }}
                >
                  Branch
                </label>
                <input
                  data-testid="git-branch-dropdown-input"
                  type="text"
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  disabled={!selectedRepo}
                  className="glass-input flex h-9 items-center px-3 text-sm disabled:opacity-40"
                  style={{
                    color: "var(--text-primary)",
                    minWidth: "100px",
                  }}
                />
              </div>

              {/* Launch button */}
              <Button
                data-testid="repo-launch-button"
                type="button"
                disabled={!selectedRepo || isLaunching}
                onClick={() => handleLaunch("repo")}
                className="btn-accent h-9 gap-2 rounded-lg px-4 text-sm font-medium"
              >
                {isLaunching && launchTarget === "repo"
                  ? "Starting..."
                  : "Launch"}
              </Button>
            </div>
          </div>
        )}

        {/* ── Suggested Tasks ── */}
        {hasConnectedRepo ? (
          <div
            data-testid="task-suggestions"
            className="card gradient-accent-border p-5 animate-fade-in-up"
            style={{ animationDelay: "400ms" }}
          >
            <h2
              className="mb-3 text-sm font-semibold tracking-tight"
              style={{ color: "var(--text-primary)" }}
            >
              Suggested tasks
            </h2>

            <div className="flex flex-col gap-2">
              {repositories.map((repo, index) => (
                <div
                  key={repo.id}
                  className="card flex items-center justify-between rounded-lg p-3 press transition-all"
                  style={{
                    animation: `fade-in-up 0.4s var(--ease-out) both`,
                    animationDelay: `${index * 60}ms`,
                  }}
                >
                  <div className="flex items-center gap-2">
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      style={{ color: "var(--accent)" }}
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
                    <span
                      className="text-sm"
                      style={{ color: "var(--text-primary)" }}
                    >
                      {repo.full_name}
                    </span>
                  </div>
                  <Button
                    data-testid="task-launch-button"
                    type="button"
                    disabled={isLaunching}
                    onClick={() => handleLaunch("task")}
                    className="btn-accent rounded-lg px-3 py-1.5 text-xs font-medium"
                  >
                    Launch
                  </Button>
                </div>
              ))}
              {repositories.length === 0 && (
                <p
                  className="text-sm text-center"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  Connect a repository to see suggested tasks.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div
            className="card gradient-accent-border p-5 animate-fade-in-up"
            style={{ animationDelay: "400ms" }}
          >
            <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
              Connect a repository to see suggested tasks and recent
              conversations.
            </p>
          </div>
        )}

        {/* ── Start Fresh / Import (duplicate for non-repo state) ── */}
        {!hasConnectedRepo && (
          <div
            data-testid="home-screen-new-conversation-section"
            className="flex flex-col gap-3 md:flex-row animate-fade-in-up"
            style={{ animationDelay: "500ms" }}
          >
            <div className="card flex flex-1 flex-col gap-2 p-5">
              <h3
                className="text-sm font-semibold tracking-tight"
                style={{ color: "var(--text-primary)" }}
              >
                Start fresh
              </h3>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Begin a new conversation without a repository
              </p>
              <Button
                type="button"
                disabled={isLaunching}
                onClick={() => handleLaunch("header")}
                className="btn mt-auto h-8 justify-center rounded-lg text-xs font-medium"
              >
                New conversation
              </Button>
            </div>
            <div className="card flex flex-1 flex-col gap-2 p-5">
              <h3
                className="text-sm font-semibold tracking-tight"
                style={{ color: "var(--text-primary)" }}
              >
                Import project
              </h3>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Clone a repository to start working
              </p>
              <Button
                type="button"
                disabled={isLaunching}
                className="btn mt-auto h-8 justify-center rounded-lg text-xs font-medium"
              >
                Import
              </Button>
            </div>
          </div>
        )}

        {/* ── Recent Conversations ── */}
        {hasConnectedRepo && (
          <div
            data-testid="home-screen-recent-conversations-section"
            className="flex flex-col gap-3 md:flex-row animate-fade-in-up"
            style={{ animationDelay: "600ms" }}
          >
            <div className="card flex flex-1 flex-col gap-2 p-5">
              <h3
                className="text-sm font-medium"
                style={{ color: "var(--text-primary)" }}
              >
                Recent conversations
              </h3>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Continue where you left off
              </p>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                No recent conversations yet.
              </p>
            </div>
          </div>
        )}

        {/* ── AI Config Modal ── */}
        {settings404 && (
          <div
            data-testid="ai-config-modal"
            className="backdrop-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="card-elevated w-full max-w-md rounded-xl p-6 animate-scale-in">
              <h2
                className="text-lg font-semibold tracking-tight"
                style={{ color: "var(--text-primary)" }}
              >
                AI Configuration Required
              </h2>
              <p
                className="mt-2 text-sm"
                style={{ color: "var(--text-subtle)" }}
              >
                Please configure your LLM provider to get started.
              </p>

              <div className="mt-6 flex items-center justify-between">
                <a
                  data-testid="advanced-settings-link"
                  href="/settings"
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-sm underline underline-offset-2 transition-all hover:opacity-80"
                  style={{ color: "var(--accent)" }}
                >
                  Advanced settings →
                </a>
                <Button
                  type="button"
                  onClick={() => setSettings404(false)}
                  className="btn-accent rounded-lg px-4 py-2 text-sm font-medium"
                >
                  Close
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ── Start Error Toast ── */}
        {startError && (
          <div className="fixed bottom-6 right-4 z-50 animate-slide-in-right">
            <div
              className="card flex items-center gap-3 p-4 w-80"
              style={{
                borderColor: "var(--error)",
                boxShadow:
                  "0 0 20px color-mix(in srgb, var(--error) 20%, transparent)",
              }}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ color: "var(--error)", flexShrink: 0 }}
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <p
                className="text-sm flex-1"
                style={{ color: "var(--text-primary)" }}
              >
                {startError}
              </p>
              <button
                onClick={handleDismissError}
                className="text-sm hover:underline"
                style={{ color: "var(--text-subtle)" }}
              >
                Dismiss
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
