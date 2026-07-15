import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useConfig } from "#/hooks/query/use-config";
import { Button } from "#/components/ui/Button";
import { Input } from "#/components/ui/Input";
import { Nav } from "#/components/ui/Nav";
import { Footer } from "#/components/ui/Footer";

const PROVIDER_METADATA: Record<
  string,
  {
    name: string;
    description: string;
    url: string;
    local?: boolean;
  }
> = {
  anthropic: {
    name: "Anthropic",
    description: "Claude models",
    url: "https://console.anthropic.com/settings/keys",
  },
  openrouter: {
    name: "OpenRouter",
    description: "Multi-model gateway",
    url: "https://openrouter.ai/keys",
  },
  openai: {
    name: "OpenAI",
    description: "GPT-4o, GPT-4, GPT-3.5",
    url: "https://platform.openai.com/api-keys",
  },
  google: {
    name: "Google AI",
    description: "Gemini models",
    url: "https://aistudio.google.com/app/apikey",
  },
  deepseek: {
    name: "DeepSeek",
    description: "DeepSeek V3, R1, Coder",
    url: "https://platform.deepseek.com/api_keys",
  },
  mistral: {
    name: "Mistral AI",
    description: "Mistral Large, Small",
    url: "https://console.mistral.ai/api-keys",
  },
  groq: {
    name: "Groq",
    description: "Fast Llama, Mixtral, Gemma",
    url: "https://console.groq.com/keys",
  },
  together: {
    name: "Together AI",
    description: "Llama, Mixtral, Qwen",
    url: "https://api.together.xyz/settings/api-keys",
  },
  ollama: {
    name: "Ollama",
    description: "Local models, no API key",
    url: "https://ollama.com/download",
    local: true,
  },
  fireworks: {
    name: "Fireworks AI",
    description: "Fast inference models",
    url: "https://fireworks.ai/api-keys",
  },
  perplexity: {
    name: "Perplexity",
    description: "Sonar models",
    url: "https://www.perplexity.ai/settings/api",
  },
  cohere: {
    name: "Cohere",
    description: "Command R+ models",
    url: "https://dashboard.cohere.com/api-keys",
  },
  azure: {
    name: "Azure OpenAI",
    description: "Enterprise OpenAI",
    url: "https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford",
  },
};

type ProviderConfig = {
  provider: string;
  model: string;
  apiKey?: string;
  baseUrl?: string;
};

function buildProviderList(configProviders?: string[]) {
  const ids = configProviders ?? Object.keys(PROVIDER_METADATA);
  return ids.map((id) => ({
    id,
    ...(PROVIDER_METADATA[id] || {
      name: id.charAt(0).toUpperCase() + id.slice(1),
      description: "Custom provider",
      url: "",
    }),
  }));
}

export default function ProviderSetup() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { data: config } = useConfig();

  const availableProviders = buildProviderList(config?.providers_configured);

  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [savedProviders, setSavedProviders] = useState<ProviderConfig[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load saved providers from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem("wren_llm_providers");
      if (stored) {
        setSavedProviders(JSON.parse(stored));
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (selectedProvider) {
      setSelectedModel("");
      setErrors({});
    }
  }, [selectedProvider]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    const meta = selectedProvider
      ? PROVIDER_METADATA[selectedProvider]
      : undefined;

    if (!selectedProvider) {
      newErrors.provider = "Select a provider";
    }
    if (!selectedModel) {
      newErrors.model = "Enter a model name";
    }
    if (meta && !meta.local && !apiKey.trim()) {
      newErrors.apiKey = "API key is required";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) return;

    const meta = selectedProvider
      ? PROVIDER_METADATA[selectedProvider]
      : undefined;
    const newConfig: ProviderConfig = {
      provider: selectedProvider!,
      model: selectedModel,
      apiKey: meta?.local ? undefined : apiKey.trim(),
      baseUrl: baseUrl.trim() || undefined,
    };

    const updated = [
      ...savedProviders.filter((p) => p.provider !== selectedProvider),
      newConfig,
    ];
    setSavedProviders(updated);
    localStorage.setItem("wren_llm_providers", JSON.stringify(updated));

    setTimeout(() => {
      const next = new URLSearchParams(window.location.search).get("next");
      navigate(next || "/conversations/new", { replace: true });
    }, 1500);
  };

  const handleRemove = (providerId: string) => {
    const updated = savedProviders.filter((p) => p.provider !== providerId);
    setSavedProviders(updated);
    localStorage.setItem("wren_llm_providers", JSON.stringify(updated));
  };

  // Show success state
  if (savedProviders.length > 0 && !selectedProvider) {
    return (
      <div
        className="flex min-h-screen flex-col"
        style={{ background: "var(--bg)" }}
      >
        <Nav />
        <main id="main" className="flex-1 flex flex-col">
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="w-full max-w-md animate-fade-in-up">
              <div className="flex flex-col items-center gap-4 animate-scale-in">
                <div
                  className="flex h-14 w-14 items-center justify-center rounded-full animate-pulse-glow"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                    boxShadow:
                      "0 0 40px color-mix(in srgb, var(--accent) 35%, transparent)",
                  }}
                >
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M20 6L9 17l-5-5"
                      stroke="white"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <h2
                  className="text-lg font-medium"
                  style={{ color: "var(--text-primary)" }}
                >
                  Providers configured!
                </h2>
                <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
                  Redirecting to conversations...
                </p>
              </div>
            </div>
          </div>
        </main>
        <Footer version="1.30.0" />
      </div>
    );
  }

  const selectedMeta = selectedProvider
    ? PROVIDER_METADATA[selectedProvider]
    : undefined;

  return (
    <div
      className="flex min-h-screen flex-col"
      style={{ background: "var(--bg)" }}
    >
      <Nav />

      <main id="main" className="flex-1 flex flex-col">
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-2xl animate-fade-in-up">
            {/* Hero */}
            <header
              className="text-center mb-10 animate-slide-in-right"
              style={{ animationDelay: "100ms" }}
            >
              <div
                className="inline-flex h-14 w-14 items-center justify-center rounded-full mb-4 mx-auto animate-pulse-glow"
                style={{
                  background:
                    "linear-gradient(135deg, var(--accent), var(--accent-hover))",
                  boxShadow:
                    "0 0 32px color-mix(in srgb, var(--accent) 30%, transparent)",
                }}
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  aria-hidden="true"
                >
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <h1
                className="text-3xl md:text-4xl font-semibold tracking-tight mb-2"
                style={{ color: "var(--text-primary)" }}
              >
                Connect your LLM
              </h1>
              <p
                className="text-lg max-w-md mx-auto"
                style={{ color: "var(--text-subtle)" }}
              >
                Choose a provider, pick a model, and add your API key. Keys are
                stored locally and never leave your browser.
              </p>
            </header>

            {/* Provider Cards */}
            <section
              aria-label="Providers"
              className="mb-10 animate-fade-in-up"
              style={{ animationDelay: "200ms" }}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {availableProviders.map((p) => {
                  const active = selectedProvider === p.id;
                  const saved = savedProviders.find(
                    (sp) => sp.provider === p.id,
                  );
                  return (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        setSelectedProvider(p.id);
                        setApiKey("");
                        setBaseUrl("");
                      }}
                      className={`press relative flex flex-col p-4 rounded-xl transition-all duration-200 ${
                        active
                          ? "ring-2 ring-accent bg-accent/5"
                          : "bg-surface hover:bg-surface-hover border border-border"
                      }`}
                      style={{
                        borderColor: active ? "var(--accent)" : "var(--border)",
                      }}
                    >
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div
                          className="flex h-10 w-10 items-center justify-center rounded-lg flex-shrink-0 text-sm font-bold"
                          style={{
                            background: active
                              ? "var(--accent)"
                              : "var(--surface-hover)",
                            color: active ? "white" : "var(--text-primary)",
                          }}
                        >
                          {p.name.charAt(0)}
                        </div>
                        {saved && (
                          <span
                            className="flex-shrink-0 px-2 py-0.5 text-[10px] font-medium rounded-full"
                            style={{
                              background: "var(--success)",
                              color: "white",
                            }}
                          >
                            Configured
                          </span>
                        )}
                      </div>
                      <div className="flex-1 min-h-0">
                        <h3
                          className="font-medium text-sm truncate"
                          style={{
                            color: active
                              ? "var(--accent)"
                              : "var(--text-primary)",
                          }}
                        >
                          {p.name}
                        </h3>
                        <p
                          className="mt-1 text-[11px] truncate"
                          style={{ color: "var(--text-subtle)" }}
                        >
                          {p.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Configuration Form */}
            {selectedProvider && selectedMeta && (
              <section
                aria-label="Configuration"
                className="mb-10 animate-fade-in-up"
                style={{ animationDelay: "300ms" }}
              >
                <div
                  className="card p-5"
                  style={{ borderColor: "var(--border)" }}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold"
                      style={{ background: "var(--accent)", color: "white" }}
                    >
                      {selectedMeta.name.charAt(0)}
                    </div>
                    <div>
                      <h2
                        className="font-medium"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {selectedMeta.name}
                      </h2>
                      <p
                        className="text-xs"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        Configure your connection
                      </p>
                    </div>
                  </div>

                  {/* Model Input */}
                  <div className="mb-4">
                    <label
                      className="block text-xs font-medium mb-1.5"
                      style={{ color: "var(--text-subtle)" }}
                    >
                      Model
                    </label>
                    <Input
                      type="text"
                      value={selectedModel}
                      onChange={(e) => {
                        setSelectedModel(e.target.value);
                        setErrors((prev) => ({ ...prev, model: "" }));
                      }}
                      placeholder="e.g. gpt-4o, claude-3-5-sonnet-20241022"
                      className={`w-full ${errors.model ? "border-error" : ""}`}
                    />
                    {errors.model && (
                      <p className="mt-1.5 text-sm text-error">
                        {errors.model}
                      </p>
                    )}
                  </div>

                  {/* API Key */}
                  {selectedMeta.local ? (
                    <div
                      className="mb-4 p-3 rounded-lg"
                      style={{
                        background: "var(--success-subtle)",
                        border: "1px solid var(--success)",
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          aria-hidden="true"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <path d="M12 6v6l4 2" />
                        </svg>
                        <div>
                          <p
                            className="text-sm font-medium"
                            style={{ color: "var(--success)" }}
                          >
                            Running locally via Ollama
                          </p>
                          <p
                            className="text-xs"
                            style={{ color: "var(--text-subtle)" }}
                          >
                            No API key needed. Ensure Ollama is running on
                            localhost:11434
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="mb-4">
                      <label
                        className="block text-xs font-medium mb-1.5"
                        style={{ color: "var(--text-subtle)" }}
                      >
                        API Key
                      </label>
                      <div className="relative">
                        <Input
                          type="password"
                          value={apiKey}
                          onChange={(e) => {
                            setApiKey(e.target.value);
                            setErrors((prev) => ({ ...prev, apiKey: "" }));
                          }}
                          placeholder={`Enter your ${selectedMeta.name} API key`}
                          className={`w-full ${errors.apiKey ? "border-error" : ""}`}
                        />
                        {apiKey && (
                          <button
                            type="button"
                            onClick={() => {
                              setApiKey("");
                              setErrors((prev) => ({ ...prev, apiKey: "" }));
                            }}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-subtle hover:text-text-primary"
                            aria-label="Clear API key"
                          >
                            <svg
                              width="18"
                              height="18"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              aria-hidden="true"
                            >
                              <line x1="18" y1="6" x2="6" y2="18" />
                              <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                          </button>
                        )}
                      </div>
                      {errors.apiKey && (
                        <p className="mt-1.5 text-sm text-error">
                          {errors.apiKey}
                        </p>
                      )}
                      {selectedMeta.url && (
                        <p
                          className="mt-1.5 text-xs"
                          style={{ color: "var(--text-quiet)" }}
                        >
                          Get your key at{" "}
                          <a
                            href={selectedMeta.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline hover:opacity-80"
                            style={{ color: "var(--accent)" }}
                          >
                            {selectedMeta.name} Console
                          </a>
                        </p>
                      )}
                    </div>
                  )}

                  {/* Base URL (optional) */}
                  <div className="mb-4">
                    <label
                      className="block text-xs font-medium mb-1.5"
                      style={{ color: "var(--text-subtle)" }}
                    >
                      Base URL{" "}
                      <span className="text-[10px] font-normal">
                        (optional)
                      </span>
                    </label>
                    <Input
                      type="url"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      placeholder="https://api.example.com/v1"
                      className="w-full"
                    />
                    <p
                      className="mt-1.5 text-xs"
                      style={{ color: "var(--text-quiet)" }}
                    >
                      Custom endpoint for proxies, self-hosted, or enterprise
                      deployments
                    </p>
                  </div>

                  {/* Save Button */}
                  <Button
                    onClick={handleSave}
                    className="w-full"
                    disabled={!validateForm()}
                  >
                    {savedProviders.some((p) => p.provider === selectedProvider)
                      ? "Update Provider"
                      : "Add Provider"}
                  </Button>
                </div>
              </section>
            )}

            {/* Saved Providers List */}
            {savedProviders.length > 0 && (
              <section
                aria-label="Configured providers"
                className="mb-10 animate-fade-in-up"
                style={{ animationDelay: "400ms" }}
              >
                <h3
                  className="text-sm font-semibold mb-3"
                  style={{ color: "var(--text-primary)" }}
                >
                  Configured Providers ({savedProviders.length})
                </h3>
                <div className="space-y-2">
                  {savedProviders.map((sp) => {
                    const spMeta = PROVIDER_METADATA[sp.provider];
                    return (
                      <div
                        key={sp.provider}
                        className="card p-3 flex items-center justify-between gap-3"
                        style={{ borderColor: "var(--border)" }}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold"
                            style={{
                              background: "var(--accent-subtle)",
                              color: "var(--accent)",
                            }}
                          >
                            {(spMeta?.name || sp.provider).charAt(0)}
                          </div>
                          <div>
                            <p
                              className="font-medium text-sm"
                              style={{ color: "var(--text-primary)" }}
                            >
                              {spMeta?.name || sp.provider}
                            </p>
                            <p className="text-xs text-text-tertiary font-mono">
                              {sp.model}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedProvider(sp.provider);
                              setSelectedModel(sp.model);
                              setApiKey(sp.apiKey || "");
                              setBaseUrl(sp.baseUrl || "");
                            }}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemove(sp.provider)}
                            style={{ color: "var(--error)" }}
                          >
                            Remove
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Continue Button */}
            {savedProviders.length > 0 && (
              <Button
                onClick={() =>
                  navigate("/conversations/new", { replace: true })
                }
                className="w-full"
                size="lg"
              >
                Continue to Conversations →
              </Button>
            )}
          </div>
        </div>
      </main>

      <Footer version="1.30.0" />
    </div>
  );
}
