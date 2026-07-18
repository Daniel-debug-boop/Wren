import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useUIStore } from "../../stores/useUIStore";

export function CommandPalette() {
  const { paletteOpen, setPalette } = useUIStore();
  const [q, setQ] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setPalette(!paletteOpen);
      }
      if (e.key === "Escape") setPalette(false);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [paletteOpen]);

  useEffect(() => {
    if (paletteOpen) inputRef.current?.focus();
  }, [paletteOpen]);

  const COMMANDS = [
    "New Chat",
    "Toggle Terminal",
    "Open File",
    "Deploy",
    "Settings",
  ];

  return (
    <AnimatePresence>
      {paletteOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-32 backdrop-blur-sm"
          onClick={() => setPalette(false)}
        >
          <motion.div
            initial={{ scale: 0.95, y: -10 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: -10 }}
            className="card w-[540px] overflow-hidden rounded-xl shadow-2xl" style={{ borderColor: 'var(--border-strong)' }}
            onClick={(e) => e.stopPropagation()}
          >
            <input
              ref={inputRef}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Type a command or search…"
              className="w-full border-b bg-transparent px-4 py-3 text-sm outline-none"
              style={{
                borderColor: 'var(--border)',
                color: 'var(--text)',
              }}
            />
            <div className="max-h-80 overflow-y-auto p-2">
              {COMMANDS.filter((c) =>
                c.toLowerCase().includes(q.toLowerCase()),
              ).map((c) => (
                <div
                  key={c}
                  className="cursor-pointer rounded-md px-3 py-2 text-sm transition"
                  style={{
                    color: 'var(--text-subtle)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--surface-hover)';
                    e.currentTarget.style.color = 'var(--text)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-subtle)';
                  }}
                >
                  {c}
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
