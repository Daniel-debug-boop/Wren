import { useState, useRef, useEffect, type ReactNode } from "react";

type IconProps = { className?: string };

function IcoLogo({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M5 14c0-4 3-7 7-7s7 3 7 7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M9 18h6"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <circle cx="12" cy="11" r="1.6" fill="currentColor" />
    </svg>
  );
}

function IcoPlus({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M12 5v14M5 12h14"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IcoChat({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M4 6.5C4 5.1 5.1 4 6.5 4h11C19 4 20 5.1 20 6.5v7c0 1.4-1.1 2.5-2.5 2.5H9l-4 4v-4H6.5C5.1 16 4 14.9 4 13.5v-7Z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
    </svg>
  );
}

function IcoExplore({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <circle cx="12" cy="12" r="8.2" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="m14.5 9.5-2 5-5 2 2-5 5-2Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IcoAgents({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <rect
        x="4"
        y="7"
        width="7"
        height="6"
        rx="1.6"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <rect
        x="13"
        y="11"
        width="7"
        height="6"
        rx="1.6"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path
        d="M7.5 13v2M16.5 17v1.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IcoCode({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="m9 8-4 4 4 4M15 8l4 4-4 4"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IcoImage({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <rect
        x="4"
        y="5"
        width="16"
        height="14"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <circle cx="9" cy="10" r="1.6" fill="currentColor" />
      <path
        d="m5 17 4.5-4.5L13 16l3-3 3 3.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IcoPanel({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <rect
        x="3.5"
        y="4.5"
        width="17"
        height="15"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path d="M14 5v14" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function IcoSend({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M12 4v16M4 12h16"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IcoArrow({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M5 12h14M13 6l6 6-6 6"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IcoSearch({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <circle cx="11" cy="11" r="6.5" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="m16 16 4 4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

function IcoSpark({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden>
      <path
        d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

const SIDEBAR_BG = "linear-gradient(180deg,#0E0E10 0%,#0B0B0C 100%)";
const PANEL_BG = "rgba(18,18,20,0.72)";
const HAIR = "rgba(255,255,255,0.08)";
const HAIR_STRONG = "rgba(255,255,255,0.12)";
const ACCENT = "#7C7CFF";
const ACCENT_2 = "#9D7BFF";
const TEXT = "#ECECEE";
const MUTED = "#8A8A92";
const FAINT = "#5E5E66";

const history: { id: string; title: string; time: string }[] = [
  { id: "h1", title: "Refactor auth middleware", time: "2m" },
  { id: "h2", title: "API rate limiting", time: "1h" },
  { id: "h3", title: "Database migration plan", time: "3h" },
  { id: "h4", title: "UI component library", time: "Yesterday" },
  { id: "h5", title: "Deployment pipeline", time: "Yesterday" },
  { id: "h6", title: "Performance audit", time: "Mon" },
];

function ChatScroll({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-5 overflow-y-auto px-6 py-8 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.12)_transparent] md:px-10">
      {children}
    </div>
  );
}

function SystemBubble({ children }: { children: ReactNode }) {
  return (
    <div className="flex justify-start">
      <div
        className="max-w-[78%] rounded-2xl rounded-tl-md border px-4 py-3 text-[13.5px] leading-relaxed backdrop-blur-xl md:max-w-[64%]"
        style={{
          background: PANEL_BG,
          borderColor: HAIR,
          color: TEXT,
          boxShadow: "0 8px 30px rgba(0,0,0,0.35)",
        }}
      >
        {children}
      </div>
    </div>
  );
}

function UserBubble({
  children,
  emphasized,
}: {
  children: ReactNode;
  emphasized?: boolean;
}) {
  return (
    <div className="flex justify-end">
      <div
        className="max-w-[78%] rounded-2xl rounded-tr-md border px-4 py-3 text-[13.5px] leading-relaxed backdrop-blur-xl md:max-w-[64%]"
        style={{
          background: emphasized
            ? "linear-gradient(135deg,rgba(124,124,255,0.22),rgba(157,123,255,0.12))"
            : "rgba(255,255,255,0.04)",
          borderColor: emphasized ? "rgba(124,124,255,0.45)" : HAIR,
          color: emphasized ? "#F4F3FF" : TEXT,
          boxShadow: emphasized
            ? "0 10px 40px rgba(124,124,255,0.18)"
            : "0 8px 30px rgba(0,0,0,0.3)",
        }}
      >
        {children}
      </div>
    </div>
  );
}

function Thinking() {
  return (
    <div
      className="flex items-center gap-2.5 text-[13px]"
      style={{ color: MUTED }}
    >
      <span className="relative flex h-4 w-4">
        <span
          className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60"
          style={{ background: ACCENT }}
        />
        <span
          className="relative inline-flex h-4 w-4 rounded-full"
          style={{ background: ACCENT_2 }}
        />
      </span>
      <span className="animate-pulse">Thinking</span>
      <span className="flex gap-0.5">
        <span
          className="h-1 w-1 animate-bounce rounded-full"
          style={{ background: MUTED }}
        />
        <span
          className="h-1 w-1 animate-bounce rounded-full [animation-delay:0.15s]"
          style={{ background: MUTED }}
        />
        <span
          className="h-1 w-1 animate-bounce rounded-full [animation-delay:0.3s]"
          style={{ background: MUTED }}
        />
      </span>
    </div>
  );
}

export default function WrenRedesign() {
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [showArtifacts, setShowArtifacts] = useState(true);
  const [active, setActive] = useState<"chat" | "explore" | "agents">("chat");
  const [messages, setMessages] = useState<
    {
      id: number;
      role: "system" | "user";
      text: string;
      emphasized?: boolean;
    }[]
  >([
    {
      id: 1,
      role: "system",
      text: "I can scaffold components, review code, and run sandboxes. What would you like to build?",
    },
    {
      id: 2,
      role: "user",
      text: "Build a React component for a glassmorphism card",
      emphasized: true,
    },
    {
      id: 3,
      role: "system",
      text: "On it. Drafting a reusable <GlassCard /> with backdrop blur, a hairline border, and a soft elevation shadow. Generating preview now.",
    },
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, thinking]);

  const send = () => {
    const text = input.trim();
    if (!text || thinking) return;
    setMessages((m) => [...m, { id: Date.now(), role: "user", text }]);
    setInput("");
    setThinking(true);
    window.setTimeout(() => {
      setThinking(false);
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "system",
          text: "Received. Synthesizing the implementation and preparing the artifact panel.",
        },
      ]);
    }, 1900);
  };

  const navBtn = (
    key: "chat" | "explore" | "agents",
    label: string,
    Ico: (p: IconProps) => JSX.Element,
  ) => {
    const on = active === key;
    return (
      <button
        onClick={() => setActive(key)}
        className="group flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-[13px] font-medium transition-all duration-200"
        style={{
          background: on ? "rgba(124,124,255,0.12)" : "transparent",
          borderColor: on ? "rgba(124,124,255,0.35)" : "transparent",
          color: on ? "#F4F3FF" : MUTED,
        }}
      >
        <Ico className="h-[18px] w-[18px]" />
        {label}
        {on && (
          <span
            className="ml-auto h-1.5 w-1.5 rounded-full"
            style={{ background: ACCENT_2 }}
          />
        )}
      </button>
    );
  };

  return (
    <div
      className="flex h-screen w-screen overflow-hidden antialiased"
      style={{
        background: "#0B0B0C",
        color: TEXT,
        fontFamily:
          "Inter, 'SF Pro Display', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* SIDEBAR */}
      <aside
        className="flex w-[270px] shrink-0 flex-col border-r"
        style={{ background: SIDEBAR_BG, borderColor: HAIR }}
      >
        <div className="flex items-center gap-2.5 px-5 pb-4 pt-5">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-xl border"
            style={{
              background: "linear-gradient(135deg,#7C7CFF,#9D7BFF)",
              borderColor: "rgba(255,255,255,0.18)",
              color: "#0B0B0C",
            }}
          >
            <IcoLogo className="h-5 w-5" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-[17px] font-semibold tracking-tight">
              Wren
            </span>
            <kbd
              className="rounded-md border px-1.5 py-0.5 text-[10px] font-medium"
              style={{ borderColor: HAIR, color: FAINT }}
            >
              ⌘K
            </kbd>
          </div>
        </div>

        <div className="px-3">
          <button
            className="flex w-full items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-[13px] font-semibold transition-all duration-200 hover:brightness-110"
            style={{
              background:
                "linear-gradient(135deg,rgba(124,124,255,0.9),rgba(157,123,255,0.9))",
              borderColor: "rgba(255,255,255,0.16)",
              color: "#0B0B0C",
              boxShadow: "0 8px 24px rgba(124,124,255,0.25)",
            }}
          >
            <IcoPlus className="h-4 w-4" strokeWidth={2.2} /> New
          </button>
        </div>

        <nav className="mt-5 flex flex-col gap-1 px-3">
          {navBtn("chat", "Chat", IcoChat)}
          {navBtn("explore", "Explore", IcoExplore)}
          {navBtn("agents", "Agents", IcoAgents)}
        </nav>

        <div
          className="px-5 pb-2 pt-6 text-[11px] font-semibold uppercase tracking-[0.12em]"
          style={{ color: FAINT }}
        >
          Recent
        </div>
        <div className="flex-1 overflow-y-auto px-3 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.1)_transparent]">
          {history.map((h) => (
            <button
              key={h.id}
              className="group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[12.5px] transition-colors duration-150 hover:bg-white/[0.04]"
              style={{ color: MUTED }}
            >
              <span
                className="h-1.5 w-1.5 shrink-0 rounded-full"
                style={{ background: HAIR_STRONG }}
              />
              <span className="flex-1 truncate group-hover:text-[#ECECEE]">
                {h.title}
              </span>
              <span className="text-[10.5px]" style={{ color: FAINT }}>
                {h.time}
              </span>
            </button>
          ))}
        </div>

        <div className="border-t p-3" style={{ borderColor: HAIR }}>
          <button
            onClick={() => setShowArtifacts((s) => !s)}
            className="mb-2 flex w-full items-center gap-2.5 rounded-xl border px-3 py-2.5 text-[12.5px] font-medium transition-all duration-200"
            style={{
              background: showArtifacts
                ? "rgba(124,124,255,0.10)"
                : "transparent",
              borderColor: showArtifacts ? "rgba(124,124,255,0.3)" : HAIR,
              color: showArtifacts ? "#F4F3FF" : MUTED,
            }}
          >
            <IcoPanel className="h-[18px] w-[18px]" />
            Show Artifacts
            <span
              className="ml-auto h-[18px] w-[32px] rounded-full border p-0.5 transition-all duration-200"
              style={{
                background: showArtifacts
                  ? "rgba(124,124,255,0.4)"
                  : "rgba(255,255,255,0.06)",
                borderColor: HAIR,
              }}
            >
              <span
                className="block h-3.5 w-3.5 rounded-full transition-transform duration-200"
                style={{
                  background: showArtifacts ? ACCENT_2 : FAINT,
                  transform: showArtifacts
                    ? "translateX(14px)"
                    : "translateX(0)",
                }}
              />
            </span>
          </button>
          <button
            className="flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition-colors duration-200 hover:bg-white/[0.04]"
            style={{ borderColor: HAIR }}
          >
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full text-[12px] font-semibold"
              style={{
                background: "linear-gradient(135deg,#7C7CFF,#9D7BFF)",
                color: "#0B0B0C",
              }}
            >
              DV
            </div>
            <div className="flex-1">
              <div
                className="text-[12.5px] font-medium"
                style={{ color: TEXT }}
              >
                Dev User
              </div>
              <div className="text-[10.5px]" style={{ color: FAINT }}>
                Pro workspace
              </div>
            </div>
            <IcoSpark className="h-4 w-4" style={{ color: MUTED }} />
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="relative flex min-w-0 flex-1 flex-col">
        <header
          className="flex items-center gap-3 border-b px-6 py-3.5 backdrop-blur-xl md:px-10"
          style={{ background: "rgba(11,11,12,0.6)", borderColor: HAIR }}
        >
          <div
            className="flex items-center gap-2 text-[13px] font-medium"
            style={{ color: TEXT }}
          >
            <IcoSpark className="h-4 w-4" style={{ color: ACCENT_2 }} /> Chat
          </div>
          <div
            className="ml-auto flex items-center gap-2 rounded-xl border px-3 py-1.5 text-[12px]"
            style={{
              background: "rgba(255,255,255,0.03)",
              borderColor: HAIR,
              color: MUTED,
            }}
          >
            <IcoSearch className="h-3.5 w-3.5" />
            <span>Search</span>
            <kbd
              className="rounded border px-1 text-[10px]"
              style={{ borderColor: HAIR, color: FAINT }}
            >
              ⌘K
            </kbd>
          </div>
        </header>

        <div className="flex min-h-0 flex-1">
          <section className="flex min-w-0 flex-1 flex-col">
            <div ref={scrollRef} className="min-h-0 flex-1">
              <ChatScroll>
                {messages.map((m) =>
                  m.role === "user" ? (
                    <UserBubble key={m.id} emphasized={m.emphasized}>
                      {m.text}
                    </UserBubble>
                  ) : (
                    <SystemBubble key={m.id}>{m.text}</SystemBubble>
                  ),
                )}
                {thinking && (
                  <div className="flex justify-start">
                    <div
                      className="rounded-2xl rounded-tl-md border px-4 py-3 backdrop-blur-xl"
                      style={{
                        background: PANEL_BG,
                        borderColor: HAIR,
                        boxShadow: "0 8px 30px rgba(0,0,0,0.35)",
                      }}
                    >
                      <Thinking />
                    </div>
                  </div>
                )}
              </ChatScroll>
            </div>

            {/* COMPOSER */}
            <div className="px-6 pb-6 pt-2 md:px-10">
              <div
                className="mx-auto flex max-w-3xl flex-col rounded-2xl border backdrop-blur-2xl"
                style={{
                  background:
                    "linear-gradient(180deg,rgba(20,20,23,0.9),rgba(14,14,16,0.92))",
                  borderColor: HAIR_STRONG,
                  boxShadow:
                    "0 18px 50px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.05)",
                }}
              >
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  rows={1}
                  placeholder="Type a message..."
                  className="max-h-44 min-h-[52px] w-full resize-none bg-transparent px-4 pt-3.5 text-[14px] leading-relaxed outline-none placeholder:text-[#5E5E66]"
                  style={{ color: TEXT }}
                />
                <div className="flex items-center gap-1 px-3 pb-3">
                  <button
                    onClick={() => {}}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border transition-colors duration-150 hover:bg-white/[0.06]"
                    style={{ borderColor: HAIR, color: MUTED }}
                    title="Add context"
                  >
                    <IcoPlus className="h-[18px] w-[18px]" />
                  </button>
                  <button
                    onClick={() => {}}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border transition-colors duration-150 hover:bg-white/[0.06]"
                    style={{ borderColor: HAIR, color: MUTED }}
                    title="Insert code"
                  >
                    <IcoCode className="h-[18px] w-[18px]" />
                  </button>
                  <button
                    onClick={() => {}}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border transition-colors duration-150 hover:bg-white/[0.06]"
                    style={{ borderColor: HAIR, color: MUTED }}
                    title="Upload image"
                  >
                    <IcoImage className="h-[18px] w-[18px]" />
                  </button>

                  <div className="ml-auto flex items-center gap-2">
                    {input.trim() && (
                      <span
                        className="hidden text-[11px] sm:block"
                        style={{ color: FAINT }}
                      >
                        Enter to send
                      </span>
                    )}
                    <button
                      onClick={send}
                      disabled={!input.trim() || thinking}
                      className="flex h-9 items-center gap-1.5 rounded-xl px-4 text-[13px] font-semibold transition-all duration-200 disabled:cursor-not-allowed"
                      style={
                        input.trim() && !thinking
                          ? {
                              background:
                                "linear-gradient(135deg,#7C7CFF,#9D7BFF)",
                              color: "#0B0B0C",
                              boxShadow: "0 8px 22px rgba(124,124,255,0.3)",
                            }
                          : {
                              background: "rgba(255,255,255,0.05)",
                              color: FAINT,
                              border: `1px solid ${HAIR}`,
                            }
                      }
                    >
                      {thinking ? (
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      ) : input.trim() ? (
                        <IcoArrow className="h-4 w-4" />
                      ) : (
                        <IcoSend className="h-4 w-4 rotate-45" />
                      )}
                      {thinking ? "Running" : "Send"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* ARTIFACTS PANEL */}
          {showArtifacts && (
            <aside
              className="hidden w-[360px] shrink-0 flex-col border-l backdrop-blur-xl lg:flex"
              style={{ background: "rgba(14,14,16,0.7)", borderColor: HAIR }}
            >
              <div
                className="flex items-center justify-between border-b px-5 py-3.5"
                style={{ borderColor: HAIR }}
              >
                <div
                  className="flex items-center gap-2 text-[13px] font-medium"
                  style={{ color: TEXT }}
                >
                  <IcoCode className="h-4 w-4" style={{ color: ACCENT_2 }} />{" "}
                  Artifacts
                </div>
                <span
                  className="rounded-md border px-2 py-0.5 text-[10.5px]"
                  style={{ borderColor: HAIR, color: FAINT }}
                >
                  GlassCard.tsx
                </span>
              </div>
              <div className="flex-1 overflow-auto p-4 [scrollbar-width:thin] [scrollbar-color:rgba(255,255,255,0.1)_transparent]">
                <div
                  className="rounded-xl border p-4 text-[12.5px] leading-relaxed backdrop-blur-xl"
                  style={{
                    background: PANEL_BG,
                    borderColor: HAIR,
                    color: "#C9C9D2",
                    fontFamily: "'SF Mono',ui-monospace,Menlo,monospace",
                  }}
                >
                  <div style={{ color: ACCENT_2 }}>export</div>{" "}
                  <div style={{ color: "#9D7BFF" }}>function</div> GlassCard(){" "}
                  {"{"}
                  <div className="pl-4">// backdrop blur + hairline border</div>
                  <div className="pl-4">
                    {'return <div className="glass" />'}
                  </div>
                  {"}"};
                </div>
                <div
                  className="mt-4 flex h-40 items-center justify-center rounded-xl border"
                  style={{
                    background:
                      "linear-gradient(135deg,rgba(124,124,255,0.18),rgba(157,123,255,0.1))",
                    borderColor: "rgba(124,124,255,0.3)",
                  }}
                >
                  <div
                    className="h-24 w-40 rounded-2xl border"
                    style={{
                      background: "rgba(255,255,255,0.06)",
                      borderColor: HAIR_STRONG,
                      boxShadow: "0 12px 40px rgba(0,0,0,0.4)",
                      backdropFilter: "blur(12px)",
                    }}
                  />
                </div>
              </div>
            </aside>
          )}
        </div>
      </main>
    </div>
  );
}
