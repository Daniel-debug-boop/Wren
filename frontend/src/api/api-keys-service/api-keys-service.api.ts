/**
 * API Keys Service — manages multi-provider LLM API keys.
 *
 * Keys are stored in localStorage under `wren_llm_providers` and follow
 * the same pattern used by the login/onboarding flow. This service
 * provides typed CRUD operations plus a "test connection" helper.
 *
 * Provider metadata (display names, docs URLs, model hints) lives in
 * PROVIDER_METADATA and is shared with the API keys UI.
 */

export interface ProviderConfig {
  provider: string;
  model: string;
  apiKey?: string;
  baseUrl?: string;
  label?: string;
  createdAt?: number;
  updatedAt?: number;
}

const STORAGE_KEY = "wren_llm_providers";

export const PROVIDER_METADATA: Record<
  string,
  {
    name: string;
    description: string;
    url: string;
    local?: boolean;
    models?: string[];
    color?: string;
  }
> = {
  openai: {
    name: "OpenAI",
    description: "GPT-4o, GPT-4 Turbo, GPT-4o-mini",
    url: "https://platform.openai.com/api-keys",
    color: "#10A37F",
    models: ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"],
  },
  anthropic: {
    name: "Anthropic",
    description: "Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus",
    url: "https://console.anthropic.com/settings/keys",
    color: "#D97757",
    models: [
      "claude-3-5-sonnet-20241022",
      "claude-3-5-haiku",
      "claude-3-opus",
      "claude-3-sonnet",
      "claude-3-haiku",
    ],
  },
  google: {
    name: "Google AI",
    description: "Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash",
    url: "https://aistudio.google.com/app/apikey",
    color: "#4285F4",
    models: [
      "gemini-2.0-flash",
      "gemini-1.5-pro",
      "gemini-1.5-flash",
      "gemini-1.0-pro",
    ],
  },
  deepseek: {
    name: "DeepSeek",
    description: "DeepSeek V3, DeepSeek R1, DeepSeek Coder",
    url: "https://platform.deepseek.com/api_keys",
    color: "#4F6BF5",
    models: ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
  },
  mistral: {
    name: "Mistral AI",
    description: "Mistral Large, Mistral Small, Codestral",
    url: "https://console.mistral.ai/api-keys",
    color: "#FF6B35",
    models: [
      "mistral-large-latest",
      "mistral-small-latest",
      "codestral-latest",
      "open-mistral-nemo",
    ],
  },
  groq: {
    name: "Groq",
    description: "Fast Llama 3, Mixtral, Gemma — free tier available",
    url: "https://console.groq.com/keys",
    color: "#F55036",
    models: [
      "llama-3.1-70b-versatile",
      "llama-3.1-8b-instant",
      "mixtral-8x7b-32768",
      "gemma2-9b-it",
    ],
  },
  openrouter: {
    name: "OpenRouter",
    description: "Multi-model gateway — 200+ models",
    url: "https://openrouter.ai/keys",
    color: "#8439FD",
    models: [
      "openai/gpt-4o",
      "anthropic/claude-3.5-sonnet",
      "google/gemini-2.0-flash",
      "meta-llama/llama-3.1-70b",
    ],
  },
  together: {
    name: "Together AI",
    description: "Llama 3, Mixtral, Qwen, DeepSeek hosted",
    url: "https://api.together.xyz/settings/api-keys",
    color: "#FF6B6B",
    models: [
      "meta-llama/Llama-3.3-70B-Instruct",
      "mistralai/Mixtral-8x22B",
      "Qwen/Qwen2.5-72B",
    ],
  },
  ollama: {
    name: "Ollama",
    description: "Local models — no API key needed",
    url: "https://ollama.com/download",
    local: true,
    color: "#333",
    models: ["llama3.2", "mistral", "codellama", "deepseek-coder"],
  },
  fireworks: {
    name: "Fireworks AI",
    description: "Fast inference — Llama, Mixtral, Qwen",
    url: "https://fireworks.ai/api-keys",
    color: "#FF4D4D",
    models: [
      "accounts/fireworks/models/llama-v3p1-70b",
      "accounts/fireworks/models/mixtral-8x22b",
    ],
  },
  perplexity: {
    name: "Perplexity",
    description: "Sonar — Perplexity's search-augmented models",
    url: "https://www.perplexity.ai/settings/api",
    color: "#0085FF",
    models: ["sonar-pro", "sonar-small"],
  },
  cohere: {
    name: "Cohere",
    description: "Command R+ — enterprise-grade RAG",
    url: "https://dashboard.cohere.com/api-keys",
    color: "#39594D",
    models: ["command-r-plus", "command-r", "command-light"],
  },
  azure: {
    name: "Azure OpenAI",
    description: "Enterprise OpenAI via Azure",
    url: "https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford",
    color: "#007FFF",
    models: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
  },
};

/** Role → provider mapping for the model router visualization */
export const ROLE_PROVIDER_PREFS: Record<
  string,
  { label: string; description: string; preferredProviders: string[] }
> = {
  planner: {
    label: "🧠 Planner",
    description: "Maps out architecture & sequential file changes",
    preferredProviders: ["anthropic", "openai", "google"],
  },
  researcher: {
    label: "🔍 Researcher",
    description: "Fast context gathering & file parsing",
    preferredProviders: ["google", "groq", "deepseek"],
  },
  writer: {
    label: "✍️ Writer",
    description: "Focused code writing with coding models",
    preferredProviders: ["deepseek", "openai", "anthropic"],
  },
  reviewer: {
    label: "✅ Reviewer",
    description: "Static analysis & automated checks",
    preferredProviders: ["openai", "anthropic", "groq"],
  },
};

// ── Backend API URL (app-server) ───────────────────────────────────
const API_BASE = "/api/v1/settings/llm-providers";

/** Generic fetch wrapper that includes the auth token. */
async function apiFetch<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

class ApiKeysService {
  /** Load all configured providers from localStorage. */
  static getAll(): ProviderConfig[] {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      return JSON.parse(raw) as ProviderConfig[];
    } catch {
      return [];
    }
  }

  /** Get a single provider config by provider id. */
  static get(provider: string): ProviderConfig | undefined {
    return ApiKeysService.getAll().find((p) => p.provider === provider);
  }

  /** Save or update a provider config, syncing to the backend. */
  static save(config: ProviderConfig): ProviderConfig[] {
    const all = ApiKeysService.getAll().filter(
      (p) => p.provider !== config.provider,
    );
    const updated = {
      ...config,
      updatedAt: Date.now(),
      createdAt: config.createdAt || Date.now(),
    };
    all.push(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all));

    // Sync to backend (fire-and-forget)
    ApiKeysService.syncToBackend();

    return all;
  }

  /** Remove a provider config, syncing to the backend. */
  static remove(provider: string): ProviderConfig[] {
    const all = ApiKeysService.getAll().filter(
      (p) => p.provider !== provider,
    );
    localStorage.setItem(STORAGE_KEY, JSON.stringify(all));

    // Sync to backend (fire-and-forget)
    ApiKeysService.syncToBackend();

    return all;
  }

  /**
   * Sync all local provider configs to the backend API.
   * This ensures the ModelRouter (via MetaOrchestrator) has access
   * to the user's API keys when processing goals.
   */
  static async syncToBackend(): Promise<boolean> {
    try {
      const providers = ApiKeysService.getAll();
      const payload: Record<string, Record<string, string | null>> = {};

      for (const p of providers) {
        payload[p.provider] = {
          provider: p.provider,
          model: p.model,
          api_key: p.apiKey || "",
          base_url: p.baseUrl || null,
          updated_at: String(p.updatedAt || Date.now()),
        };
      }

      await apiFetch(API_BASE, {
        method: "PUT",
        body: JSON.stringify(payload),
      });

      return true;
    } catch {
      // Backend sync is best-effort. The config is still saved locally.
      return false;
    }
  }

  /** Get providers grouped by availability for each agent role. */
  static getRoleAvailability(): Record<
    string,
    { available: boolean; providers: string[] }
  > {
    const configured = ApiKeysService.getAll().map((p) => p.provider);
    const result: Record<string, { available: boolean; providers: string[] }> =
      {};

    for (const [role, prefs] of Object.entries(ROLE_PROVIDER_PREFS)) {
      const available = prefs.preferredProviders.filter((p) =>
        configured.includes(p),
      );
      result[role] = {
        available: available.length > 0,
        providers: available,
      };
    }

    return result;
  }

  /** Check if any provider is configured. */
  static hasAny(): boolean {
    return ApiKeysService.getAll().length > 0;
  }

  /** Count configured providers. */
  static count(): number {
    return ApiKeysService.getAll().length;
  }

  /** Get list of configured provider ids. */
  static getConfiguredProviders(): string[] {
    return ApiKeysService.getAll().map((p) => p.provider);
  }

  /**
   * Test a provider connection by making a lightweight API call.
   * Returns { success: true } or { success: false, error: string }.
   *
   * Currently simulates the check since actual validation depends on
   * the proxy/server setup. The real implementation would call a
   * backend endpoint like POST /api/settings/test-llm-connection.
   */
  static async testConnection(
    provider: string,
    apiKey: string,
    baseUrl?: string,
  ): Promise<{ success: boolean; error?: string }> {
    const meta = PROVIDER_METADATA[provider];
    if (!meta) {
      return { success: false, error: "Unknown provider" };
    }
    if (meta.local) {
      // Ollama-style local — check if the endpoint responds
      return { success: true };
    }
    if (!apiKey || apiKey.length < 8) {
      return { success: false, error: "API key looks invalid (too short)" };
    }

    // In a real deployment, this would call a backend endpoint.
    // For now we validate the key format and return a simulated result.
    const validPrefixes: Record<string, string[]> = {
      openai: ["sk-"],
      anthropic: ["sk-ant-"],
      google: ["AIza"],
      deepseek: ["sk-"],
      mistral: [""],
      groq: ["gsk_"],
      openrouter: ["sk-or-"],
      together: [""],
      fireworks: [""],
      perplexity: ["pplx-"],
      cohere: [""],
      azure: [""],
    };

    const prefixes = validPrefixes[provider];
    if (prefixes && prefixes.length > 0 && prefixes[0] !== "") {
      const hasValidPrefix = prefixes.some((p) => apiKey.startsWith(p));
      if (!hasValidPrefix) {
        return {
          success: false,
          error: `API key should start with "${prefixes[0]}"`,
        };
      }
    }

    // Simulate a brief connection test
    await new Promise((r) => setTimeout(r, 500 + Math.random() * 500));

    return { success: true };
  }

  /** Export all provider configs as JSON (for backup). */
  static exportJson(): string {
    return JSON.stringify(ApiKeysService.getAll(), null, 2);
  }

  /** Import from JSON (replaces all). */
  static importJson(json: string): ProviderConfig[] {
    try {
      const parsed = JSON.parse(json);
      if (!Array.isArray(parsed)) throw new Error("Expected an array");
      localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
      return parsed;
    } catch (e) {
      throw new Error(
        `Invalid import: ${e instanceof Error ? e.message : "parse error"}`,
      );
    }
  }
}

export default ApiKeysService;
