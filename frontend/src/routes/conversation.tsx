export default function ConversationPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-lg font-semibold mb-6" style={{ color: "var(--color-text-primary)" }}>
        Conversation
      </h1>
      <div className="premium-card p-6">
        <div className="flex flex-col gap-4">
          <div className="rounded-lg p-4" style={{ background: "var(--surface)" }}>
            <p className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
              Start a conversation with Wren to build your project.
            </p>
          </div>
          <div className="flex gap-2">
            <input className="input flex-1" placeholder="Type your message..." />
            <button className="accent-button h-10 px-4 text-xs">Send</button>
          </div>
        </div>
      </div>
    </div>
  );
}
