export default function DeviceVerifyPage() {
  return (
    <div
      data-testid="device-verify-page"
      className="flex h-full w-full items-center justify-center p-8"
      style={{ background: "var(--claude-canvas)" }}
    >
      <div className="w-full max-w-md text-center">
        <h1
          className="text-xl font-medium"
          style={{
            color: "var(--claude-text)",
            fontFamily: "var(--font-serif)",
          }}
        >
          Device Verification
        </h1>
        <p
          className="mt-2 text-sm"
          style={{ color: "var(--claude-text-secondary)" }}
        >
          Enter the code shown on your device.
        </p>
      </div>
    </div>
  );
}
