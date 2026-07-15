/* eslint-disable i18next/no-literal-string */

import { type ReactNode } from "react";
import { motion } from "framer-motion";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  compact?: boolean;
}

function DefaultIcon({ color }: { color: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--glass-accent)"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  );
}

function ConversationIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--glass-accent)"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  );
}

function ActivityIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--glass-text-tertiary)"
      strokeWidth="1"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

export const EmptyStateIcons = {
  Default: DefaultIcon,
  Chat: ChatIcon,
  Conversation: ConversationIcon,
  Activity: ActivityIcon,
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  compact = false,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="glass-card"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: compact ? "2rem 1rem" : "3rem 1.5rem",
        minHeight: compact ? 120 : 240,
        border: "1px solid var(--glass-border)",
      }}
      role="status"
      aria-label={title}
    >
      {/* Decorative background glow */}
      <div
        style={{
          position: "relative",
          marginBottom: compact ? "0.75rem" : "1.25rem",
        }}
        aria-hidden="true"
      >
        <div
          className="animate-pulse-glow"
          style={{
            position: "absolute",
            inset: -8,
            background:
              "radial-gradient(ellipse at center, color-mix(in srgb, var(--glass-accent) 8%, transparent) 0%, transparent 70%)",
            borderRadius: "50%",
          }}
        />
        {icon || <DefaultIcon color="var(--glass-accent)" />}
      </div>

      <h3
        style={{
          fontSize: compact ? "0.95rem" : "1.1rem",
          fontWeight: 600,
          color: "var(--glass-text-primary)",
          margin: "0 0 0.375rem",
          lineHeight: 1.4,
          fontFamily: "var(--font-serif)",
        }}
      >
        {title}
      </h3>

      {description && (
        <p
          style={{
            fontSize: "0.85rem",
            color: "var(--glass-text-tertiary)",
            margin: "0 0 1.25rem",
            maxWidth: 320,
            lineHeight: 1.5,
          }}
        >
          {description}
        </p>
      )}

      {(action || secondaryAction) && (
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
            justifyContent: "center",
          }}
        >
          {action && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="btn-glass-accent"
              onClick={action.onClick}
              aria-label={action.label}
              style={{ fontSize: "0.8rem", padding: "0.5rem 1rem" }}
            >
              {action.label}
            </motion.button>
          )}
          {secondaryAction && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="btn-glass"
              onClick={secondaryAction.onClick}
              aria-label={secondaryAction.label}
              style={{ fontSize: "0.8rem", padding: "0.5rem 1rem" }}
            >
              {secondaryAction.label}
            </motion.button>
          )}
        </div>
      )}
    </motion.div>
  );
}
