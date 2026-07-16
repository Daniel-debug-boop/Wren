import { describe, it, expect, vi } from "vitest";
import { render, screen } from "#/test-utils";
import { MessageBubble } from "#/components/conversation/MessageBubble";
import type { Message } from "#/types/conversation";

describe("MessageBubble", () => {
  const baseUserMessage: Message = {
    id: "msg-1",
    role: "user",
    content: "Hello, can you help me build a component?",
    timestamp: new Date("2025-01-01T12:00:00Z"),
  };

  const baseAssistantMessage: Message = {
    id: "msg-2",
    role: "assistant",
    content: "Sure! I can help with that.",
    timestamp: new Date("2025-01-01T12:00:05Z"),
  };

  const systemMessage: Message = {
    id: "msg-3",
    role: "system",
    content: "System notification",
    timestamp: new Date("2025-01-01T12:00:10Z"),
  };

  it("renders user messages correctly", () => {
    render(<MessageBubble message={baseUserMessage} />);
    expect(
      screen.getByText("Hello, can you help me build a component?"),
    ).toBeDefined();
  });

  it("renders assistant messages correctly", () => {
    render(<MessageBubble message={baseAssistantMessage} />);
    expect(screen.getByText("Sure! I can help with that.")).toBeDefined();
  });

  it("renders system messages differently", () => {
    render(<MessageBubble message={systemMessage} />);
    expect(screen.getByText("System notification")).toBeDefined();
  });

  it("shows loading indicator for loading assistant messages", () => {
    const loadingMsg: Message = {
      ...baseAssistantMessage,
      isLoading: true,
    };
    render(<MessageBubble message={loadingMsg} />);
    // Loading indicator elements should be present
    const loadingDots = document.querySelectorAll(".animate-pulse-glow");
    // The component has 3 loading dots when isLoading is true
    expect(loadingDots.length).toBeGreaterThanOrEqual(1);
  });

  it("shows mode badge when mode is provided", () => {
    const modeMsg: Message = {
      ...baseAssistantMessage,
      mode: "plan",
    };
    render(<MessageBubble message={modeMsg} />);
    expect(screen.getByText("plan")).toBeDefined();
  });

  it("shows action type tag when actionType is provided", () => {
    const actionMsg: Message = {
      ...baseAssistantMessage,
      actionType: "run",
      actionTitle: "Running tests",
    };
    render(<MessageBubble message={actionMsg} />);
    expect(screen.getByText("Running tests")).toBeDefined();
  });

  it("displays the timestamp", () => {
    render(<MessageBubble message={baseUserMessage} />);
    // The timestamp should be rendered as locale time string
    const timeStr = baseUserMessage.timestamp.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    expect(screen.getByText(timeStr)).toBeDefined();
  });
});
