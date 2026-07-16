import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type ReactNode,
} from "react";
import { DEFAULT_MODE, MODES, type ModeId } from "#/types/mode";
import SettingsService from "#/api/settings-service/settings-service.api";

const LS_KEY = "wren-mode";

function getInitialMode(): ModeId {
  if (typeof window === "undefined") return DEFAULT_MODE;
  try {
    const saved = localStorage.getItem(LS_KEY);
    if (!saved) return DEFAULT_MODE;
    const validModes = MODES.map((m) => m.id);
    if (validModes.includes(saved as ModeId)) return saved as ModeId;
  } catch {
    /* localStorage unavailable */
  }
  return DEFAULT_MODE;
}

interface ModeContextValue {
  mode: ModeId;
  setMode: (m: ModeId) => void;
}

const ModeContext = createContext<ModeContextValue | null>(null);

export function ModeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ModeId>(getInitialMode);

  const setMode = useCallback((m: ModeId) => {
    setModeState(m);
    try {
      localStorage.setItem(LS_KEY, m);
    } catch {
      /* localStorage unavailable */
    }
    // Persist to backend settings for conversation creation
    SettingsService.saveSettings({ mode: m }).catch(() => {
      /* best-effort */
    });
  }, []);

  const value = useMemo(() => ({ mode, setMode }), [mode, setMode]);

  return <ModeContext.Provider value={value}>{children}</ModeContext.Provider>;
}

export function useMode(): ModeContextValue {
  const ctx = useContext(ModeContext);
  if (!ctx) throw new Error("useMode must be used within ModeProvider");
  return ctx;
}
