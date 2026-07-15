import { type ReactNode } from "react";

interface WorkspaceFeedProps {
  children: ReactNode;
}

export default function WorkspaceFeed({ children }: WorkspaceFeedProps) {
  return (
    <main
      className="relative flex flex-1 flex-col overflow-hidden"
      style={{ background: "var(--glass-bg)" }}
    >
      {/* ── Gradient ambient glow ── */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-64"
        style={{
          background: `radial-gradient(ellipse at 50% 0%, color-mix(in srgb, var(--glass-accent) 3%, transparent) 0%, transparent 70%)`,
        }}
      />

      {/* ── Background ambient dots pattern ── */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `radial-gradient(var(--glass-accent) 1px, transparent 1px)`,
          backgroundSize: `32px 32px`,
        }}
      />

      {/* ── Scrollable Content Area ── */}
      <div className="relative z-10 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl animate-fade-in-up">{children}</div>
      </div>
    </main>
  );
}
