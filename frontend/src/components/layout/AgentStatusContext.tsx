/* ── AgentStatusContext — Shared agent state for TopBar ── */
import {
  createContext,
  useContext,
  useState,
  useMemo,
  type ReactNode,
} from "react";

interface AgentStatusValue {
  isRunning: boolean;
  taskCount: number;
  elapsedMs: number;
  setRunning: (v: boolean) => void;
  setTaskCount: (n: number) => void;
  setElapsedMs: (n: number) => void;
}

const AgentStatusContext = createContext<AgentStatusValue | null>(null);

export function AgentStatusProvider({ children }: { children: ReactNode }) {
  const [isRunning, setRunning] = useState(false);
  const [taskCount, setTaskCount] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);

  const value = useMemo(
    () => ({
      isRunning,
      taskCount,
      elapsedMs,
      setRunning,
      setTaskCount,
      setElapsedMs,
    }),
    [isRunning, taskCount, elapsedMs],
  );

  return (
    <AgentStatusContext.Provider value={value}>
      {children}
    </AgentStatusContext.Provider>
  );
}

export function useAgentStatus(): AgentStatusValue {
  const ctx = useContext(AgentStatusContext);
  if (!ctx)
    throw new Error("useAgentStatus must be used within AgentStatusProvider");
  return ctx;
}
