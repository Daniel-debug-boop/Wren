import { describe, it, expect, beforeEach } from "vitest";
import { useWorkspaceStore } from "./workspace-store";

describe("workspace store", () => {
  beforeEach(() => {
    useWorkspaceStore.setState({
      conversations: [],
      messages: [],
      activeConversationId: null,
      activeConversation: null,
      agentState: "idle",
      agentThought: "",
      files: [],
      activeFilePath: null,
      activeFileContent: null,
      terminalHistory: [],
    });
  });

  it("creates a conversation and activates it", () => {
    const store = useWorkspaceStore.getState();
    const id = store.createConversation();
    const next = useWorkspaceStore.getState();
    expect(next.activeConversationId).toBe(id);
    expect(next.conversations).toHaveLength(1);
    expect(next.conversations[0].id).toBe(id);
  });

  it("adds a message to the active conversation", () => {
    useWorkspaceStore.getState().createConversation();
    useWorkspaceStore.getState().addMessage({
      id: "user-1",
      role: "user",
      content: "hello",
      timestamp: 1,
    });
    const next = useWorkspaceStore.getState();
    expect(next.messages).toHaveLength(1);
    expect(next.messages[0].content).toBe("hello");
  });

  it("updates a streaming message in place", () => {
    useWorkspaceStore.getState().createConversation();
    const store = useWorkspaceStore.getState();
    store.addMessage({
      id: "assistant-1",
      role: "assistant",
      content: "hel",
      timestamp: 2,
    });
    store.updateMessageContent("assistant-1", "hello world");
    const msg = useWorkspaceStore
      .getState()
      .messages.find((m) => m.id === "assistant-1");
    expect(msg?.content).toBe("hello world");
  });

  it("switches active conversation", () => {
    const s = useWorkspaceStore.getState();
    const first = s.createConversation();
    const second = useWorkspaceStore.getState().createConversation();
    useWorkspaceStore.getState().setActiveConversation(first);
    expect(useWorkspaceStore.getState().activeConversationId).toBe(first);
    useWorkspaceStore.getState().setActiveConversation(second);
    expect(useWorkspaceStore.getState().activeConversationId).toBe(second);
  });

  it("sets files and active file", () => {
    const tree = [{ name: "src", path: "src", type: "directory" as const }];
    useWorkspaceStore.getState().setFiles(tree);
    expect(useWorkspaceStore.getState().files).toEqual(tree);
    useWorkspaceStore.getState().setActiveFile("src/App.tsx", "code()");
    const next = useWorkspaceStore.getState();
    expect(next.activeFilePath).toBe("src/App.tsx");
    expect(next.activeFileContent).toBe("code()");
  });

  it("appends terminal lines", () => {
    useWorkspaceStore.getState().addTerminalLine("$ npm run dev");
    expect(useWorkspaceStore.getState().terminalHistory).toContain(
      "$ npm run dev",
    );
  });

  it("tracks agent state", () => {
    useWorkspaceStore.getState().setAgentState("thinking");
    useWorkspaceStore.getState().setAgentThought("Analyzing…");
    const next = useWorkspaceStore.getState();
    expect(next.agentState).toBe("thinking");
    expect(next.agentThought).toBe("Analyzing…");
  });
});
