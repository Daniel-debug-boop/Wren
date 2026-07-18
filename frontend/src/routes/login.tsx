import { useState, useMemo, useCallback } from "react";
import { useNavigate } from "react-router";
import { Button } from "#/components/ui/Button";
import { Input } from "#/components/ui/Input";
import { Nav } from "#/components/ui/Nav";
import { Footer } from "#/components/ui/Footer";
import ApiKeysService, {
  PROVIDER_METADATA,
} from "#/api/api-keys-service/api-keys-service.api";

const PREFIX_MAP: [string, string][] = [
  ["sk-ant-", "anthropic"],
  ["sk-or-", "openrouter"],
  ["gsk_", "groq"],
  ["pplx-", "perplexity"],
  ["AIza", "google"],
  ["sk-", "openai"],
];

function detectProvider(key: string): string | null {
  const trimmed = key.trim();
  if (!trimmed) return null;
  for (const [prefix, provider] of PREFIX_MAP) {
    if (trimmed.startsWith(prefix)) return provider;
  }
  return "openai";
}

export default function ApiKeySetup() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);

  const existingProviders = useMemo(() => ApiKeysService.getAll(), []);

  const detectedProvider = useMemo(() => {
    if (!apiKey.trim()) return null;
    return detectProvider(apiKey);
  }, [apiKey]);

  const detectedMeta = detectedProvider
    ? PROVIDER_METADATA[detectedProvider]
    : null;

  const isValid = apiKey.trim().length >= 8;

  const handleSave = useCallback(() => {
    const provider = detectedProvider || "openai";
    ApiKeysService.save({
      provider,
      model: PROVIDER_METADATA[provider]?.models?.[0] || "gpt-4o",
      apiKey: apiKey.trim(),
    });
    setSaved(true);
    setTimeout(() => {
      navigate("/conversations/new", { replace: true });
    }, 1200);
  }, [apiKey, detectedProvider, navigate]);

  if (saved) {
    return (
      <div
        className="flex min-h-screen flex-col"
        style={{ background: "var(--bg)" }}
      >
        <Nav />
        <main className="flex-1 flex items-center justify-center p-6">
          <div className="flex flex-col items-center gap-4 animate-fade-in-up">
            <div
              className="flex h-14 w-14 items-center justify-center rounded-full"
              style={{
                background:
                  "linear-gradient(135deg, var(--accent), var(--accent-hover))",
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
              API Key saved!
            </h2>
            <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
              Redirecting to conversations...
            </p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div
      className="flex min-h-screen flex-col"
      style={{ background: "var(--bg)" }}
    >
      <Nav />

      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-md animate-fade-in-up">
          <header className="text-center mb-8">
            <h1
              className="text-2xl font-semibold tracking-tight mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Bring Your Own API Key
            </h1>
            <p className="text-sm" style={{ color: "var(--text-subtle)" }}>
              Paste your LLM provider API key below. It is stored locally and
              never leaves your browser.
            </p>
          </header>

          {existingProviders.length > 0 && (
            <div
              className="mb-6 p-3 rounded-lg text-sm flex items-center gap-2"
              style={{
                background: "var(--accent-subtle)",
                color: "var(--accent)",
                border: "1px solid var(--accent)",
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" />
              </svg>
              <span>
                {existingProviders.length} provider
                {existingProviders.length > 1 ? "s" : ""} already configured. Add
                another or{" "}
                <button
                  type="button"
                  onClick={() => navigate("/conversations/new")}
                  className="underline font-medium"
                >
                  skip to conversations
                </button>
                .
              </span>
            </div>
          )}

          <div className="space-y-4">
            <Input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Paste your API key here..."
              autoFocus
            />

            {detectedMeta && (
              <div
                className="flex items-center gap-3 p-3 rounded-lg animate-fade-in-up"
                style={{
                  background: "var(--surface-hover)",
                  border: "1px solid var(--border)",
                }}
              >
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-lg text-xs font-bold flex-shrink-0"
                  style={{
                    background: detectedMeta.color || "var(--accent)",
                    color: "white",
                  }}
                >
                  {detectedMeta.name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <p
                    className="text-sm font-medium truncate"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Detected: {detectedMeta.name}
                  </p>
                  <p
                    className="text-xs truncate"
                    style={{ color: "var(--text-subtle)" }}
                  >
                    {detectedMeta.description}
                  </p>
                </div>
              </div>
            )}

            {apiKey.trim() && apiKey.trim().length < 8 && (
              <p
                className="text-xs text-center"
                style={{ color: "var(--text-quiet)" }}
              >
                Key must be at least 8 characters
              </p>
            )}

            <Button
              onClick={handleSave}
              className="w-full"
              size="lg"
              disabled={!isValid}
            >
              Get Started
            </Button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
