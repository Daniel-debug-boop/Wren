import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import SidebarNav from "./SidebarNav";
import SidebarHistory from "./SidebarHistory";
import WorkspaceFooter from "./WorkspaceFooter";
import { useArtifacts } from "./ArtifactsContext";
import { useMode } from "./ModeContext";
import { MODES, type ModeId } from "#/types/mode";
import { ConversationApi } from "#/api/conversation-service/conversation-service.api";
import type { AppConversation } from "#/types/app-conversation";

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "now";
  if (diffMin < 60) return `${diffMin}m`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay === 1) return "Yesterday";
  if (diffDay < 7) return `${diffDay}d`;
  return new Date(dateStr).toLocaleDateString();
}

function toHistoryItems(convs: AppConversation[]) {
  return convs.map((c) => ({
    id: c.id,
    title: c.title || "Untitled conversation",
    time: formatRelativeTime(c.updated_at || c.created_at),
    mode: (c as { mode?: string }).mode,
  }));
}

// Icons for non-dev modes only: plan, code, review, debug, ask
const MODE_ICONS: Record<string, React.ReactNode> = {
  plan: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 1.5v9M1.5 6h9" />
      <circle cx="6" cy="6" r="4.5" />
    </svg>
  ),
  code: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 3l-3 3 3 3M7.5 3l3 3-3 3" />
    </svg>
  ),
  review: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M4 6l1.5 1.5L8 4.5" />
    </svg>
  ),
  debug: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 3.5v2.5l1.5 1.5" />
    </svg>
  ),
  ask: (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="4.5" />
      <path d="M6 4.5v.5M6 7v.5" />
    </svg>
  ),
};

// Simple modes for non-dev users
const VIBE_MODES = ["ask", "code", "plan", "review", "debug"];

export default function Sidebar() {
  const { open: artifactsOpen, toggle: toggleArtifacts } = useArtifacts();
  const { mode, setMode } = useMode();
  const navigate = useNavigate();
  const [activeItem, setActiveItem] = useState<string | null>(null);
  const [historyItems, setHistoryItems] = useState<
    { id: string; title: string; time: string; mode?: string }[]
  >([]);

  useEffect(() => {
    let cancelled = false;
    ConversationApi.listConversations({ sort_order: "updated_at" })
      .then((page) => {
        if (!cancelled) setHistoryItems(toHistoryItems(page.items));
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  return (
    <aside className="glass-sidebar flex w-[240px] shrink-0 flex-col">
      {/* Mode selector row — simplified for non-devs */}
      <div className="flex gap-0.5 px-2 pt-2 pb-1.5">
        {VIBE_MODES.map((id) => {
          const modeDef = MODES.find((m) => m.id === id);
          if (!modeDef) return null;
          const isActive = mode === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => {
                setMode(id as ModeId);
                if (mode !== id) navigate("/");
              }}
              title={modeDef.description}
              className={`flex flex-col items-center gap-0.5 rounded-md px-1.5 py-1 text-[10px] font-medium transition-all duration-200 flex-1 ${
                isActive ? "bg-accent/10 text-accent" : "text-text-tertiary hover:text-text-secondary"
              }`}
            >
              <span className="opacity-80">{MODE_ICONS[id]}</span>
              <span>{modeDef.shortLabel}</span>
            </button>
          );
        })}
      </div>

      {/* Separator */}
      <div className="mx-3 h-px" style={{ background: "var(--glass-border)" }} />

      <SidebarNav />
      <SidebarHistory
        items={historyItems}
        activeId={activeItem}
        onSelect={(id) => {
          setActiveItem(id);
          navigate(`/conversations/${id}`);
        }}
      />
      <WorkspaceFooter
        artifactsOpen={artifactsOpen}
        onToggleArtifacts={toggleArtifacts}
      />
    </aside>
  );
}
