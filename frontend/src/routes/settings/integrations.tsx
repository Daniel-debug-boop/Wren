export default function IntegrationsSettingsPage() {
  return (
    <div data-testid="git-settings-screen" className="flex h-full flex-col">
      <div
        className="border-b px-6 py-4"
        style={{ borderColor: "var(--claude-border)" }}
      >
        <h1
          className="text-lg font-medium"
          style={{
            color: "var(--claude-text)",
            fontFamily: "var(--font-serif)",
          }}
        >
          Integrations
        </h1>
        <p className="text-xs" style={{ color: "var(--claude-text-tertiary)" }}>
          Manage your connected git providers
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="flex flex-col gap-3">
          <ProviderCard provider="GitHub" connected={false} />
          <ProviderCard provider="GitLab" connected={false} />
          <ProviderCard provider="Azure DevOps" connected={false} />
        </div>
      </div>
    </div>
  );
}

function ProviderCard({
  provider,
  connected,
}: {
  provider: string;
  connected: boolean;
}) {
  return (
    <div
      className="flex items-center justify-between rounded-xl border p-4"
      style={{ borderColor: "var(--claude-border)" }}
    >
      <div>
        <span
          className="text-sm font-medium"
          style={{ color: "var(--claude-text)" }}
        >
          {provider}
        </span>
      </div>
      <button
        type="button"
        className="rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
        style={{
          background: connected
            ? "var(--claude-border)"
            : "var(--claude-accent)",
          color: connected
            ? "var(--claude-text-secondary)"
            : "var(--claude-canvas)",
        }}
      >
        {connected ? "Disconnect" : "Connect"}
      </button>
    </div>
  );
}
