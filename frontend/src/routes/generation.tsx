export default function GenerationPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-lg font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
        Automated Project Generator
      </h1>
      <p className="text-sm mb-8" style={{ color: "var(--color-text-secondary)" }}>
        Describe your project and Wren will generate it.
      </p>
      <div className="premium-card p-6">
        <textarea
          className="input mb-4"
          rows={4}
          placeholder="e.g., Build a 3D solar system explorer with Three.js..."
        />
        <button className="accent-button text-xs">
          <span>Generate Project</span>
          <span className="icon-ring">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </span>
        </button>
      </div>
    </div>
  );
}
