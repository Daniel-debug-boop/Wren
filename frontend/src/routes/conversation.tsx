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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch conversations list
  const { data: conversations = [], refetch: refetchConvs } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => conversationsApi.list(),
  });

  // Fetch messages for active conversation
  const { data: messages = [], refetch: refetchMessages } = useQuery({
    queryKey: ["messages", activeConvId],
    queryFn: () => (activeConvId ? conversationsApi.messages(activeConvId) : []),
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
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-6xl gap-4 px-6 py-6">
      {/* Sidebar */}
      <div className="w-64 shrink-0">
        <div className="card p-4 h-full flex flex-col">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              Conversations
            </h2>
            <button
              onClick={() => setShowNewConv(true)}
              className="rounded-lg p-1.5 transition-colors hover:bg-white/5"
              style={{ color: "var(--accent)" }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>
          </div>

          {/* New conversation input */}
          {showNewConv && (
            <div className="mb-3 flex gap-1">
              <input
                className="input flex-1 text-xs"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Conversation title..."
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") createMutation.mutate(newTitle || undefined);
                  if (e.key === "Escape") setShowNewConv(false);
                }}
              />
              <button
                onClick={() => createMutation.mutate(newTitle || undefined)}
                className="accent-button text-xs px-2"
              >
                +
              </button>
            </div>
          )}

          {/* Conversation list */}
          <div className="flex-1 space-y-1 overflow-y-auto">
            {conversations.length === 0 && !showNewConv && (
              <p className="py-8 text-center text-xs" style={{ color: "var(--text-tertiary)" }}>
                No conversations yet.
                <br />
                Click + to start one.
              </p>
            )}
            {conversations.map((conv: any) => (
              <div
                key={conv.conversation_id}
                onClick={() => setActiveConvId(conv.conversation_id)}
                className="group flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 transition-all"
                style={{
                  background: activeConvId === conv.conversation_id ? "var(--accent-muted, rgba(139,92,246,0.1))" : "transparent",
                  border: activeConvId === conv.conversation_id ? "1px solid rgba(139,92,246,0.3)" : "1px solid transparent",
                }}
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium" style={{ color: "var(--text-primary)" }}>
                    {conv.title || "Untitled"}
                  </p>
                  <p className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>
                    {conv.created_at ? new Date(conv.created_at).toLocaleDateString() : ""}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteMutation.mutate(conv.conversation_id);
                  }}
                  className="hidden rounded p-1 text-red-400 opacity-0 transition-opacity hover:bg-red-500/10 group-hover:block group-hover:opacity-100"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex flex-1 flex-col">
        <div className="card flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {!activeConvId && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
                    Select a conversation
                  </p>
                  <p className="mt-1 text-xs" style={{ color: "var(--text-tertiary)" }}>
                    or create a new one to start chatting
                  </p>
                </div>
              </div>
            )}
            {activeConvId && messages.length === 0 && (
              <div className="flex h-full items-center justify-center">
                <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                  Start the conversation by sending a message.
                </p>
              </div>
            )}
            {messages.map((msg: any) => (
              <div
                key={msg.id}
                className="flex gap-3"
                style={{ justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}
              >
                <div
                  className="max-w-[75%] rounded-xl px-4 py-2.5"
                  style={{
                    background: msg.role === "user"
                      ? "var(--accent)"
                      : "var(--surface)",
                    border: msg.role === "assistant"
                      ? "1px solid var(--border)"
                      : "none",
                  }}
                >
                  <p className="text-xs leading-relaxed whitespace-pre-wrap" style={{
                    color: msg.role === "user" ? "#fff" : "var(--text-primary)"
                  }}>
                    {msg.content}
                  </p>
                  <p className="mt-1 text-[10px] opacity-50 text-right" style={{
                    color: msg.role === "user" ? "#fff" : "var(--text-tertiary)"
                  }}>
                    {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ""}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          {activeConvId && (
            <div className="border-t p-3" style={{ borderColor: "var(--border)" }}>
              <div className="flex gap-2">
                <input
                  className="input flex-1"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your message... (Shift+Enter for new line)"
                  disabled={sendMutation.isPending}
                />
                <button
                  onClick={handleSend}
                  disabled={!messageInput.trim() || sendMutation.isPending}
                  className="accent-button px-4 text-xs"
                >
                  {sendMutation.isPending ? (
                    <span className="flex items-center gap-2">
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    </span>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
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
