import { useEffect, useRef, useState } from "react";
import { useAgentStore } from "../../stores/useAgentStore";
import { useSocket } from "../../hooks/useSocket";
import { MessageBubble } from "./MessageBubble";

export function ChatPanel() {
  const { messages, addMessage, appendToken, pushTimeline } = useAgentStore();
  const [input, setInput] = useState("");
  const { socket, connected } = useSocket("demo-conv");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = () => {
    if (!input.trim()) return;
    const id = crypto.randomUUID();
    addMessage({ id, role: "user", mode: "vibe-code", content: input });
    pushTimeline(`User: ${input.slice(0, 30)}`);

    const respId = crypto.randomUUID();
    addMessage({
      id: respId,
      role: "assistant",
      mode: "vibe-code",
      content: "",
      streaming: true,
    });
    const tokens = "I'll build that for you. Creating components…".split(" ");
    tokens.forEach((t, i) =>
      setTimeout(() => {
        appendToken(respId, `${t} `);
        if (i === tokens.length - 1) pushTimeline("Assistant responded");
      }, i * 120),
    );
    setInput("");
  };

  return (
    <div className="flex h-1/2 flex-col bg-[#0a0e14]">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-sm text-zinc-600">
            Conversation started. Messages stream here.
          </p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} {...m} />
        ))}
        <div ref={endRef} />
      </div>
      <div className="border-t border-white/5 p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder={connected ? "Message Wren…" : "Connecting…"}
            className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200 outline-none focus:ring-2 focus:ring-cyan-500/30"
          />
          <button
            type="button"
            onClick={send}
            className="rounded-lg bg-cyan-500/20 px-4 py-2 text-sm text-cyan-200 transition hover:bg-cyan-500/30"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
