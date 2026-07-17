import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Badge } from "../ui/GlassCard";

interface Props {
  role: "user" | "assistant";
  mode: string;
  content: string;
  streaming?: boolean;
}

export function MessageBubble({ role, mode, content, streaming }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${role === "user" ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
          role === "user"
            ? "bg-cyan-500/10 text-cyan-100"
            : "bg-white/5 text-zinc-200"
        }`}
      >
        <Badge className="mb-1">{mode}</Badge>
        <ReactMarkdown>{content}</ReactMarkdown>
        {streaming && <span className="animate-pulse text-cyan-400">▋</span>}
      </div>
    </motion.div>
  );
}
