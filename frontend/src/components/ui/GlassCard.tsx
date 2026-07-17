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
        "rounded-xl border border-white/10 bg-white/5 backdrop-blur-xl",
        "shadow-[0_8px_32px_rgba(0,0,0,0.4)] transition-all duration-200",
        "hover:border-cyan-500/30 hover:bg-white/[0.07]",
        className,
      )}
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
        "rounded-full bg-cyan-500/15 px-2 py-0.5 text-[10px] font-medium text-cyan-300",
        className,
      )}
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
        "rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-zinc-300 transition",
        "hover:bg-white/10 hover:text-white",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
