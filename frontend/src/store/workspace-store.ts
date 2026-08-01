import { create } from "zustand";
import {
  type Conversation,
  type Message,
  type AgentState,
  type LLMSettings,
  type FileTreeNode,
} from "../types";

interface WorkspaceState {
  // Conversations
  conversations: Conversation[];
  activeConversationId: string | null;
  activeConversation: Conversation | null;

  // Messages
  messages: Message[];

  // Agent state
  agentState: AgentState;
  agentThought: string;

  // UI state
  sidebarOpen: boolean;
  rightPanelOpen: boolean;
  rightPanelTab: "chat" | "terminal" | "timeline";

  // Terminal
  terminalHistory: string[];

  // File tree
  files: FileTreeNode[];
  activeFilePath: string | null;
  activeFileContent: string | null;

  // Settings
  settings: {
    theme: "dark";
    fontSize: number;
    tabSize: number;
    wordWrap: boolean;
  };
  llmSettings: LLMSettings;

  // Actions
  setActiveConversation: (id: string) => void;
  addMessage: (message: Message) => void;
  updateMessageContent: (messageId: string, content: string) => void;
  setAgentState: (state: AgentState) => void;
  setAgentThought: (thought: string) => void;
  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: "chat" | "terminal" | "timeline") => void;
  addTerminalLine: (line: string) => void;
  setFiles: (files: FileTreeNode[]) => void;
  setActiveFile: (path: string, content: string) => void;
  updateSettings: (settings: Partial<WorkspaceState["settings"]>) => void;
  updateLLMSettings: (settings: Partial<LLMSettings>) => void;
  createConversation: () => string;
  addConversation: (conversation: Conversation) => void;
}

const defaultLLMSettings: LLMSettings = {
  apiKey: "",
  model: "gpt-4o",
  baseUrl: "",
  provider: "openai",
  temperature: 0.7,
  maxTokens: 4096,
};

let conversationCounter = 0;

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  activeConversation: null,
  messages: [],
  agentState: "idle",
  agentThought: "",
  sidebarOpen: true,
  rightPanelOpen: true,
  rightPanelTab: "chat",
  terminalHistory: [
    "$ Wren AI workspace ready",
    "$ Type your prompt to start building",
  ],
  files: [],
  activeFilePath: null,
  activeFileContent: null,
  settings: {
    theme: "dark",
    fontSize: 14,
    tabSize: 2,
    wordWrap: true,
  },
  llmSettings: defaultLLMSettings,

  setActiveConversation: (id) => {
    const conv = get().conversations.find((c) => c.id === id);
    if (conv) {
      set({
        activeConversationId: id,
        activeConversation: conv,
        messages: conv.messages,
      });
    }
  },

  addMessage: (message) => {
    set((state) => {
      const messages = [...state.messages, message];
      const conversations = state.conversations.map((c) =>
        c.id === state.activeConversationId
          ? { ...c, messages, updatedAt: Date.now() }
          : c,
      );
      return { messages, conversations };
    });
  },

  // Streaming: replace a message's content (used for token deltas)
  updateMessageContent: (messageId, content) => {
    set((state) => {
      const messages = state.messages.map((m) =>
        m.id === messageId ? { ...m, content } : m,
      );
      const conversations = state.conversations.map((c) =>
        c.id === state.activeConversationId
          ? { ...c, messages, updatedAt: Date.now() }
          : c,
      );
      return { messages, conversations };
    });
  },

  setAgentState: (state) => set({ agentState: state }),
  setAgentThought: (thought) => set({ agentThought: thought }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab }),

  addTerminalLine: (line) =>
    set((s) => ({ terminalHistory: [...s.terminalHistory, line] })),

  setFiles: (files) => set({ files }),
  setActiveFile: (path, content) =>
    set({ activeFilePath: path, activeFileContent: content }),

  updateSettings: (newSettings) =>
    set((s) => ({ settings: { ...s.settings, ...newSettings } })),

  updateLLMSettings: (newSettings) =>
    set((s) => ({ llmSettings: { ...s.llmSettings, ...newSettings } })),

  createConversation: () => {
    const id = `conv-${Date.now()}-${conversationCounter}`;
    conversationCounter += 1;
    const conv: Conversation = {
      id,
      title: `Conversation ${conversationCounter}`,
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set((s) => ({
      conversations: [conv, ...s.conversations],
      activeConversationId: id,
      activeConversation: conv,
      messages: [],
    }));
    return id;
  },

  addConversation: (conversation) =>
    set((s) => ({ conversations: [conversation, ...s.conversations] })),
}));
