export default function ApiKeysPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-lg font-semibold mb-6" style={{ color: "var(--color-text-primary)" }}>
        API Keys
      </h1>
      <div className="premium-card p-6">
        <p className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
          Manage your API keys for LLM providers.
        </p>
      </div>
    </div>
  );
}
