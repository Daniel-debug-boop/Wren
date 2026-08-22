"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { settingsApi, healthApi } from "#/api/endpoints";
import type { Settings } from "#/types/api";
import { SETTINGS_QUERY_KEYS } from "#/hooks/query/query-keys";

/* ── Settings Page ───────────────────────────────────────────────────────────
 * Full LLM configuration (provider, model, base URL, API key, params).
 * Saves to the Wren backend (PUT /settings) and mirrors the API key to
 * localStorage so the WebSocket chat authenticates with it.
 */

const ANTHROPIC_BASE_URL = "https://api.anthropic.com";
const OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1";
const EXAMPLE_MODEL = "openai/gpt-4o";

export default function SettingsPage() {
  const { t } = useTranslation();
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-4o");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [maxTokens, setMaxTokens] = useState(4096);
  const [temperature, setTemperature] = useState(0.7);
  const [saved, setSaved] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Fetch current settings
  const {
    data: settings,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.all,
    queryFn: () => settingsApi.get(),
  });

  // Backend health probe
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: () => healthApi.check(),
  });

  useEffect(() => {
    setBackendOnline(healthData?.status === "ok");
  }, [healthData]);

  // Save settings
  const saveMutation = useMutation({
    mutationFn: (data: Partial<Settings>) => settingsApi.update(data),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      refetch();
    },
  });

  // Sync local state with fetched settings (backend returns flat fields,
  // never the raw key — only api_key_set)
  useEffect(() => {
    if (settings) {
      setProvider(settings.provider || "openai");
      setModel(settings.model || "gpt-4o");
      setBaseUrl(settings.base_url || "");
      setMaxTokens(settings.max_tokens || 4096);
      setTemperature(settings.temperature ?? 0.7);
      if (settings.api_key_set) {
        setApiKey(""); // keep placeholder; key is stored server-side
      }
    }
  }, [settings]);

  const handleSave = () => {
    saveMutation.mutate({
      provider,
      model,
      base_url: baseUrl,
      max_tokens: maxTokens,
      temperature,
      // Only send the key when the user typed a new one
      ...(apiKey ? { api_key: apiKey } : {}),
    });
    if (apiKey) {
      localStorage.setItem("wren_llm_api_key", apiKey);
      setApiKey("");
    }
  };

  let saveButtonContent;
  if (saveMutation.isPending) {
    saveButtonContent = (
      <span className="flex items-center gap-2">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
        {t("SETTINGS$SAVING")}
      </span>
    );
  } else if (saved) {
    saveButtonContent = t("SETTINGS$SAVED");
  } else {
    saveButtonContent = t("SETTINGS$SAVE_CHANGES");
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 md:px-6 md:py-12">
        <div className="space-y-4">
          <div className="skeleton-shimmer h-6 w-32 rounded-lg" />
          <div className="skeleton-shimmer h-64 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl animate-fade-up px-4 py-8 md:px-6 md:py-12">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1
            className="font-display text-xl font-semibold tracking-tight md:text-2xl"
            style={{ color: "var(--text-primary)" }}
          >
            {t("SETTINGS$TITLE")}
          </h1>
          <p
            className="mt-1.5 text-sm leading-relaxed"
            style={{ color: "var(--text-tertiary)" }}
          >
            {t("SETTINGS$SUBTITLE")}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span
            className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
            style={{
              background: backendOnline
                ? "rgba(74,124,89,0.08)"
                : "var(--bg-surface)",
              color: backendOnline
                ? "var(--status-success)"
                : "var(--text-muted)",
            }}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${backendOnline ? "bg-status-success animate-pulse-dot" : "bg-text-muted"}`}
            />
            {backendOnline
              ? t("SETTINGS$BACKEND_CONNECTED")
              : t("SETTINGS$BACKEND_OFFLINE")}
          </span>
          <button
            type="button"
            onClick={handleSave}
            disabled={saveMutation.isPending}
            className="accent-button text-xs"
          >
            {saveButtonContent}
          </button>
        </div>
      </div>

      {/* LLM Configuration */}
      <div className="card p-5 md:p-7" style={{ marginBottom: 24 }}>
        <div className="mb-5 flex items-center gap-2.5">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-lg"
            style={{
              background: "var(--accent-subtle)",
              color: "var(--accent-strong)",
            }}
          >
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <rect x="9" y="9" width="6" height="6" />
              <line x1="9" y1="1" x2="9" y2="4" />
              <line x1="15" y1="1" x2="15" y2="4" />
              <line x1="9" y1="20" x2="9" y2="23" />
              <line x1="15" y1="20" x2="15" y2="23" />
              <line x1="20" y1="9" x2="23" y2="9" />
              <line x1="20" y1="14" x2="23" y2="14" />
              <line x1="1" y1="9" x2="4" y2="9" />
              <line x1="1" y1="14" x2="4" y2="14" />
            </svg>
          </span>
          <h2
            className="font-display text-[15px] font-semibold"
            style={{ color: "var(--text-primary)" }}
          >
            {t("SETTINGS$LLM_CONFIGURATION")}
          </h2>
        </div>
        <div className="grid gap-x-4 gap-y-5 sm:grid-cols-2">
          <div>
            <label
              htmlFor="provider"
              className="mb-1.5 block text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              {t("SETTINGS$PROVIDER")}
            </label>
            <select
              id="provider"
              className="input w-full"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="openai">{t("SETTINGS$PROVIDER_OPENAI")}</option>
              <option value="anthropic">
                {t("SETTINGS$PROVIDER_ANTHROPIC")}
              </option>
              <option value="openrouter">
                {t("SETTINGS$PROVIDER_OPENROUTER")}
              </option>
              <option value="groq">{t("SETTINGS$PROVIDER_GROQ")}</option>
              <option value="google">{t("SETTINGS$PROVIDER_GOOGLE")}</option>
              <option value="mistral">{t("SETTINGS$PROVIDER_MISTRAL")}</option>
            </select>
          </div>
          <div>
            <label
              htmlFor="model"
              className="mb-1.5 block text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              {t("SETTINGS$MODEL")}
            </label>
            <input
              id="model"
              className="input w-full"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. gpt-4o, claude-sonnet-4-20250514"
            />
          </div>
          <div>
            <label
              htmlFor="baseUrl"
              className="mb-1.5 block text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              {t("SETTINGS$BASE_URL")}
            </label>
            <input
              id="baseUrl"
              className="input w-full"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://api.openai.com/v1"
            />
          </div>
          <div>
            <label
              htmlFor="apiKey"
              className="mb-1.5 block text-xs font-medium"
              style={{ color: "var(--text-secondary)" }}
            >
              {t("SETTINGS$API_KEY")}
            </label>
            <input
              id="apiKey"
              className="input w-full"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={
                settings?.api_key_set ? "•••••••• (saved)" : "sk-..."
              }
            />
          </div>
          <div className="grid grid-cols-2 gap-3 sm:col-span-2">
            <div>
              <label
                htmlFor="maxTokens"
                className="mb-1.5 block text-xs font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                {t("SETTINGS$MAX_TOKENS")}
              </label>
              <input
                id="maxTokens"
                className="input w-full"
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
              />
            </div>
            <div>
              <label
                htmlFor="temperature"
                className="mb-1.5 block text-xs font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                {t("SETTINGS$TEMPERATURE")}
              </label>
              <input
                id="temperature"
                className="input w-full"
                type="number"
                min={0}
                max={2}
                step={0.1}
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
              />
            </div>
          </div>
        </div>

        {/* Tips */}
        <div
          className="mt-6 rounded-xl p-4 text-xs leading-relaxed"
          style={{
            background: "var(--bg-surface)",
            color: "var(--text-secondary)",
          }}
        >
          {t("SETTINGS$TIPS_PREFIX")}{" "}
          <code
            className="rounded px-1.5 py-0.5 font-mono text-accent-strong"
            style={{ background: "var(--bg-elevated)" }}
          >
            {ANTHROPIC_BASE_URL}
          </code>
          {t("SETTINGS$TIPS_MIDDLE")}{" "}
          <code
            className="rounded px-1.5 py-0.5 font-mono text-accent-strong"
            style={{ background: "var(--bg-elevated)" }}
          >
            {OPENROUTER_BASE_URL}
          </code>
          {t("SETTINGS$TIPS_MODEL")}{" "}
          <code
            className="rounded px-1.5 py-0.5 font-mono text-accent-strong"
            style={{ background: "var(--bg-elevated)" }}
          >
            {EXAMPLE_MODEL}
          </code>
          {t("SETTINGS$TIPS_SUFFIX")}
        </div>
      </div>
    </div>
  );
}
