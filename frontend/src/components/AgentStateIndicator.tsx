/* eslint-disable i18next/no-literal-string */

import { motion } from "framer-motion";

type ExecutionStatus =
  | "STOPPED"
  | "RUNNING"
  | "AWAITING_USER_INPUT"
  | "FINISHED"
  | "ERROR";

interface AgentStateIndicatorProps {
  status: ExecutionStatus;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
}

const statusConfig: Record<
  ExecutionStatus,
  { label: string; color: string; glow: string; icon: string }
> = {
  STOPPED: {
    label: "Stopped",
    color: "var(--color-text-tertiary)",
    glow: "transparent",
    icon: "M6 4h4v16H6zM14 4h4v16h-4z",
  },
  RUNNING: {
    label: "Running",
    color: "var(--color-success)",
    glow: "rgba(92, 184, 116, 0.15)",
    icon: "M8 5v14l11-7z",
  },
  AWAITING_USER_INPUT: {
    label: "Awaiting Input",
    color: "var(--color-gold-400)",
    glow: "rgba(201, 185, 116, 0.15)",
    icon: "M12 2a10 10 0 1010 10M12 2v4M12 2l4 4",
  },
  FINISHED: {
    label: "Finished",
    color: "var(--color-info)",
    glow: "rgba(90, 141, 212, 0.15)",
    icon: "M9 12l2 2l4-4m6 2a9 9 0 11-18 0a9 9 0 0118 0z",
  },
  ERROR: {
    label: "Error",
    color: "var(--color-error)",
    glow: "rgba(212, 90, 90, 0.15)",
    icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z",
  },
};

export function AgentStateIndicator({
  status,
  onPause,
  onResume,
  onStop,
}: AgentStateIndicatorProps) {
  const cfg = statusConfig[status] || statusConfig.STOPPED;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-subtle"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.625rem",
        padding: "0.375rem 0.75rem",
        borderRadius: "var(--radius-md)",
        fontSize: "0.75rem",
      }}
      role="status"
      aria-label={`Agent status: ${cfg.label}`}
      aria-live="polite"
    >
      {/* Status dot */}
      <motion.span
        animate={{
          scale: status === "RUNNING" ? [1, 1.3, 1] : 1,
          opacity: status === "RUNNING" ? [1, 0.5, 1] : 1,
        }}
        transition={{
          duration: 2,
          repeat: status === "RUNNING" ? Infinity : 0,
          ease: "easeInOut",
        }}
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: cfg.color,
          boxShadow: `0 0 8px ${cfg.glow}`,
          flexShrink: 0,
        }}
        aria-hidden="true"
      />

      {/* Label */}
      <span style={{ color: "var(--color-text-secondary)", fontWeight: 500 }}>
        {cfg.label}
      </span>

      {/* Actions */}
      <span
        style={{
          display: "inline-flex",
          gap: "0.25rem",
          marginLeft: "0.25rem",
        }}
      >
        {status === "RUNNING" && onPause && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="btn-icon"
            onClick={onPause}
            aria-label="Pause agent"
            title="Pause"
            style={{ width: 22, height: 22, padding: 0 }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="6" y="4" width="4" height="16" />
              <rect x="14" y="4" width="4" height="16" />
            </svg>
          </motion.button>
        )}
        {status === "AWAITING_USER_INPUT" && onResume && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="btn-icon"
            onClick={onResume}
            aria-label="Resume agent"
            title="Resume"
            style={{ width: 22, height: 22, padding: 0 }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          </motion.button>
        )}
        {status === "RUNNING" && onStop && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="btn-icon"
            onClick={onStop}
            aria-label="Stop agent"
            title="Stop"
            style={{ width: 22, height: 22, padding: 0 }}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            </svg>
          </motion.button>
        )}
      </span>
    </motion.div>
  );
}
