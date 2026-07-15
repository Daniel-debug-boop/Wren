export default function OnboardingPage() {
  return (
    <div
      data-testid="onboarding-page"
      className="flex h-full w-full items-center justify-center p-8"
      style={{ background: "var(--claude-canvas)" }}
    >
      <div className="w-full max-w-lg text-center">
        <h1
          className="text-2xl font-medium"
          style={{
            color: "var(--claude-text)",
            fontFamily: "var(--font-serif)",
          }}
        >
          Welcome to Wren
        </h1>
        <p
          className="mt-2 text-sm"
          style={{ color: "var(--claude-text-secondary)" }}
        >
          Let's get you set up.
        </p>
      </div>
    </div>
  );
}
