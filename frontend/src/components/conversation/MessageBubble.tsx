import { type Message } from "#/types/conversation";


interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div key={message.id} className="flex justify-center animate-fade-in-up py-2">
        <span
          className="rounded-full px-3 py-1 text-[11px] italic"
          style={{
            background: "color-mix(in srgb, var(--accent) 6%, transparent)",
            color: "var(--text-subtle)",
          }}
        >
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      key={message.id}
      className={`flex flex-col gap-2 animate-fade-in-up ${isUser ? "items-end" : "items-start"}`}
      style={{ maxWidth: "85%" }}
    >
      {/* Mode badge + action tag */}
      {!isUser && (
        <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-subtle)" }}>
          {message.mode && (
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
              style={{
                background: "color-mix(in srgb, var(--accent) 8%, transparent)",
                color: "var(--accent)",
              }}
            >
              {message.mode}
            </span>
          )}
          {message.actionType && (
            <span
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full"
              style={{ background: "var(--accent-subtle)", color: "var(--accent)" }}
            >
              {message.actionTitle || message.actionType}
            </span>
          )}
          {message.isLoading && (
            <span className="flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="h-1.5 w-1.5 rounded-full animate-pulse-glow"
                  style={{ background: "var(--accent)" }}
                />
              ))}
            </span>
          )}
        </div>
      )}

      {/* Bubble */}
      <div
        className={`glass-bubble p-4 ${isUser ? "self-end" : "self-start"}`}
        style={{
          background: isUser
            ? "color-mix(in srgb, var(--accent) 15%, transparent)"
            : "var(--surface)",
          border: isUser
            ? "1px solid color-mix(in srgb, var(--accent) 20%, transparent)"
            : "1px solid var(--border)",
          backdropFilter: "blur(12px)",
        }}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-primary)", fontWeight: 480 }}>
          {message.content}
        </p>
        <span className="text-xs" style={{ color: "var(--text-quiet)" }}>
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
