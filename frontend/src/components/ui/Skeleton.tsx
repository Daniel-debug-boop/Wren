import { type HTMLAttributes } from "react";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular" | "card";
  width?: string | number;
  height?: string | number;
  animation?: "shimmer" | "pulse" | "none";
}

export function Skeleton({
  variant = "text",
  width = "100%",
  height,
  animation = "shimmer",
  className = "",
  ...props
}: SkeletonProps) {
  const baseStyles = {
    width,
    height:
      height ||
      (variant === "text" ? "1rem" : variant === "circular" ? "1rem" : "100%"),
    borderRadius:
      variant === "circular"
        ? "9999px"
        : variant === "card"
          ? "var(--radius-xl)"
          : "var(--radius-md)",
  };

  return (
    <div
      className={`shimmer ${animation === "pulse" ? "animate-pulse-glow" : ""} ${className}`}
      style={baseStyles as React.CSSProperties}
      aria-hidden="true"
      {...props}
    />
  );
}

export function SkeletonText({
  lines = 3,
  className = "",
  ...props
}: { lines?: number; className?: string } & Omit<SkeletonProps, "variant">) {
  return (
    <div className={`space-y-2 ${className}`} {...props}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? "60%" : "100%"}
          {...props}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({
  className = "",
  ...props
}: { className?: string } & Omit<SkeletonProps, "variant">) {
  return (
    <div className={`card p-5 space-y-4 ${className}`} {...props}>
      <div className="flex items-center justify-between">
        <Skeleton variant="rectangular" width="40%" height="1.25rem" />
        <Skeleton variant="circular" width="2.5rem" height="2.5rem" />
      </div>
      <SkeletonText lines={3} />
      <div className="flex items-center gap-2">
        <Skeleton variant="rectangular" width="20%" height="2rem" />
        <Skeleton variant="rectangular" width="20%" height="2rem" />
      </div>
    </div>
  );
}
