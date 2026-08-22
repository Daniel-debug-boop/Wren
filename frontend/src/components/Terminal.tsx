import { useEffect, useRef, useCallback, useState } from "react";
import * as xtermModule from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import "@xterm/xterm/css/xterm.css";

const Terminal = xtermModule.Terminal;
type XtermTerminal = InstanceType<typeof Terminal>;

interface TerminalComponentProps {
  wsUrl: string;
  onExit?: (code: number) => void;
  onError?: (message: string) => void;
  className?: string;
}

export function TerminalComponent({
  wsUrl,
  onExit,
  onError,
  className = "",
}: TerminalComponentProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<XtermTerminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [exited, setExited] = useState(false);

  // Initialize terminal
  useEffect(() => {
    if (!containerRef.current) return;

    const term = new Terminal({
      cursorBlink: true,
      cursorStyle: "bar",
      fontSize: 13,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      theme: {
        background: "#0a0a0c",
        foreground: "#f4f4f5",
        cursor: "#f59e0b",
        cursorAccent: "#0a0a0c",
        selectionBackground: "rgba(245, 158, 11, 0.25)",
        selectionForeground: "#f4f4f5",
        black: "#18181b",
        red: "#ef4444",
        green: "#22c55e",
        yellow: "#f59e0b",
        blue: "#3b82f6",
        magenta: "#a855f7",
        cyan: "#06b6d4",
        white: "#f4f4f5",
        brightBlack: "#52525b",
        brightRed: "#f87171",
        brightGreen: "#4ade80",
        brightYellow: "#fbbf24",
        brightBlue: "#60a5fa",
        brightMagenta: "#c084fc",
        brightCyan: "#22d3ee",
        brightWhite: "#fafafa",
      },
      allowProposedApi: true,
      scrollback: 5000,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);

    term.open(containerRef.current);
    fitAddon.fit();

    termRef.current = term;
    fitAddonRef.current = fitAddon;

    // Handle resize
    const handleResize = () => {
      fitAddon.fit();
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            type: "resize",
            cols: term.cols,
            rows: term.rows,
          }),
        );
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      term.dispose();
      termRef.current = null;
      fitAddonRef.current = null;
    };
  }, []);

  // Connect WebSocket
  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setExited(false);
      const term = termRef.current;
      const fitAddon = fitAddonRef.current;
      if (term && fitAddon) {
        fitAddon.fit();
        ws.send(
          JSON.stringify({
            type: "resize",
            cols: term.cols,
            rows: term.rows,
          }),
        );
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        const term = termRef.current;
        if (!term) return;

        switch (msg.type) {
          case "output":
            term.write(msg.data);
            break;
          case "exit":
            setExited(true);
            term.write(
              `\r\n\x1b[33m[Process exited with code ${msg.code}]\x1b[0m\r\n`,
            );
            onExit?.(msg.code);
            break;
          case "error":
            term.write(`\r\n\x1b[31m[Error: ${msg.message}]\x1b[0m\r\n`);
            onError?.(msg.message);
            break;
          case "pong":
            break;
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    ws.onerror = () => {
      setConnected(false);
      onError?.("WebSocket connection failed");
    };
  }, [wsUrl, onExit, onError]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  // Wire up keyboard input
  useEffect(() => {
    const term = termRef.current;
    if (!term) return;

    const disposable = term.onData((data: string) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "input", data }));
      }
    });

    return () => {
      disposable.dispose();
    };
  }, [connected]);

  // Handle restart
  const handleRestart = useCallback(() => {
    const term = termRef.current;
    if (term) {
      term.clear();
    }
    connect();
  }, [connect]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Status bar */}
      <div
        className="flex items-center justify-between px-3 py-1 text-[10px] border-b shrink-0"
        style={{
          background: "var(--bg-surface)",
          borderColor: "var(--border)",
        }}
      >
        <div className="flex items-center gap-2">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connected
                ? "bg-green-400"
                : exited
                  ? "bg-yellow-400"
                  : "bg-red-400"
            }`}
          />
          <span style={{ color: "var(--text-tertiary)" }}>
            {connected ? "Terminal" : exited ? "Exited" : "Connecting..."}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {exited && (
            <button
              onClick={handleRestart}
              className="px-2 py-0.5 rounded text-[10px] hover:bg-white/5 transition-colors"
              style={{ color: "var(--accent)" }}
            >
              Restart
            </button>
          )}
        </div>
      </div>
      {/* Terminal container */}
      <div ref={containerRef} className="flex-1 p-1 overflow-hidden" />
    </div>
  );
}
