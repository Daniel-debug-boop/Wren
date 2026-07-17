import { useEffect } from "react";
import { GlassCard } from "../ui/GlassCard";
import { useAgentStore } from "../../stores/useAgentStore";

export function RightSidebar() {
  const { memory, timeline, tasksRunning } = useAgentStore();

  useEffect(() => {
    useAgentStore
      .getState()
      .setMemory([
        "User prefers TypeScript strict mode",
        "Project uses TanStack Query",
        "Deploys to Vercel",
      ]);
  }, []);

  return (
    <div className="flex h-full w-full flex-col gap-3 overflow-y-auto bg-[#0d1117] p-3">
      <Section
        title={`Agent Context${tasksRunning ? ` · ${tasksRunning} running` : ""}`}
      >
        <p className="text-xs text-zinc-500">Autonomous execution ready.</p>
      </Section>
      <Section title="Working Memory">
        <ul className="space-y-1 text-xs text-zinc-400">
          {memory.map((m, i) => (
            <li key={i}>• {m}</li>
          ))}
        </ul>
      </Section>
      <Section title="Review / Diff">
        <p className="text-xs text-zinc-500">No pending changes</p>
      </Section>
      <Section title="Timeline">
        <div className="space-y-2 text-xs text-zinc-500">
          {timeline.length === 0 && <div>No activity yet</div>}
          {timeline.map((t, i) => (
            <div key={i}>
              {t.time} — {t.event}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <GlassCard className="p-3">
      <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
        {title}
      </h3>
      {children}
    </GlassCard>
  );
}
