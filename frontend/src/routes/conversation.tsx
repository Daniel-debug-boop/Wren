"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { conversationsApi } from "#/api/endpoints";

/* ── Conversation Page ───────────────────────────────────────────────────────
 * Full chat interface with message history, send messages,
 * create/switch conversations, and auto-scroll.
 */

export default function ConversationPage() {
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messageInput, setMessageInput] = useState("");
  const [showNewConv, setShowNewConv] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [listOpen, setListOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch conversations list
  const { data: conversations = [], refetch: refetchConvs } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => conversationsApi.list(),
  });

  // Fetch messages for active conversation
  const { data: messages = [], refetch: refetchMessages } = useQuery({
    queryKey: ["messages", activeConvId],
    queryFn: () =>
      activeConvId ? conversationsApi.messages(activeConvId) : [],
    enabled: !!activeConvId,
  });

  // Create conversation
  const createMutation = useMutation({
    mutationFn: (title?: string) => conversationsApi.create(title),
    onSuccess: (conv) => {
      setActiveConvId(conv.conversation_id);
      setShowNewConv(false);
      setNewTitle("");
      refetchConvs();
    },
  });

  // Delete conversation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => conversationsApi.delete(id),
    onSuccess: () => {
      if (activeConvId === deleteMutation.variables) setActiveConvId(null);
      refetchConvs();
    },
  });

  // Send message
  const sendMutation = useMutation({
    mutationFn: ({ id, content }: { id: string; content: string }) =>
      conversationsApi.sendMessage(id, content),
    onSuccess: () => {
      setMessageInput("");
      refetchMessages();
    },
  });

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-select first conversation
  useEffect(() => {
    if (!activeConvId && conversations.length > 0) {
      setActiveConvId(conversations[0].conversation_id);
    }
  }, [conversations, activeConvId]);

  const handleSend = () => {
    if (!messageInput.trim() || !activeConvId) return;
    sendMutation.mutate({ id: activeConvId, content: messageInput.trim() });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="mx-auto flex h-[calc(100dvh-3rem)] max-w-6xl gap-4 px-4 py-4 md:h-dvh md:px-6 md:py-6">
      {/* Sidebar */}
      <div
        className={`${listOpen ? "block" : "hidden"} w-full shrink-0 md:block md:w-64`}
      >
        <div className="card flex h-full flex-col overflow-hidden">
          <div
            className="flex items-center justify-between border-b px-4 py-3"
            style={{ borderColor: "var(--border)" }}
          >
            <h2
              className="font-display text-sm font-semibold"
              style={{ color: "var(--text-primary)" }}
            >
              Conversations
            </h2>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setShowNewConv(true)}
                aria-label="New conversation"
                className="rounded-lg p-1.5 transition-all duration-200 ease-out hover:scale-105"
                style={{
                  background: "var(--accent-subtle)",
                  color: "var(--accent-strong)",
                }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
              {/* Mobile: close list */}
              <button
                onClick={() => setListOpen(false)}
                aria-label="Back to chat"
                className="rounded-lg p-1.5 transition-colors duration-200 ease-out hover:bg-black/5 md:hidden"
                style={{ color: "var(--text-secondary)" }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                >
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* New conversation input */}
          {showNewConv && (
            <div className="animate-fade-in mb-3 flex gap-1 px-3 pt-3">
              <input
                className="input flex-1 text-xs"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Conversation title..."
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter")
                    createMutation.mutate(newTitle || undefined);
                  if (e.key === "Escape") setShowNewConv(false);
                }}
              />
              <button
                onClick={() => createMutation.mutate(newTitle || undefined)}
                className="accent-button !px-2.5 text-xs"
                aria-label="Create conversation"
              >
                +
              </button>
            </div>
          )}

          {/* Conversation list */}
          <div className="flex-1 space-y-1 overflow-y-auto p-3">
            {conversations.length === 0 && !showNewConv && (
              <p
                className="py-8 text-center text-xs leading-relaxed"
                style={{ color: "var(--text-tertiary)" }}
              >
                No conversations yet.
                <br />
                Click + to start one.
              </p>
            )}
            {conversations.map((conv: any) => {
              const isActive = activeConvId === conv.conversation_id;
              return (
                <div
                  key={conv.conversation_id}
                  onClick={() => setActiveConvId(conv.conversation_id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter")
                      setActiveConvId(conv.conversation_id);
                  }}
                  className={`group flex cursor-pointer items-center justify-between rounded-xl border px-3 py-2 transition-all duration-200 ease-out ${
                    isActive ? "" : "hover:bg-black/[0.03]"
                  }`}
                  style={{
                    background: isActive
                      ? "var(--accent-subtle)"
                      : "transparent",
                    borderColor: isActive
                      ? "rgba(217,119,87,0.30)"
                      : "transparent",
                  }}
                >
                  <div className="min-w-0 flex-1">
                    <p
                      className="truncate text-[13px] font-medium"
                      style={{
                        color: isActive
                          ? "var(--accent-strong)"
                          : "var(--text-primary)",
                      }}
                    >
                      {conv.title || "Untitled"}
                    </p>
                    <p
                      className="mt-0.5 text-[10px]"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {conv.created_at
                        ? new Date(conv.created_at).toLocaleDateString()
                        : ""}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteMutation.mutate(conv.conversation_id);
                    }}
                    aria-label={`Delete ${conv.title || "conversation"}`}
                    className="hidden rounded-md p-1 transition-colors duration-150 group-hover:block"
                    style={{ color: "var(--status-error)" }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "rgba(191,66,64,0.08)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "transparent";
                    }}
                  >
                    <svg
                      width="11"
                      height="11"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    >
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div
        className={`${listOpen ? "hidden" : "flex"} min-w-0 flex-1 flex-col md:flex`}
      >
        <div className="card flex flex-1 flex-col overflow-hidden">
          {/* Mobile: switch-conversation affordance */}
          {activeConvId && (
            <button
              onClick={() => setListOpen(true)}
              className="flex items-center justify-between border-b px-4 py-2.5 text-left transition-colors duration-200 ease-out hover:bg-black/[0.03] md:hidden"
              style={{ borderColor: "var(--border)" }}
            >
              <span
                className="truncate text-xs font-medium"
                style={{ color: "var(--text-secondary)" }}
              >
                {conversations.find(
                  (c: any) => c.conversation_id === activeConvId,
                )?.title || "Conversations"}
              </span>
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                style={{ color: "var(--text-muted)" }}
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          )}

          {/* Messages */}
          <div className="flex-1 space-y-4 overflow-y-auto p-4 md:p-6">
            {!activeConvId && (
              <div className="flex h-full items-center justify-center">
                <div className="animate-fade-up text-center">
                  <div
                    className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-2xl"
                    style={{
                      background: "var(--accent-subtle)",
                      color: "var(--accent-strong)",
                    }}
                  >
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    >
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  <p
                    className="font-display text-base font-semibold"
                    style={{ color: "var(--text-primary)" }}
                  >
                    Select a conversation
                  </p>
                  <p
                    className="mt-1 text-xs"
                    style={{ color: "var(--text-tertiary)" }}
                  >
                    or create a new one to start chatting
                  </p>
                </div>
              </div>
            )}
            {activeConvId && messages.length === 0 && (
              <div className="flex h-full items-center justify-center">
                <p
                  className="text-xs"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  Start the conversation by sending a message.
                </p>
              </div>
            )}
            {messages.map((msg: any) => (
              <div
                key={msg.id}
                className="animate-fade-up flex gap-3"
                style={{
                  justifyContent:
                    msg.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 shadow-sm md:max-w-[70%] ${
                    msg.role === "user" ? "rounded-br-md" : "rounded-bl-md"
                  }`}
                  style={{
                    background:
                      msg.role === "user"
                        ? "linear-gradient(135deg, var(--accent), var(--accent-hover))"
                        : "var(--bg-elevated)",
                    border:
                      msg.role === "assistant"
                        ? "1px solid var(--border)"
                        : "none",
                  }}
                >
                  <p
                    className="whitespace-pre-wrap text-[13px] leading-relaxed"
                    style={{
                      color:
                        msg.role === "user" ? "#fffaf7" : "var(--text-primary)",
                    }}
                  >
                    {msg.content}
                  </p>
                  <p
                    className="mt-1 text-right text-[10px]"
                    style={{
                      opacity: 0.55,
                      color:
                        msg.role === "user" ? "#fffaf7" : "var(--text-muted)",
                    }}
                  >
                    {msg.timestamp
                      ? new Date(msg.timestamp).toLocaleTimeString()
                      : ""}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          {activeConvId && (
            <div
              className="border-t p-3 md:p-4"
              style={{
                borderColor: "var(--border)",
                background: "var(--bg-card)",
              }}
            >
              <div className="flex items-end gap-2">
                <input
                  className="input flex-1 !rounded-full !py-2.5"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message..."
                  disabled={sendMutation.isPending}
                />
                <button
                  onClick={handleSend}
                  disabled={!messageInput.trim() || sendMutation.isPending}
                  aria-label="Send message"
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all duration-200 ease-spring enabled:hover:-translate-y-0.5 enabled:hover:shadow-lg disabled:opacity-40"
                  style={{
                    background: "var(--accent-strong)",
                    color: "#fffaf7",
                  }}
                >
                  {sendMutation.isPending ? (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  ) : (
                    <svg
                      width="15"
                      height="15"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
