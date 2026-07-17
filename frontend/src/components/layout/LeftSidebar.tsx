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
    <div className="flex h-full w-full flex-col bg-[#0d1117]">
      <div className="flex border-b border-white/5 text-xs">
        {(["files", "skills"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "flex-1 py-2 capitalize transition",
              tab === t ? "text-cyan-400" : "text-zinc-500 hover:text-zinc-300",
            )}
          >
            {t}
            {tab === t && (
              <motion.div
                layoutId="leftTab"
                className="mx-auto mt-1 h-0.5 w-8 rounded bg-cyan-400"
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
