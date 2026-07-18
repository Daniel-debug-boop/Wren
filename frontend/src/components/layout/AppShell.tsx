import { motion, AnimatePresence } from "framer-motion";
import { useUIStore } from "../../stores/useUIStore";
import { useResizable } from "../../hooks/useResizable";
import { TopBar } from "./TopBar";
import { LeftSidebar } from "./LeftSidebar";
import { RightSidebar } from "./RightSidebar";
import { BottomBar } from "./BottomBar";
import { ChatPanel } from "../chat/ChatPanel";
import { CodeEditor } from "../editor/CodeEditor";
import { CommandPalette } from "../palette/CommandPalette";

function ResizeHandle({
  axis,
  onPointerDown,
  cursor,
}: {
  axis: "x" | "y";
  onPointerDown: (e: React.PointerEvent) => void;
  cursor: string;
}) {
  return (
    <div
      onPointerDown={onPointerDown}
      className={`shrink-0 transition ${
        axis === "x" ? "w-1 cursor-col-resize" : "h-1 cursor-row-resize"
      }`}
      style={{
        cursor,
        background: 'var(--border)',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--accent)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'var(--border)'; }}
    />
  );
}

export function AppShell() {
  const {
    leftOpen,
    rightOpen,
    bottomOpen,
    leftWidth,
    rightWidth,
    bottomHeight,
    setLeftWidth,
    setRightWidth,
    setBottomHeight,
  } = useUIStore();
  const leftResize = useResizable({
    axis: "x",
    min: 200,
    max: 480,
    value: leftWidth,
    onChange: setLeftWidth,
  });
  const rightResize = useResizable({
    axis: "x",
    min: 280,
    max: 560,
    value: rightWidth,
    onChange: setRightWidth,
  });
  const bottomResize = useResizable({
    axis: "y",
    min: 160,
    max: 520,
    value: bottomHeight,
    onChange: setBottomHeight,
  });

  return (
    <div className="flex h-screen flex-col overflow-hidden" style={{ background: 'var(--bg)', color: 'var(--text)' }}>
      <TopBar />
      {}
      <div className="hidden md:flex md:flex-1 md:overflow-hidden">
        <AnimatePresence initial={false}>
          {leftOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: leftWidth, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 40 }}
              className="shrink-0 overflow-hidden border-r" style={{ borderColor: 'var(--border)' }}
            >
              <LeftSidebar />
            </motion.aside>
          )}
        </AnimatePresence>
        {leftOpen && (
          <ResizeHandle
            axis="x"
            onPointerDown={leftResize.onPointerDown}
            cursor={leftResize.cursor}
          />
        )}

        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="flex flex-1 overflow-hidden">
            <div className="flex flex-1 flex-col overflow-hidden">
              <ChatPanel />
              <div className="h-px" style={{ background: 'var(--border)' }} />
              <CodeEditor />
            </div>
            <AnimatePresence initial={false}>
              {rightOpen && (
                <motion.aside
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: rightWidth, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ type: "spring", stiffness: 400, damping: 40 }}
                  className="shrink-0 overflow-hidden border-l" style={{ borderColor: 'var(--border)' }}
                >
                  <RightSidebar />
                </motion.aside>
              )}
            </AnimatePresence>
            {rightOpen && (
              <ResizeHandle
                axis="x"
                onPointerDown={rightResize.onPointerDown}
                cursor={rightResize.cursor}
              />
            )}
          </div>
          <AnimatePresence initial={false}>
            {bottomOpen && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: bottomHeight }}
                exit={{ height: 0 }}
                transition={{ type: "spring", stiffness: 400, damping: 40 }}
                className="overflow-hidden border-t" style={{ borderColor: 'var(--border)' }}
              >
                <BottomBar />
              </motion.div>
            )}
          </AnimatePresence>
          {bottomOpen && (
            <ResizeHandle
              axis="y"
              onPointerDown={bottomResize.onPointerDown}
              cursor={bottomResize.cursor}
            />
          )}
        </div>
      </div>

      {}
      <div className="flex flex-1 flex-col overflow-hidden md:hidden">
        <ChatPanel />
        <div className="h-px" style={{ background: 'var(--border)' }} />
        <CodeEditor />
      </div>
      <AnimatePresence>
        {leftOpen && (
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            className="fixed inset-y-0 left-0 z-40 w-72 md:hidden"
          >
            <LeftSidebar />
          </motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {rightOpen && (
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            className="fixed inset-y-0 right-0 z-40 w-80 md:hidden"
          >
            <RightSidebar />
          </motion.div>
        )}
      </AnimatePresence>

      <CommandPalette />
    </div>
  );
}
