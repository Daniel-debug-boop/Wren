"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { settingsApi, profilesApi } from "#/api/endpoints";
import type { Profile } from "#/types/api";

/* ── Settings Page ───────────────────────────────────────────────────────────
 * Full LLM configuration with model, base URL, API key, profiles.
 * Loads from backend on mount, saves on form submit.
 */

export default function SettingsPage() {
  const [model, setModel] = useState("openai/gpt-4o-mini");
  const [baseUrl, setBaseUrl] = useState("https://openrouter.ai/api/v1");
  const [apiKey, setApiKey] = useState("");
  const [maxTokens, setMaxTokens] = useState(4096);
  const [temperature, setTemperature] = useState(0.7);
  const [saved, setSaved] = useState(false);
  const [profileName, setProfileName] = useState("");

  // Fetch current settings
  const { data: settings, isLoading, refetch } = useQuery({
    queryKey: ["settings"],
    queryFn: () => settingsApi.get(),
  });

  // Fetch profiles
  const { data: profilesData, refetch: refetchProfiles } = useQuery({
    queryKey: ["profiles"],
    queryFn: () => profilesApi.list(),
  });

  // Save settings
  const saveMutation = useMutation({
    mutationFn: (data: any) => settingsApi.update(data),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      refetch();
    },
  });

  // Create profile
  const createProfileMutation = useMutation({
    mutationFn: (data: { name: string; config: any }) =>
      profilesApi.create(data.name, data.config),
    onSuccess: () => {
      setProfileName("");
      refetchProfiles();
    },
  });

  // Delete profile
  const deleteProfileMutation = useMutation({
    mutationFn: (name: string) => profilesApi.delete(name),
    onSuccess: () => refetchProfiles(),
  });

  // Activate profile
  const activateProfileMutation = useMutation({
    mutationFn: (name: string) => profilesApi.activate(name),
    onSuccess: () => refetchProfiles(),
  });

  // Sync local state with fetched settings
  useEffect(() => {
    if (settings?.llm_config) {
      setModel(settings.llm_config.model || "openai/gpt-4o-mini");
      setBaseUrl(settings.llm_config.base_url || "https://openrouter.ai/api/v1");
      setMaxTokens(settings.llm_config.max_tokens || 4096);
      setTemperature(settings.llm_config.temperature || 0.7);
    }
  }, [settings]);

  const handleSave = () => {
    saveMutation.mutate({
      llm_config: {
        model,
        base_url: baseUrl,
        max_tokens: maxTokens,
        temperature,
      },
    });
  };

  const handleCreateProfile = () => {
    if (!profileName.trim()) return;
    createProfileMutation.mutate({
      name: profileName.trim(),
      config: { model, base_url: baseUrl, api_key: apiKey },
    });
  };

  const profiles: Profile[] = profilesData?.profiles || [];
  const activeProfile = profilesData?.active_profile;

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 rounded bg-white/5" />
          <div className="h-64 rounded-xl bg-white/5" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
            Settings
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-tertiary)" }}>
            Configure your LLM provider and application preferences
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saveMutation.isPending}
          className="accent-button text-xs"
        >
          {saveMutation.isPending ? (
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Saving...
            </span>
          ) : saved ? (
            "✓ Saved!"
          ) : (
            "Save Changes"
          )}
        </button>
      </div>

      {/* LLM Configuration */}
      <div className="card p-6 mb-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
          LLM Configuration
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              Model
            </label>
            <input
              className="input w-full"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. openai/gpt-4o-mini"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              Base URL
            </label>
            <input
              className="input w-full"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="https://openrouter.ai/api/v1"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
              API Key
            </label>
            <input
              className="input w-full"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-or-v1-..."
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Max Tokens
              </label>
              <input
                className="input w-full"
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(Number(e.target.value))}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Temperature
              </label>
              <input
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
      </div>

      {/* Profiles */}
      <div className="card p-6 mb-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text-primary)" }}>
          LLM Profiles
        </h2>
        <p className="text-xs mb-4" style={{ color: "var(--text-tertiary)" }}>
          Save different model configurations and switch between them.
        </p>

        {profiles.length === 0 ? (
          <p className="text-sm py-3 text-center" style={{ color: "var(--text-tertiary)" }}>
            No profiles yet. Create your first profile below.
          </p>
        ) : (
          <div className="space-y-2 mb-4">
            {profiles.map((profile) => (
              <div
                key={profile.name}
                className="flex items-center justify-between rounded-lg px-4 py-3"
                style={{
                  background: "var(--surface)",
                  border: activeProfile === profile.name
                    ? "1px solid var(--accent)"
                    : "1px solid var(--border)",
                }}
              >
                <div>
                  <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                    {profile.name}
                  </span>
                  <span className="ml-2 text-xs" style={{ color: "var(--text-tertiary)" }}>
                    {profile.model}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {activeProfile === profile.name && (
                    <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                      Active
                    </span>
                  )}
                  <button
                    onClick={() => activateProfileMutation.mutate(profile.name)}
                    className="rounded px-2 py-1 text-xs transition-colors hover:bg-white/5"
                    style={{ color: "var(--text-secondary)" }}
                    disabled={activeProfile === profile.name}
                  >
                    Activate
                  </button>
                  <button
                    onClick={() => deleteProfileMutation.mutate(profile.name)}
                    className="rounded px-2 py-1 text-xs text-red-400 transition-colors hover:bg-red-500/10"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <input
            className="input flex-1"
            value={profileName}
            onChange={(e) => setProfileName(e.target.value)}
            placeholder="Profile name..."
          />
          <button
            onClick={handleCreateProfile}
            disabled={!profileName.trim() || createProfileMutation.isPending}
            className="accent-button text-xs"
          >
            {createProfileMutation.isPending ? "Saving..." : "Save as Profile"}
          </button>
        </div>
      </div>
    </div>
  );
}
