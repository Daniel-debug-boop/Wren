import { ReactNode } from "react";
import { cn } from "../../lib/utils";

export function GlassCard({
  className,
  ...props
}: { className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  const { ...rest } = props;
  return (
    <div
      className={cn(
        "rounded-xl border backdrop-blur-xl",
        "transition-all duration-200",
        "hover:-translate-y-0.5",
        className,
      )}
      style={{
        background: 'var(--surface)',
        borderColor: 'var(--border)',
        boxShadow: 'var(--shadow-sm), var(--shadow-inner)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'color-mix(in srgb, var(--accent) 30%, var(--border))';
        e.currentTarget.style.boxShadow = 'var(--shadow-md), var(--shadow-inner), var(--shadow-glow)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)';
        e.currentTarget.style.boxShadow = 'var(--shadow-sm), var(--shadow-inner)';
      }}
      {...rest}
    />
  );
}

export function Badge({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[10px] font-medium",
        className,
      )}
      style={{
        background: 'var(--accent-subtle)',
        color: 'var(--accent)',
      }}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  className,
  type = "button",
  ...props
}: { className?: string } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { ...rest } = props;
  return (
    <button
      type={type}
      className={cn(
        "rounded-md px-3 py-1.5 text-xs transition",
        className,
      )}
      style={{
        border: '1px solid var(--border)',
        background: 'var(--surface)',
        color: 'var(--text-muted)',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'var(--surface-hover)';
        e.currentTarget.style.color = 'var(--text)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'var(--surface)';
        e.currentTarget.style.color = 'var(--text-muted)';
      }}
      {...rest}
    >
      {children}
    </button>
  );
}
