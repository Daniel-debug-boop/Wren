import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface ArtifactData {
  code?: string;
  preview?: string;
  terminal?: string;
  diff?: string;
}

interface ArtifactsContextValue {
  open: boolean;
  toggle: () => void;
  close: () => void;
  setOpen: (open: boolean) => void;
  data: ArtifactData;
  setData: (data: ArtifactData) => void;
  appendTerminal: (text: string) => void;
  setDiff: (diff: string) => void;
  setCode: (code: string) => void;
  setPreview: (preview: string) => void;
}

const EMPTY_DATA: ArtifactData = {};

const ArtifactsContext = createContext<ArtifactsContextValue | null>(null);

export function ArtifactsProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ArtifactData>(EMPTY_DATA);

  const toggle = useCallback(() => setOpen((prev) => !prev), []);
  const close = useCallback(() => {
    setOpen(false);
  }, []);

  const appendTerminal = useCallback((text: string) => {
    setData((prev) => ({
      ...prev,
      terminal: (prev.terminal ?? "") + text + "\n",
    }));
  }, []);

  const setDiff = useCallback((diff: string) => {
    setData((prev) => ({ ...prev, diff }));
  }, []);

  const setCode = useCallback((code: string) => {
    setData((prev) => ({ ...prev, code }));
  }, []);

  const setPreview = useCallback((preview: string) => {
    setData((prev) => ({ ...prev, preview }));
  }, []);

  const value = useMemo(
    () => ({
      open,
      toggle,
      close,
      setOpen,
      data,
      setData,
      appendTerminal,
      setDiff,
      setCode,
      setPreview,
    }),
    [open, data, toggle, close, setOpen, appendTerminal, setDiff, setCode, setPreview],
  );

  return (
    <ArtifactsContext.Provider value={value}>
      {children}
    </ArtifactsContext.Provider>
  );
}

export function useArtifacts(): ArtifactsContextValue {
  const ctx = useContext(ArtifactsContext);
  if (!ctx) {
    throw new Error("useArtifacts must be used within an ArtifactsProvider");
  }
  return ctx;
}
