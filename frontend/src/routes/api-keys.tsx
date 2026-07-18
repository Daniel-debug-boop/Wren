import { ErrorBoundary } from "#/components/ErrorBoundary";
import { useState, useEffect, useMemo, useRef } from "react";
import { useNavigate } from "react-router";
import { Button } from "#/components/ui/Button";
import { Input } from "#/components/ui/Input";
import ApiKeysService, {
  PROVIDER_METADATA,
  type ProviderConfig,
} from "#/api/api-keys-service/api-keys-service.api";

const PROVIDER_IDS = Object.keys(PROVIDER_METADATA);

export default function ApiKeysPage() {
  return (
    <ErrorBoundary>
      <ApiKeysContent />
    </ErrorBoundary>
  );
}

function ApiKeysContent() {
  const navigate = useNavigate();
  const [providers, setProviders] = useState<ProviderConfig[]>(() =>
    ApiKeysService.getAll(),
  );
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error";
  } | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [providerDropdownOpen, setProviderDropdownOpen] = useState(false);

  const refreshProviders = () => setProviders(ApiKeysService.getAll());

  // Toast effect
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(t);
  }, [toast]);

  const addFormRef = useRef<HTMLDivElement>(null);
  const providerBtnRef = useRef<HTMLButtonElement>(null);

  // Close provider dropdown on outside click
  useEffect(() => {
    if (!providerDropdownOpen) return;
    const handleClick = (e: MouseEvent) => {
      // Don't close if clicking the toggle button itself
      if (providerBtnRef.current?.contains(e.target as Node)) return;
      setProviderDropdownOpen(false);
    };
    document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [providerDropdownOpen]);

  // Reset form when provider changes
  useEffect(() => {
    if (!selectedProvider) return;
    const existing = ApiKeysService.get(selectedProvider);
    if (existing) {
      setSelectedModel(existing.model);
      setApiKey(existing.apiKey || "");
      setBaseUrl(existing.baseUrl || "");
    } else {
      const meta = PROVIDER_METADATA[selectedProvider];
      setSelectedModel(meta?.models?.[0] || "");
      setApiKey("");
      setBaseUrl("");
    }
    setErrors({});
  }, [selectedProvider]);

  const selectedMeta = selectedProvider
    ? PROVIDER_METADATA[selectedProvider]
    : null;

  // ── Save ──
  const handleSave = () => {
    if (!selectedProvider) {
      setErrors({ provider: "Select a provider" });
      return;
    }
    const meta = PROVIDER_METADATA[selectedProvider];
    if (!meta?.local && apiKey.trim().length < 4) {
      setErrors({ apiKey: "Enter a valid API key" });
      return;
    }

    ApiKeysService.save({
      provider: selectedProvider,
      model: selectedModel,
      apiKey: meta?.local ? undefined : apiKey.trim(),
      baseUrl: baseUrl.trim() || undefined,
    });

    refreshProviders();
    setToast({
      message: `${meta?.name || selectedProvider} configured successfully`,
      type: "success",
    });
    // Reset form to add another
    setSelectedProvider(null);
    setSelectedModel("");
    setApiKey("");
    setBaseUrl("");
  };

  // ── Remove ──
  const handleRemove = (providerId: string) => {
    const meta = PROVIDER_METADATA[providerId];
    ApiKeysService.remove(providerId);
    refreshProviders();
    setToast({
      message: `${meta?.name || providerId} removed`,
      type: "success",
    });
  };

  // Quick-edit: select a provider & scroll to form
  const handleEdit = (providerId: string) => {
    setSelectedProvider(providerId);
    // Scroll to the add form at top
    setTimeout(() => {
      addFormRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }, 100);
  };

  // ── Role availability ──
  const roleAvailability = useMemo(
    () => ApiKeysService.getRoleAvailability(),
    [providers],
  );
  const rolesEnabled = Object.values(roleAvailability).filter(
    (r) => r.available,
  ).length;

  return (
    <div className="flex h-full w-full flex-col overflow-hidden">
      {/* ── Toast ── */}
      {toast && (
        <div className="fixed top-6 right-6 z-[100] animate-slide-in-right">
          <div
            className={`flex items-center gap-3 p-4 rounded-xl shadow-lg border ${
              toast.type === "success"
                ? "border-success/30 bg-surface"
                : "border-error/30 bg-surface"
            }`}
            style={{ borderColor: "var(--border-strong)" }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke={
                toast.type === "success" ? "var(--success)" : "var(--error)"
              }
              strokeWidth="2"
              aria-hidden="true"
            >
              {toast.type === "success" ? (
                <>
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                  <polyline points="22 4 12 14.01 9 11.01" />
                </>
              ) : (
                <>
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </>
              )}
            </svg>
            <span className="text-sm font-medium">{toast.message}</span>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 pt-12 pb-16">
          {/* ── Header ── */}
          <header className="mb-8 animate-fade-in-up">
            <div className="flex items-center gap-3 mb-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-xl"
                style={{
                  background:
                    "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                  boxShadow:
                    "0 0 24px color-mix(in srgb, var(--accent) 25%, transparent)",
                }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <div>
                <h1
                  className="text-2xl md:text-3xl font-semibold tracking-tight"
                  style={{ color: "var(--text)" }}
                >
                  API Keys
                </h1>
                <p
                  className="text-sm mt-0.5"
                  style={{ color: "var(--text-subtle)" }}
                >
                  Add your LLM provider API keys. The Model Router automatically
                  picks the best model for each task.
                </p>
              </div>
            </div>
          </header>

          {/* ── Top: Quick Add Card ── */}
          <div ref={addFormRef} className="card p-6 animate-fade-in-up mb-8">
            <h2
              className="text-base font-semibold mb-1"
              style={{ color: "var(--text)" }}
            >
              Add an API key
            </h2>
            <p className="text-xs mb-5" style={{ color: "var(--text-subtle)" }}>
              Select your provider, enter your key, and you're done.
            </p>

            <div className="flex flex-col gap-4">
              {/* Row: Provider + Model */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Provider Select */}
                <div className="relative">
                  <label
                    className="block text-xs font-medium mb-1.5"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    Provider
                  </label>
                  <button
                    ref={providerBtnRef}
                    type="button"
                    onClick={() => setProviderDropdownOpen((o) => !o)}
                    className="glass-input flex h-10 w-full items-center gap-2 rounded-xl px-3 text-sm text-left"
                    style={{
                      color: selectedProvider
                        ? "var(--text-primary)"
                        : "var(--text-quiet)",
                      borderColor: errors.provider
                        ? "var(--error)"
                        : "var(--border-strong)",
                    }}
                  >
                    {selectedProvider && selectedMeta ? (
                      <div className="flex items-center gap-2">
                        <div
                          className="flex h-6 w-6 items-center justify-center rounded-md text-[10px] font-bold text-white"
                          style={{
                            background: selectedMeta.color || "var(--accent)",
                          }}
                        >
                          {selectedMeta.name.charAt(0)}
                        </div>
                        <span>{selectedMeta.name}</span>
                      </div>
                    ) : (
                      <span>Choose a provider...</span>
                    )}
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      className="ml-auto"
                    >
                      <path d="M3 4.5l3 3 3-3" />
                    </svg>
                  </button>
                  {providerDropdownOpen && (
                    <div
                      className="absolute left-0 top-full z-50 mt-1 w-full rounded-xl py-1 shadow-xl"
                      style={{
                        background: "var(--surface-elevated)",
                        border: "1px solid var(--border-strong)",
                        maxHeight: "280px",
                        overflowY: "auto",
                      }}
                    >
                      {PROVIDER_IDS.map((id) => {
                        const meta = PROVIDER_METADATA[id];
                        const configured = providers.find(
                          (p) => p.provider === id,
                        );
                        return (
                          <button
                            key={id}
                            type="button"
                            onClick={() => {
                              setSelectedProvider(id);
                              setProviderDropdownOpen(false);
                              setErrors({});
                            }}
                            className="flex w-full items-center gap-3 px-3 py-2.5 text-sm text-left hover:bg-surface-hover transition-colors"
                            style={{
                              color: "var(--text-primary)",
                              background:
                                selectedProvider === id
                                  ? "color-mix(in srgb, var(--accent) 8%, transparent)"
                                  : "transparent",
                            }}
                          >
                            <div
                              className="flex h-7 w-7 items-center justify-center rounded-lg text-[10px] font-bold text-white flex-shrink-0"
                              style={{
                                background: meta?.color || "var(--accent)",
                              }}
                            >
                              {meta?.name.charAt(0)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-medium truncate">
                                  {meta?.name || id}
                                </span>
                                {configured && (
                                  <span
                                    className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                                    style={{
                                      background:
                                        "color-mix(in srgb, var(--success) 15%, transparent)",
                                      color: "var(--success)",
                                    }}
                                  >
                                    Configured
                                  </span>
                                )}
                              </div>
                              <p
                                className="text-[11px] truncate"
                                style={{ color: "var(--text-subtle)" }}
                              >
                                {meta?.description}
                              </p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                  {errors.provider && (
                    <p
                      className="mt-1 text-xs"
                      style={{ color: "var(--error)" }}
                    >
                      {errors.provider}
                    </p>
                  )}
                </div>

                {/* API Key */}
                <div>
                  <label
                    className="block text-xs font-medium mb-1.5"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    {selectedMeta?.local
                      ? "Local Model (no key needed)"
                      : "API Key"}
                  </label>
                  {selectedMeta?.local ? (
                    <div
                      className="flex h-10 items-center gap-2 rounded-xl px-3 text-sm"
                      style={{
                        background:
                          "color-mix(in srgb, var(--success) 8%, transparent)",
                        border:
                          "1px solid color-mix(in srgb, var(--success) 20%, transparent)",
                        color: "var(--success)",
                      }}
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        aria-hidden="true"
                      >
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 6v6l4 2" />
                      </svg>
                      <span className="text-xs font-medium">
                        Running locally via Ollama
                      </span>
                    </div>
                  ) : (
                    <div className="relative">
                      <Input
                        type="password"
                        value={apiKey}
                        onChange={(e) => {
                          setApiKey(e.target.value);
                          setErrors((prev) => ({ ...prev, apiKey: "" }));
                        }}
                        placeholder={
                          selectedProvider
                            ? `Enter your ${selectedMeta?.name} key`
                            : "Select a provider first"
                        }
                        disabled={!selectedProvider}
                        className={`h-10 ${errors.apiKey ? "border-error" : ""}`}
                      />
                      {errors.apiKey && (
                        <p
                          className="mt-1 text-xs"
                          style={{ color: "var(--error)" }}
                        >
                          {errors.apiKey}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Row: Model + optional Base URL */}
              {selectedProvider && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 animate-fade-in-up">
                  {/* Model quick-pick */}
                  {selectedMeta?.models && (
                    <div>
                      <label
                        className="block text-xs font-medium mb-1.5"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        Model
                      </label>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedMeta.models.map((m) => (
                          <button
                            key={m}
                            type="button"
                            onClick={() => setSelectedModel(m)}
                            className={`text-[11px] px-2.5 py-1 rounded-lg font-mono transition-all ${
                              selectedModel === m
                                ? "bg-accent text-white"
                                : "bg-surface-hover text-text-muted hover:text-text border border-border"
                            }`}
                          >
                            {m}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Base URL (optional) */}
                  <div>
                    <label
                      className="block text-xs font-medium mb-1.5"
                      style={{ color: "var(--text-subtle)" }}
                    >
                      Base URL{" "}
                      <span className="font-normal text-[10px]">
                        (optional)
                      </span>
                    </label>
                    <Input
                      type="url"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.example.com/v1"
                      className="h-10"
                    />
                  </div>
                </div>
              )}

              {/* Save / Get Key */}
              <div className="flex items-center justify-between pt-2">
                {selectedProvider && selectedMeta && !selectedMeta.local && (
                  <a
                    href={selectedMeta.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs underline hover:opacity-80 transition-opacity"
                    style={{ color: "var(--accent)" }}
                  >
                    Get key at {selectedMeta.name} →
                  </a>
                )}
                {!selectedProvider && (
                  <span
                    className="text-xs"
                    style={{ color: "var(--text-quiet)" }}
                  />
                )}
                <Button
                  onClick={handleSave}
                  disabled={!selectedProvider}
                  className="h-10 px-5 gap-2"
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
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  }
                >
                  {selectedProvider &&
                  providers.find((p) => p.provider === selectedProvider)
                    ? "Update"
                    : "Save Key"}
                </Button>
              </div>
            </div>
          </div>

          {/* ── Status Cards ── */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 animate-fade-in-up">
            <div className="card p-4 flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-lg"
                style={{
                  background: "var(--accent-subtle)",
                  color: "var(--accent)",
                }}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  aria-hidden="true"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <div>
                <p
                  className="text-sm font-medium"
                  style={{ color: "var(--text)" }}
                >
                  {providers.length}/{PROVIDER_IDS.length}
                </p>
                <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  Providers configured
                </p>
              </div>
            </div>
            <div className="card p-4 flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-lg"
                style={{
                  background:
                    "color-mix(in srgb, var(--success) 15%, transparent)",
                  color: "var(--success)",
                }}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  aria-hidden="true"
                >
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </div>
              <div>
                <p
                  className="text-sm font-medium"
                  style={{ color: "var(--text)" }}
                >
                  {rolesEnabled}/4
                </p>
                <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  Agent roles active
                </p>
              </div>
            </div>
            <div className="card p-4 flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-lg"
                style={{
                  background:
                    "color-mix(in srgb, var(--info) 15%, transparent)",
                  color: "var(--info)",
                }}
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  aria-hidden="true"
                >
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <div>
                <p
                  className="text-sm font-medium"
                  style={{ color: "var(--text)" }}
                >
                  {providers.length > 0 ? "Ready" : "Not configured"}
                </p>
                <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                  Model Router status
                </p>
              </div>
            </div>
          </div>

          {/* ── Configured Providers List ── */}
          {providers.length > 0 && (
            <div className="animate-fade-in-up">
              <h2
                className="text-sm font-semibold mb-3"
                style={{ color: "var(--text)" }}
              >
                Configured Providers
              </h2>
              <div className="space-y-2">
                {providers.map((p) => {
                  const meta = PROVIDER_METADATA[p.provider];
                  const rolesForProvider = Object.entries(
                    ApiKeysService.getRoleAvailability(),
                  )
                    .filter(([, info]) => info.providers.includes(p.provider))
                    .map(([role]) => role);

                  return (
                    <div
                      key={p.provider}
                      className="card p-3 flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div
                          className="flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold flex-shrink-0 text-white"
                          style={{
                            background: meta?.color || "var(--accent-subtle)",
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
                          onClick={() => handleEdit(p.provider)}
                        >
                          Edit
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
            </div>
          )}

          {/* ── Empty State ── */}
          {providers.length === 0 && (
            <div className="text-center py-12 animate-fade-in-up">
              <div
                className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl"
                style={{
                  background:
                    "color-mix(in srgb, var(--text-quiet) 8%, transparent)",
                }}
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  style={{ color: "var(--text-quiet)" }}
                  aria-hidden="true"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </div>
              <h3
                className="text-sm font-medium mb-1"
                style={{ color: "var(--text)" }}
              >
                No API keys yet
              </h3>
              <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                Select a provider above and add your first key.
              </p>
            </div>
          )}

          {/* ── Footer info ── */}
          {providers.length > 0 && (
            <div
              className="mt-8 flex items-center justify-between"
              style={{
                borderTop: "1px solid var(--border)",
                paddingTop: "1rem",
              }}
            >
              <p className="text-xs" style={{ color: "var(--text-subtle)" }}>
                Keys stored locally in your browser.
              </p>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    navigator.clipboard.writeText(ApiKeysService.exportJson());
                    setToast({
                      message: "Config exported to clipboard",
                      type: "success",
                    });
                  }}
                >
                  Export
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const input = prompt("Paste JSON config:");
                    if (input) {
                      try {
                        ApiKeysService.importJson(input);
                        refreshProviders();
                        setToast({
                          message: "Config imported successfully",
                          type: "success",
                        });
                      } catch (e) {
                        setToast({
                          message:
                            e instanceof Error ? e.message : "Import failed",
                          type: "error",
                        });
                      }
                    }
                  }}
                >
                  Import
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
