/* eslint-disable i18next/no-literal-string */

import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface TerminalLine {
  id: string;
  type: "input" | "output" | "system";
  text: string;
  timestamp: number;
}

interface TerminalProps {
  lines?: TerminalLine[];
  onCommand?: (command: string) => void;
  height?: string | number;
  readOnly?: boolean;
}

function handleDemoCommand(cmd: string): string {
  const c = cmd.toLowerCase().trim();
  if (c === "help") {
    return [
      "Available commands:",
      "  help       — Show this message",
      "  status     — Show sandbox status",
      "  clear      — Clear terminal",
      "  ls         — List files in workspace",
      "  pwd        — Show current directory",
      "  echo <msg> — Print a message",
    ].join("\n");
  }
  if (c === "status") {
    return "Sandbox: running OK | Memory: 256MB/512MB | CPU: 12%";
  }
  if (c === "clear") {
    return "";
  }
  if (c === "ls") {
    return [
      "src/",
      "tests/",
      "README.md",
      "package.json",
      "tsconfig.json",
    ].join("\n");
  }
  if (c === "pwd") {
    return "/workspace";
  }
  if (c.startsWith("echo ")) {
    return c.slice(5);
  }
  return `Command not found: ${cmd}. Type 'help' for available commands.`;
}

export function Terminal({
  lines: externalLines,
  onCommand,
  height = 280,
  readOnly = false,
}: TerminalProps) {
  const [localLines, setLocalLines] = useState<TerminalLine[]>([
    {
      id: "welcome",
      type: "system",
      text: "Wren Terminal v1.0 — Type 'help' for available commands",
      timestamp: Date.now(),
    },
  ]);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const lines = externalLines ?? localLines;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && input.trim()) {
      const cmd = input.trim();
      const newLine: TerminalLine = {
        id: `cmd-${Date.now()}`,
        type: "input",
        text: `$ ${cmd}`,
        timestamp: Date.now(),
      };

      setLocalLines((prev) => [...prev, newLine]);
      setHistory((prev) => [...prev, cmd]);
      setHistoryIndex(-1);
      setInput("");
      onCommand?.(cmd);

      // Simulate response for demo mode
      if (!onCommand) {
        setTimeout(() => {
          setLocalLines((prev) => [
            ...prev,
            {
              id: `out-${Date.now()}`,
              type: "output",
              text: handleDemoCommand(cmd),
              timestamp: Date.now(),
            },
          ]);
        }, 300);
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (history.length > 0) {
        const newIdx =
          historyIndex < history.length - 1 ? historyIndex + 1 : historyIndex;
        setHistoryIndex(newIdx);
        setInput(history[history.length - 1 - newIdx] || "");
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIndex > 0) {
        const newIdx = historyIndex - 1;
        setHistoryIndex(newIdx);
        setInput(history[history.length - 1 - newIdx] || "");
      } else {
        setHistoryIndex(-1);
        setInput("");
      }
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="glass-strong"
      style={{
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        fontFamily: "var(--font-mono)",
        fontSize: "0.8rem",
        lineHeight: 1.5,
      }}
      role="region"
      aria-label="Terminal"
      aria-live="polite"
    >
      {/* Terminal Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.5rem 1rem",
          borderBottom: "1px solid var(--color-border)",
          background: "rgba(0, 0, 0, 0.2)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <div style={{ display: "flex", gap: "0.375rem" }} aria-hidden="true">
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "var(--color-error)",
              }}
            />
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "var(--color-warning)",
              }}
            />
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "var(--color-success)",
              }}
            />
          </div>
          <span
            style={{
              fontSize: "0.7rem",
              color: "var(--color-text-tertiary)",
              marginLeft: "0.5rem",
            }}
          >
            terminal
          </span>
        </div>
        <span
          style={{
            fontSize: "0.65rem",
            color: "var(--color-text-tertiary)",
            display: "flex",
            alignItems: "center",
            gap: "0.25rem",
          }}
        >
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: "var(--color-success)",
              display: "inline-block",
            }}
            aria-hidden="true"
          />
          connected
        </span>
      </div>

      {/* Terminal Output */}
      <div
        style={{
          padding: "0.75rem 1rem",
          height: `calc(${typeof height === "number" ? `${height}px` : height} - 42px)`,
          overflowY: "auto",
          background: "rgba(0, 0, 0, 0.3)",
        }}
      >
        <AnimatePresence>
          {lines.map((line) => (
            <motion.div
              key={line.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                color:
                  line.type === "system"
                    ? "var(--color-text-tertiary)"
                    : line.type === "input"
                      ? "var(--color-gold-300)"
                      : "var(--color-text-primary)",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                marginBottom: "0.25rem",
              }}
            >
              {line.text}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Input Line */}
        {!readOnly && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              marginTop: "0.25rem",
            }}
          >
            <span style={{ color: "var(--color-gold-400)" }}>$</span>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-label="Terminal input"
              placeholder="Type a command..."
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--color-text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: "0.8rem",
                caretColor: "var(--color-gold-400)",
              }}
            />
          </div>
        )}
        <div ref={endRef} />
      </div>
    </motion.div>
  );
}
