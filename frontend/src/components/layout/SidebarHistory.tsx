interface HistoryItem {
  id: string;
  title: string;
  time: string;
}

interface SidebarHistoryProps {
  items: HistoryItem[];
  activeId: string | null;
  onSelect: (id: string) => void;
}

export default function SidebarHistory({
  items,
  activeId,
  onSelect,
}: SidebarHistoryProps) {
  return (
    <div className="flex-1 overflow-y-auto px-3 py-2">
      <div
        className="mb-2 px-1 text-xs font-semibold uppercase tracking-wider"
        style={{ color: "var(--glass-text-tertiary)" }}
      >
        History
      </div>
      <div className="flex flex-col gap-1">
        {items.map((item, index) => {
          const active = activeId === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className="group flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left press transition-all duration-200 hover:bg-surface-hover/60"
              style={{
                animation: `fade-in-up 0.4s var(--ease-out) both`,
                animationDelay: `${index * 50}ms`,
                background: active
                  ? "color-mix(in srgb, var(--glass-accent) 8%, transparent)"
                  : "transparent",
              }}
            >
              <span
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{
                  background: active
                    ? "var(--glass-accent)"
                    : "var(--glass-border-strong)",
                }}
              />
              <span
                className="flex-1 truncate text-sm font-medium"
                style={{
                  color: active
                    ? "var(--glass-text-primary)"
                    : "var(--glass-text-secondary)",
                }}
              >
                {item.title}
              </span>
              <span
                className="shrink-0 text-[10.5px]"
                style={{ color: "var(--glass-text-tertiary)" }}
              >
                {item.time}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
