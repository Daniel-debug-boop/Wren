export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  actions?: AgentAction[];
}

export interface AgentAction {
  type: string;
  thought?: string;
  content?: string;
  timestamp: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  model?: string;
}

export interface LLMSettings {
  apiKey: string;
  model: string;
  baseUrl: string;
  provider: string;
  temperature: number;
  maxTokens: number;
}

export interface AppSettings {
  theme: "dark" | "light" | "system";
  fontSize: number;
  tabSize: number;
  wordWrap: boolean;
  llm: LLMSettings;
}

export type AgentState =
  | "idle"
  | "thinking"
  | "writing_code"
  | "running_command"
  | "awaiting_user_input"
  | "error"
  | "complete";

export interface FileTreeNode {
  name: string;
  path: string;
  type: "file" | "directory";
  children?: FileTreeNode[];
}
