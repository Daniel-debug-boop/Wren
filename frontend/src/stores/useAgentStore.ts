import { create } from "zustand";

interface Message {
  id: string;
  role: "user" | "assistant";
  mode: string;
  content: string;
  streaming?: boolean;
}

interface AgentState {
  messages: Message[];
  memory: string[];
  timeline: { time: string; event: string }[];
  tasksRunning: number;
  addMessage: (m: Message) => void;
  appendToken: (id: string, token: string) => void;
  setMemory: (m: string[]) => void;
  pushTimeline: (event: string) => void;
  setTasksRunning: (n: number) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  messages: [],
  memory: [],
  timeline: [],
  tasksRunning: 0,
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  appendToken: (id, token) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + token } : m,
      ),
    })),
  setMemory: (m) => set({ memory: m }),
  pushTimeline: (event) =>
    set((s) => ({
      timeline: [
        ...s.timeline,
        { time: new Date().toLocaleTimeString(), event },
      ],
    })),
  setTasksRunning: (n) => set({ tasksRunning: n }),
}));
