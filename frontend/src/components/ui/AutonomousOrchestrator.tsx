/* ── Agent Activity Panel (Gemini-style sidebar) ──
 *  Non-coder friendly show what the agent is doing without cluttering the chat.
 */
import { useEffect, useState, useCallback, useRef } from "react";
import {
  OrchestrationApi,
  openOrchestrationWs,
  type SubTaskItem,
  type WorkingMemoryEntry,
  type ManagerStatus,
  type LessonItem,
  type WsStateMessage,
} from "#/api/orchestration-service/orchestration-service.api";

interface Props {
  goal: string;
  conversationId?: string;
}

function RelTime({ ts }: { ts: number }) {
  const diff = Date.now() - ts * 1000;
  const label =
    diff < 60_000
      ? "now"
      : diff < 3600_000
        ? `${Math.floor(diff / 60_000)}m`
        : `${Math.floor(diff / 3600_000)}h`;
  return (
    <span style={{ color: "var(--text-quiet)", fontSize: 10 }}>{label}</span>
  );
}

function Section({
  title,
  open,
  onToggle,
  children,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div style={{ borderBottom: "1px solid var(--border)" }}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-3 py-2 text-left press"
        style={{ color: "var(--text-primary)" }}
      >
        <span className="text-[10px] font-semibold uppercase tracking-wider">
          {title}
        </span>
        <span
          style={{
            color: "var(--text-quiet)",
            fontSize: 10,
            transform: open ? "rotate(180deg)" : "none",
            transition: "transform 0.2s",
          }}
        >
          ▾
        </span>
      </button>
      {open && (
        <div className="px-3 pb-2 flex flex-col gap-1.5">{children}</div>
      )}
    </div>
  );
}

function TaskRow({ task }: { task: SubTaskItem }) {
  const meta =
    task.status === "running"
      ? { label: "Running", color: "var(--accent)" }
      : task.status === "completed"
        ? { label: "Done", color: "var(--success)" }
        : task.status === "failed"
          ? { label: "Failed", color: "var(--error)" }
          : { label: "Pending", color: "var(--text-quiet)" };
  return (
    <div
      className="flex items-center gap-2 py-0.5"
      style={{ fontSize: 11, color: "var(--text-subtle)" }}
    >
      <span
        className="flex h-3 w-3 shrink-0 items-center justify-center rounded-full"
        style={{
          background: `color-mix(in srgb, ${meta.color} 15%, transparent)`,
          color: meta.color,
          fontSize: 7,
        }}
      >
        {task.status === "running"
          ? "◉"
          : task.status === "completed"
            ? "✓"
            : task.status === "failed"
              ? "✗"
              : "○"}
      </span>
      <span className="truncate flex-1">{task.name}</span>
      <span style={{ color: meta.color, fontSize: 9 }}>{meta.label}</span>
    </div>
  );
}

export function AutonomousOrchestrator({
  goal,
  conversationId: convIdProp,
}: Props) {
  const cid = convIdProp || "default";
  const [status, setStatus] = useState<ManagerStatus | null>(null);
  const [memories, setMemories] = useState<WorkingMemoryEntry[]>([]);
  const [lessons, setLessons] = useState<LessonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sections, setSections] = useState<Record<string, boolean>>({
    running: true,
    pending: false,
    done: false,
    info: false,
  });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const toggle = (key: string) =>
    setSections((s) => ({ ...s, [key]: !s[key] }));

  const apply = useCallback((msg: WsStateMessage) => {
    setStatus(msg.manager);
    if (msg.memory) setMemories(msg.memory.entries || []);
    if (msg.lessons) setLessons(msg.lessons);
  }, []);

  useEffect(() => {
    setLoading(true);
    let ws: WebSocket | null = null;
    try {
      ws = openOrchestrationWs(cid, (m) => {
        apply(m);
        setLoading(false);
      });
      wsRef.current = ws;
    } catch {
      /* fallback */
    }
    let mounted = true;
    (async () => {
      try {
        await OrchestrationApi.managerInit(goal, cid);
        const [s, m, l] = await Promise.all([
          OrchestrationApi.getManagerStatus(cid),
          OrchestrationApi.getMemory(undefined, 20, cid),
          OrchestrationApi.getLessons(5, cid),
        ]);
        if (!mounted) return;
        setStatus(s);
        setMemories(m.entries);
        setLessons(l.lessons);
      } catch {
        /* */
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    pollRef.current = setInterval(async () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;
      try {
        const [s, m, l] = await Promise.all([
          OrchestrationApi.getManagerStatus(cid),
          OrchestrationApi.getMemory(undefined, 20, cid),
          OrchestrationApi.getLessons(5, cid),
        ]);
        setStatus(s);
        setMemories(m.entries);
        setLessons(l.lessons);
      } catch {
        /* */
      }
    }, 5000);
    return () => {
      mounted = false;
      if (pollRef.current) clearInterval(pollRef.current);
      if (ws) ws.close();
    };
  }, [goal, cid, apply]);

  const counts = status?.status_counts || {};
  const total = status?.total || 0;
  const progress = total
    ? Math.round(
        (((counts.completed || 0) + (counts.failed || 0)) / total) * 100,
      )
    : 0;
  const allTasks = status?.all || [];
  const runningTasks = allTasks.filter((t) => t.status === "running");
  const pendingTasks = allTasks.filter((t) => t.status === "pending");
  const completedTasks = allTasks.filter((t) => t.status === "completed");
  const failedTasks = allTasks.filter((t) => t.status === "failed");

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex items-center gap-2">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="inline-block h-1.5 w-1.5 rounded-full"
              style={{ background: "var(--accent)" }}
            >
              <style>{`@keyframes p${i}{0%,100%{opacity:0.3}50%{opacity:1}}`}</style>
              <span style={{ animation: `p${i} 1s infinite ${i * 0.2}s` }} />
            </span>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ fontSize: 12 }}>
      {/* Goal header */}
      <div
        className="px-3 py-2.5"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <p
          className="text-xs font-semibold truncate"
          style={{ color: "var(--text-primary)" }}
        >
          {goal.slice(0, 80)}
        </p>
        <div
          className="mt-1.5 h-1 rounded-full overflow-hidden"
          style={{ background: "var(--border)" }}
        >
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${progress}%`,
              background:
                "linear-gradient(90deg, var(--accent), var(--accent-hover))",
            }}
          />
        </div>
        <div className="flex gap-2 mt-1.5">
          {[
            {
              label: "Run",
              count: counts.running || 0,
              color: "var(--accent)",
            },
            {
              label: "Done",
              count: counts.completed || 0,
              color: "var(--success)",
            },
            { label: "Fail", count: counts.failed || 0, color: "var(--error)" },
          ].map((s) => (
            <span key={s.label} style={{ fontSize: 9, color: s.color }}>
              {s.label} {s.count}
            </span>
          ))}
        </div>
      </div>

      {/* Running tasks */}
      {runningTasks.length > 0 && (
        <Section
          title="Running"
          open={sections.running}
          onToggle={() => toggle("running")}
        >
          {runningTasks.map((t) => (
            <TaskRow key={t.id} task={t} />
          ))}
        </Section>
      )}

      {/* Pending tasks */}
      {pendingTasks.length > 0 && (
        <Section
          title="Pending"
          open={sections.pending}
          onToggle={() => toggle("pending")}
        >
          {pendingTasks.map((t) => (
            <TaskRow key={t.id} task={t} />
          ))}
        </Section>
      )}

      {/* Completed/Failed */}
      {(completedTasks.length > 0 || failedTasks.length > 0) && (
        <Section
          title="Tasks"
          open={sections.done}
          onToggle={() => toggle("done")}
        >
          {[...completedTasks.slice(-3), ...failedTasks].map((t) => (
            <TaskRow key={t.id} task={t} />
          ))}
          {(completedTasks.length > 3 || failedTasks.length > 3) && (
            <span style={{ fontSize: 9, color: "var(--text-quiet)" }}>
              +
              {Math.max(0, completedTasks.length - 3) +
                Math.max(0, failedTasks.length - 3)}{" "}
              more
            </span>
          )}
        </Section>
      )}

      {/* Working Memory */}
      {memories.length > 0 && (
        <Section
          title="Working Memory"
          open={sections.info}
          onToggle={() => toggle("info")}
        >
          {memories.slice(-5).map((e) => (
            <div
              key={e.id}
              className="rounded-md px-2.5 py-2"
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.04)",
              }}
            >
              <div className="flex items-start gap-2">
                <span
                  className="mt-0.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{ background: "var(--accent)" }}
                />
                <span
                  className="flex-1 text-[10px] leading-relaxed"
                  style={{ color: "var(--text-subtle)" }}
                >
                  {e.content}
                </span>
              </div>
              <div className="mt-1 flex justify-end">
                <RelTime ts={e.timestamp} />
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* Lessons Learned */}
      {lessons.length > 0 && (
        <Section
          title="Lessons Learned"
          open={sections.info}
          onToggle={() => toggle("info")}
        >
          {lessons.slice(-4).map((l) => (
            <div
              key={l.id}
              className="rounded-md px-2.5 py-2"
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.04)",
              }}
            >
              <div className="flex items-start gap-2">
                <span
                  className="mt-0.5 shrink-0 text-[10px]"
                  style={{ color: "var(--success)" }}
                >
                  ✦
                </span>
                <span
                  className="flex-1 text-[10px] leading-relaxed"
                  style={{ color: "var(--text-subtle)" }}
                >
                  {l.content}
                </span>
              </div>
              <div className="mt-1 flex justify-end">
                <RelTime ts={l.timestamp} />
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* Empty state */}
      {allTasks.length === 0 &&
        memories.length === 0 &&
        lessons.length === 0 && (
          <div
            className="flex flex-col items-center justify-center py-8 gap-2"
            style={{ color: "var(--text-quiet)", fontSize: 11 }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <p>Waiting for activity...</p>
          </div>
        )}
    </div>
  );
}
