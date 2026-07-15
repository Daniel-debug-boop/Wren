import { type ReactNode } from "react";

interface InputActionButtonProps {
  label: string;
  children: ReactNode;
  onClick?: () => void;
}

export function InputActionButton({ label, children, onClick }: InputActionButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      className="press flex h-7 items-center gap-1 rounded-md px-1.5 text-xs transition-all duration-200"
      style={{ color: "var(--text-subtle)" }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "var(--claude-hover)";
        e.currentTarget.style.color = "var(--text-secondary)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "var(--text-subtle)";
      }}
    >
      {children}
    </button>
  );
}
