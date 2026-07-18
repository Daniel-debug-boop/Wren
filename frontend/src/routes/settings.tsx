import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router";
import { useConfig } from "#/hooks/query/use-config";
import { useAppMode } from "#/hooks/use-app-mode";
import SettingsService from "#/api/settings-service/settings-service.api";
import { Button } from "#/components/ui/Button";
import { Input } from "#/components/ui/Input";
import { EmptyState } from "#/components/ui/EmptyState";
import { Footer } from "#/components/ui/Footer";
import { ErrorBoundary } from "#/components/ErrorBoundary";
import ApiKeysService, {
  PROVIDER_METADATA,
  ROLE_PROVIDER_PREFS,
} from "#/api/api-keys-service/api-keys-service.api";

type SettingsCategory =
  | "application"
  | "profile"
  | "appearance"
  | "llm"
  | "integrations"
  | "api-keys"
  | "secrets";

const CATEGORIES: {
  id: SettingsCategory;
  label: string;
  description: string;
}[] = [
  {
    id: "application",
    label: "Application",
    description: "General application preferences",
  },
  { id: "profile", label: "Profile", description: "Your personal information" },
  {
    id: "appearance",
    label: "Appearance",
    description: "Theme and layout density",
  },
  {
    id: "llm",
    label: "LLM",
    description: "Configure your language model provider",
  },
  {
    id: "integrations",
    label: "Integrations",
    description: "Connect your git providers",
  },
  {
    id: "api-keys",
    label: "API Keys",
    description: "Manage your programmatic keys",
  },
  {
    id: "secrets",
    label: "Secrets",
    description: "Manage your stored credentials",
  },
];

export default function SettingsPage() {
  return (
    <ErrorBoundary>
      <SettingsContent />
    </ErrorBoundary>
  );
}

function SettingsContent() {
  const navigate = useNavigate();
  const { data: config } = useConfig();
  const { isCloud } = useAppMode();
  const [active, setActive] = useState<SettingsCategory>("application");
  const [theme, setTheme] = useState<"dark" | "light" | "system">("dark");
  const [density, setDensity] = useState<"comfortable" | "compact" | "normal">(
    "comfortable",
  );
  const [displayName, setDisplayName] = useState("");
  const [llmModel, setLlmModel] = useState("");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">(
    "idle",
  );

  // Load user settings on mount
  useEffect(() => {
    let cancelled = false;
    SettingsService.getSettings()
      .then((data) => {
        if (!cancelled) {
          if (data.ui_theme) setTheme(data.ui_theme);
          if (data.ui_density) setDensity(data.ui_density);
          if (data.display_name) setDisplayName(data.display_name);
          if (data.llm_model) setLlmModel(data.llm_model);
          if (data.llm_api_key) setLlmApiKey(data.llm_api_key);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.toggle("light", theme === "light");
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("wren_theme", theme);
  }, [theme]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setSaveStatus("idle");
    try {
      await SettingsService.saveSettings({
        ui_theme: theme,
        ui_density: density,
        display_name: displayName,
        llm_model: llmModel,
        llm_api_key: llmApiKey || undefined,
      });
      setSaveStatus("success");
      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    } finally {
      setSaving(false);
    }
  }, [theme, density, displayName, llmModel, llmApiKey]);

  return (
    <div
      className="flex h-full w-full overflow-hidden"
      data-testid="settings-screen"
    >
      <div className="flex h-full flex-col">
        <main id="main" className="flex-1 overflow-y-auto pt-8">
          <div className="mx-auto max-w-5xl px-6 py-12 animate-fade-in-up">
            {/* Page Header */}
            <header className="mb-10">
              <h1
                className="text-3xl md:text-4xl font-semibold tracking-tight mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                Settings
              </h1>
              <p className="text-lg" style={{ color: "var(--text-subtle)" }}>
                Configure your Wren experience
              </p>
            </header>

            {/* ── Two-Column Layout ── */}
            <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-8">
              {/* Sidebar Navigation */}
              <aside
                className="lg:sticky lg:top-28 lg:self-start"
                aria-label="Settings categories"
              >
                <nav
                  className="card p-3 space-y-1"
                  style={{ borderColor: "var(--border)" }}
                >
                  {CATEGORIES.map((cat) => {
                    const selected = cat.id === active;
                    return (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => setActive(cat.id)}
                        className={`w-full text-left rounded-xl px-4 py-3 transition-all duration-200 ${
                          selected
                            ? "bg-accent/10 text-accent font-medium"
                            : "text-text-secondary hover:bg-hover hover:text-text-primary"
                        }`}
                        aria-current={selected ? "page" : undefined}
                      >
                        {cat.label}
                        <p
                          className="mt-0.5 text-xs font-normal opacity-70"
                          style={{
                            color: selected
                              ? "var(--accent)"
                              : "var(--text-quiet)",
                          }}
                        >
                          {cat.description}
                        </p>
                      </button>
                    );
                  })}
                </nav>
              </aside>

              {/* Content Panel */}
              <div className="space-y-8">
                {/* Application */}
                {active === "application" && (
                  <SettingsSection
                    title="Application"
                    description="General application preferences"
                  >
                    <SettingGroup>
                      <SettingItem
                        label="Theme"
                        description="Choose your preferred color scheme"
                      >
                        <div className="flex gap-2">
                          <Button
                            variant={theme === "dark" ? "primary" : "secondary"}
                            onClick={() => setTheme("dark")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <circle cx="12" cy="12" r="5" />
                              <line x1="12" y1="1" x2="12" y2="3" />
                              <line x1="12" y1="21" x2="12" y2="23" />
                              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                              <line
                                x1="18.36"
                                y1="18.36"
                                x2="19.78"
                                y2="19.78"
                              />
                              <line x1="1" y1="12" x2="3" y2="12" />
                              <line x1="21" y1="12" x2="23" y2="12" />
                              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                            </svg>
                            <div>Dark</div>
                          </Button>
                          <Button
                            variant={
                              theme === "light" ? "primary" : "secondary"
                            }
                            onClick={() => setTheme("light")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <circle cx="12" cy="12" r="5" />
                              <line x1="12" y1="1" x2="12" y2="3" />
                              <line x1="12" y1="21" x2="12" y2="23" />
                              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                              <line
                                x1="18.36"
                                y1="18.36"
                                x2="19.78"
                                y2="19.78"
                              />
                              <line x1="1" y1="12" x2="3" y2="12" />
                              <line x1="21" y1="12" x2="23" y2="12" />
                              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                            </svg>
                            <div>Light</div>
                          </Button>
                        </div>
                      </SettingItem>

                      <SettingItem
                        label="Density"
                        description="Adjust the spacing density of the interface"
                      >
                        <div className="flex gap-2">
                          <Button
                            variant={
                              density === "comfortable"
                                ? "primary"
                                : "secondary"
                            }
                            onClick={() => setDensity("comfortable")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <line x1="9" y1="9" x2="15" y2="9" />
                              <line x1="9" y1="15" x2="15" y2="15" />
                            </svg>
                            <div>Comfortable</div>
                          </Button>
                          <Button
                            variant={
                              density === "compact" ? "primary" : "secondary"
                            }
                            onClick={() => setDensity("compact")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <line x1="9" y1="11" x2="15" y2="11" />
                            </svg>
                            <div>Compact</div>
                          </Button>
                        </div>
                      </SettingItem>

                      <SettingItem
                        label="Auto-save"
                        description="Automatically save settings when changed"
                      >
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            defaultChecked
                            className="w-5 h-5 rounded border-border bg-surface text-accent focus:ring-2 focus:ring-accent/20"
                          />
                          <span
                            className="text-sm"
                            style={{ color: "var(--text-primary)" }}
                          >
                            Enabled
                          </span>
                        </label>
                      </SettingItem>
                    </SettingGroup>
                  </SettingsSection>
                )}

                {/* Profile */}
                {active === "profile" && (
                  <SettingsSection
                    title="Profile"
                    description="Your personal information"
                  >
                    <SettingGroup>
                      <SettingItem
                        label="Display name"
                        description="Name shown across the app"
                      >
                        <Input
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                          placeholder="Your name"
                          className="max-w-md"
                        />
                      </SettingItem>

                      <SettingItem
                        label="Email"
                        description="Your account email"
                      >
                        <Input
                          type="email"
                          value={config?.user?.email || ""}
                          disabled
                          className="max-w-md"
                        />
                      </SettingItem>

                      <SettingItem
                        label="Avatar"
                        description="Your profile picture"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center overflow-hidden border border-border">
                            <svg
                              width="32"
                              height="32"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              style={{ color: "var(--accent)" }}
                            >
                              <circle cx="12" cy="8" r="4" />
                              <path d="M4 20c0-4 3-7 8-7s8 3 8 7" />
                            </svg>
                          </div>
                          <Button variant="secondary">Change avatar</Button>
                        </div>
                      </SettingItem>
                    </SettingGroup>
                  </SettingsSection>
                )}

                {/* Appearance */}
                {active === "appearance" && (
                  <SettingsSection
                    title="Appearance"
                    description="Theme and layout density"
                  >
                    <SettingGroup>
                      <SettingItem
                        label="Theme"
                        description="Choose your preferred color scheme"
                      >
                        <div className="flex gap-2">
                          <Button
                            variant={theme === "dark" ? "primary" : "secondary"}
                            onClick={() => setTheme("dark")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <circle cx="12" cy="12" r="5" />
                              <line x1="12" y1="1" x2="12" y2="3" />
                              <line x1="12" y1="21" x2="12" y2="23" />
                              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                              <line
                                x1="18.36"
                                y1="18.36"
                                x2="19.78"
                                y2="19.78"
                              />
                              <line x1="1" y1="12" x2="3" y2="12" />
                              <line x1="21" y1="12" x2="23" y2="12" />
                              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                            </svg>
                            <div>Dark</div>
                          </Button>
                          <Button
                            variant={
                              theme === "light" ? "primary" : "secondary"
                            }
                            onClick={() => setTheme("light")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <circle cx="12" cy="12" r="5" />
                              <line x1="12" y1="1" x2="12" y2="3" />
                              <line x1="12" y1="21" x2="12" y2="23" />
                              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                              <line
                                x1="18.36"
                                y1="18.36"
                                x2="19.78"
                                y2="19.78"
                              />
                              <line x1="1" y1="12" x2="3" y2="12" />
                              <line x1="21" y1="12" x2="23" y2="12" />
                              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                            </svg>
                            <div>Light</div>
                          </Button>
                        </div>
                      </SettingItem>

                      <SettingItem
                        label="Density"
                        description="Adjust the spacing density of the interface"
                      >
                        <div className="flex gap-2">
                          <Button
                            variant={
                              density === "comfortable"
                                ? "primary"
                                : "secondary"
                            }
                            onClick={() => setDensity("comfortable")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <line x1="9" y1="9" x2="15" y2="9" />
                              <line x1="9" y1="15" x2="15" y2="15" />
                            </svg>
                            <div>Comfortable</div>
                          </Button>
                          <Button
                            variant={
                              density === "compact" ? "primary" : "secondary"
                            }
                            onClick={() => setDensity("compact")}
                            className="flex-1"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              className="mx-auto mb-1"
                              aria-hidden="true"
                            >
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <line x1="9" y1="11" x2="15" y2="11" />
                            </svg>
                            <div>Compact</div>
                          </Button>
                        </div>
                      </SettingItem>
                    </SettingGroup>
                  </SettingsSection>
                )}

                {/* LLM */}
                {active === "llm" && (
                  <SettingsSection
                    title="LLM Configuration"
                    description="Configure your language model provider"
                  >
                    <SettingGroup>
                      <SettingItem
                        label="Model"
                        description="Select the LLM model to use"
                      >
                        <select
                          value={llmModel}
                          onChange={(e) => setLlmModel(e.target.value)}
                          className="input max-w-md"
                        >
                          <option value="">Select a model...</option>
                          <option value="gpt-4o">GPT-4o (OpenAI)</option>
                          <option value="gpt-4-turbo">
                            GPT-4 Turbo (OpenAI)
                          </option>
                          <option value="claude-3-5-sonnet">
                            Claude 3.5 Sonnet (Anthropic)
                          </option>
                          <option value="claude-3-opus">
                            Claude 3 Opus (Anthropic)
                          </option>
                          <option value="gemini-1.5-pro">
                            Gemini 1.5 Pro (Google)
                          </option>
                          <option value="llama-3.1-70b">
                            Llama 3.1 70B (Meta)
                          </option>
                          <option value="mistral-large">
                            Mistral Large (Mistral AI)
                          </option>
                        </select>
                      </SettingItem>

                      <SettingItem
                        label="API Key"
                        description="Your LLM provider API key (stored securely)"
                      >
                        <Input
                          type="password"
                          value={llmApiKey}
                          onChange={(e) => setLlmApiKey(e.target.value)}
                          placeholder="sk-... or your provider key"
                          className="max-w-md"
                        />
                      </SettingItem>

                      <SettingItem
                        label="Provider"
                        description="Your LLM provider"
                      >
                        <Input
                          value={config?.llm_provider || "Not configured"}
                          disabled
                          className="max-w-md"
                        />
                      </SettingItem>
                    </SettingGroup>
                  </SettingsSection>
                )}

                {/* Integrations */}
                {active === "integrations" && (
                  <SettingsSection
                    title="Git Integrations"
                    description="Connect your git providers"
                  >
                    <SettingGroup>
                      <div className="flex flex-col gap-4">
                        {["github", "gitlab", "bitbucket"].map((provider) => (
                          <ProviderCard
                            key={provider}
                            name={
                              provider.charAt(0).toUpperCase() +
                              provider.slice(1)
                            }
                            connected={
                              config?.providers_configured?.includes(
                                provider,
                              ) ?? false
                            }
                            onConnect={() =>
                              navigate(
                                `/settings/integrations?provider=${provider}`,
                              )
                            }
                          />
                        ))}
                      </div>
                    </SettingGroup>
                  </SettingsSection>
                )}

                {/* API Keys */}
                {active === "api-keys" && <ApiKeysSettings />}

                {/* Secrets */}
                {active === "secrets" && (
                  <SettingsSection
                    title="Secrets"
                    description="Manage your stored credentials"
                  >
                    <SettingGroup>
                      <EmptyState
                        icon={
                          <svg
                            width="48"
                            height="48"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            style={{ color: "var(--text-quiet)" }}
                          >
                            <rect x="3" y="11" width="18" height="11" rx="2" />
                            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                          </svg>
                        }
                        title="No secrets stored"
                        description="Add secrets to securely use them in your conversations"
                        action={{
                          label: "Add secret",
                          onClick: () => {},
                          variant: "primary",
                        }}
                      />
                    </SettingGroup>
                  </SettingsSection>
                )}

                {/* Save Status */}
                {(saveStatus === "success" || saveStatus === "error") && (
                  <div className="fixed bottom-6 right-4 z-50 animate-slide-in-right">
                    <div
                      className={`card flex items-center gap-3 p-4 w-80 ${saveStatus === "success" ? "border-success/30" : "border-error/30"}`}
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        style={{
                          color:
                            saveStatus === "success"
                              ? "var(--success)"
                              : "var(--error)",
                          flexShrink: 0,
                        }}
                      >
                        {saving ? (
                          <>
                            <svg
                              className="animate-spin h-4 w-4"
                              xmlns="http://www.w3.org/2000/svg"
                              fill="none"
                              viewBox="0 0 24 24"
                              aria-hidden="true"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              />
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                              />
                            </svg>
                            Saving...
                          </>
                        ) : saveStatus === "success" ? (
                          <svg
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            aria-hidden="true"
                          >
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                            <polyline points="22 4 12 14.01 9 11.01" />
                          </svg>
                        ) : (
                          <svg
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            aria-hidden="true"
                          >
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                          </svg>
                        )}
                      </svg>
                      <span
                        className="text-sm flex-1"
                        style={{
                          color:
                            saveStatus === "success"
                              ? "var(--success)"
                              : "var(--error)",
                        }}
                      >
                        {saveStatus === "success"
                          ? "Settings saved"
                          : "Failed to save settings"}
                      </span>
                    </div>
                  </div>
                )}

                {/* Footer (Ft2) */}
                <Footer version="1.30.0" />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

/* ── Settings Section ── */
function SettingsSection({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="card p-6" style={{ borderColor: "var(--border)" }}>
      <header className="mb-6">
        <h2
          className="text-xl font-semibold tracking-tight"
          style={{ color: "var(--text-primary)" }}
        >
          {title}
        </h2>
        <p className="mt-1 text-sm" style={{ color: "var(--text-subtle)" }}>
          {description}
        </p>
      </header>
      <div className="space-y-6">{children}</div>
    </section>
  );
}

/* ── Setting Group ── */
function SettingGroup({ children }: { children: React.ReactNode }) {
  return <div className="space-y-6">{children}</div>;
}

/* ── Setting Item ── */
function SettingItem({
  label,
  description,
  children,
}: {
  label: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label
        className="text-sm font-medium"
        style={{ color: "var(--text-primary)" }}
      >
        {label}
      </label>
      <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
        {description}
      </p>
      <div className="mt-2">{children}</div>
    </div>
  );
}

/* ── API Keys Settings (inline) ── */
function ApiKeysSettings() {
  const navigate = useNavigate();
  const [providers, setProviders] = useState(() => ApiKeysService.getAll());

  // Re-read on mount
  useEffect(() => {
    setProviders(ApiKeysService.getAll());
  }, []);

  const roleAvailability = ApiKeysService.getRoleAvailability();
  const rolesEnabled = Object.values(roleAvailability).filter(
    (r) => r.available,
  ).length;

  const handleRemove = (pid: string) => {
    ApiKeysService.remove(pid);
    setProviders(ApiKeysService.getAll());
  };

  if (providers.length === 0) {
    return (
      <SettingsSection
        title="API Keys"
        description="Configure your LLM provider API keys for the Model Router"
      >
        <SettingGroup>
          <EmptyState
            icon={
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                style={{ color: "var(--text-quiet)" }}
              >
                <rect x="3" y="11" width="18" height="11" rx="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            }
            title="No API keys configured"
            description="Add your LLM provider API keys to enable multi-agent model routing. Each agent role (Planner, Researcher, Writer, Reviewer) uses the best model available."
            action={{
              label: "Configure API Keys",
              onClick: () => navigate("/api-keys"),
              variant: "primary",
            }}
          />
        </SettingGroup>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title="API Keys"
      description="Your configured LLM providers — the Model Router uses these to select the best model for each agent role."
    >
      <SettingGroup>
        {/* Status summary */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div
            className="p-3 rounded-xl flex items-center gap-3"
            style={{
              background: "color-mix(in srgb, var(--success) 8%, transparent)",
              border:
                "1px solid color-mix(in srgb, var(--success) 20%, transparent)",
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--success)"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <div>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--text)" }}
              >
                {providers.length} provider{providers.length !== 1 ? "s" : ""}
              </p>
              <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                Configured
              </p>
            </div>
          </div>
          <div
            className="p-3 rounded-xl flex items-center gap-3"
            style={{
              background: "color-mix(in srgb, var(--accent) 8%, transparent)",
              border:
                "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--accent)"
              strokeWidth="1.5"
              aria-hidden="true"
            >
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
            <div>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--text)" }}
              >
                {rolesEnabled}/4 roles
              </p>
              <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                Active
              </p>
            </div>
          </div>
        </div>

        {/* Provider list */}
        <div className="space-y-2">
          {providers.map((p) => {
            const meta = PROVIDER_METADATA[p.provider];
            const rolesForProvider = Object.entries(ROLE_PROVIDER_PREFS)
              .filter(([, info]) =>
                info.preferredProviders.includes(p.provider),
              )
              .map(([role]) => role);

            return (
              <div
                key={p.provider}
                className="card p-3 flex items-center justify-between gap-3"
                style={{ borderColor: "var(--border)" }}
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div
                    className="flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold flex-shrink-0"
                    style={{
                      background: "var(--accent-subtle)",
                      color: "var(--accent)",
                    }}
                  >
                    {(meta?.name || p.provider).charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <p
                      className="font-medium text-sm truncate"
                      style={{ color: "var(--text)" }}
                    >
                      {meta?.name || p.provider}
                    </p>
                    <p
                      className="text-xs font-mono truncate"
                      style={{ color: "var(--text-subtle)" }}
                    >
                      {p.model}
                    </p>
                  </div>
                  {/* Role tags */}
                  <div className="hidden sm:flex gap-1 ml-2">
                    {rolesForProvider.map((role) => (
                      <span
                        key={role}
                        className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                        style={{
                          background:
                            "color-mix(in srgb, var(--accent) 8%, transparent)",
                          color: "var(--accent)",
                        }}
                      >
                        {role}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate("/api-keys")}
                  >
                    Manage
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemove(p.provider)}
                    style={{ color: "var(--error)" }}
                  >
                    Remove
                  </Button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Add more button */}
        <div className="pt-2">
          <Button
            variant="secondary"
            onClick={() => navigate("/api-keys")}
            leftIcon={
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                aria-hidden="true"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            }
          >
            Add provider
          </Button>
        </div>
      </SettingGroup>
    </SettingsSection>
  );
}

/* ── Provider Card ── */
function ProviderCard({
  name,
  connected,
  onConnect,
}: {
  name: string;
  connected: boolean;
  onConnect: () => void;
}) {
  const icons: Record<string, React.ReactNode> = {
    GitHub: (
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
    GitLab: (
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
    Bitbucket: (
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
      </svg>
    ),
  };

  return (
    <div
      className="card p-4 flex items-center justify-between gap-4"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg"
          style={{
            background: "var(--surface-hover)",
            color: "var(--text-primary)",
          }}
        >
          {icons[name as keyof typeof icons]}
        </div>
        <div>
          <p className="font-medium" style={{ color: "var(--text-primary)" }}>
            {name}
          </p>
          <p
            className="text-xs"
            style={{
              color: connected ? "var(--success)" : "var(--text-subtle)",
            }}
          >
            {connected ? "Connected" : "Not connected"}
          </p>
        </div>
      </div>
      <Button
        variant={connected ? "secondary" : "primary"}
        size="sm"
        onClick={onConnect}
      >
        {connected ? "Manage" : "Connect"}
      </Button>
    </div>
  );
}
