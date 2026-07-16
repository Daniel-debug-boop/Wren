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

// Icons for the three visible modes
const MODE_ICONS: Record<string, React.ReactNode> = {
  "vibe-code": (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4.5 3l-3 3 3 3M7.5 3l3 3-3 3" />
    </svg>
  ),
  autonomous: (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="6" cy="6" r="4.5" />
      <path d="M4.5 5l1.5 1.5L7.5 4" />
      <path d="M3 9c1.5 1.5 4.5 1.5 6 0" />
    </svg>
  ),
  game: (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="1" y="3.5" width="10" height="5" rx="1" />
      <circle cx="3" cy="6" r="0.8" fill="currentColor" />
      <circle cx="9" cy="6" r="0.8" fill="currentColor" />
      <path d="M6 4.5v3M4.5 6h3" />
    </svg>
  ),
};

// Only three visible modes — clean & simple
const VIBE_MODES = ["vibe-code", "autonomous", "game"];

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
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <aside className="glass-sidebar flex w-[240px] shrink-0 flex-col">
      {/* Brand header — smaller, cleaner */}
      <div className="flex items-center justify-between px-4 pt-4 pb-3">
        <div className="flex items-center gap-2.5">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-xl transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] hover:scale-105"
            style={{
              background: "linear-gradient(135deg, var(--accent), var(--accent-hover))",
              boxShadow: "0 0 20px color-mix(in srgb, var(--accent) 25%, transparent)",
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 2 2 7l10 5 10-5-10-5Z" />
              <path d="m2 17 10 5 10-5" />
              <path d="m2 12 10 5 10-5" />
            </svg>
          </div>
          <span className="text-sm font-semibold tracking-tight" style={{ color: "var(--text-primary)" }}>Wren</span>
        </div>
        <button
          type="button"
          onClick={() => navigate("/conversations/new")}
          title="New chat"
          className="press flex h-7 w-7 items-center justify-center rounded-xl transition-all duration-300 hover:bg-white/5 hover:text-accent"
          style={{ color: "var(--text-quiet)" }}
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
            <path d="M8 3v10M3 8h10" />
          </svg>
        </button>
      </div>

      {/* Mode pills */}
      <div className="flex gap-1 px-3 pb-3">
        {VIBE_MODES.map((id) => {
          const modeDef = MODES.find((m) => m.id === id);
          if (!modeDef) return null;
          const isActive = mode === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => { setMode(id as ModeId); if (mode !== id) navigate("/"); }}
              title={modeDef.description}
              className="press flex-1 flex items-center justify-center gap-1.5 rounded-lg py-1.5 text-[10px] font-medium transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
              style={{
                background: isActive ? "var(--accent-subtle)" : "transparent",
                color: isActive ? "var(--accent)" : "var(--text-quiet)",
                border: `1px solid ${isActive ? "color-mix(in srgb, var(--accent) 15%, transparent)" : "transparent"}`,
              }}
            >
              <span className="opacity-80">{MODE_ICONS[id]}</span>
              <span>{modeDef.shortLabel}</span>
            </button>
          );
        })}
      </div>

      {/* Separator */}
      <div className="mx-4 h-px" style={{ background: "linear-gradient(90deg, var(--border), transparent)" }} />

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
