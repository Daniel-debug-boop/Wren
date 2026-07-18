import { useState } from "react";
import { motion } from "framer-motion";
import { FileTree } from "../ide/FileTree";
import { SkillsBrowser } from "./SkillsBrowser";
import type { FileNode } from "../ide/FileTree";
import { cn } from "../../lib/utils";

export function LeftSidebar() {
  const [tab, setTab] = useState<"files" | "skills">("files");
  const [files] = useState<FileNode[]>([]);

  return (
    <div className="flex h-full w-full flex-col" style={{ background: 'var(--bg)' }}>
      <div className="flex border-b" style={{ borderColor: 'var(--border)' }}>
        {(["files", "skills"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="flex-1 py-2 text-xs capitalize transition-colors"
            style={{
              color: tab === t ? 'var(--accent)' : 'var(--text-muted)',
            }}
            onMouseEnter={(e) => {
              if (tab !== t) e.currentTarget.style.color = 'var(--text)';
            }}
            onMouseLeave={(e) => {
              if (tab !== t) e.currentTarget.style.color = 'var(--text-muted)';
            }}
          >
            {t}
            {tab === t && (
              <motion.div
                layoutId="leftTab"
                className="mx-auto mt-1 h-0.5 w-8 rounded"
                style={{ background: 'var(--accent)' }}
              />
            )}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === "files" ? <FileTree files={files} /> : <SkillsBrowser />}
      </div>
    </div>
  );
}
