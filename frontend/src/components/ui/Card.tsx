import { type HTMLAttributes, type ReactNode, forwardRef } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated";
  hoverable?: boolean;
  children: ReactNode;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = "default",
      hoverable = false,
      className = "",
      children,
      ...props
    },
    ref,
  ) => (
    <div
      ref={ref}
      className={`${variant === "elevated" ? "card-elevated" : "card"} ${hoverable ? "hover-lift" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  ),
);

Card.displayName = "Card";

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  action?: ReactNode;
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, description, action, className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={`flex items-start justify-between gap-4 p-5 pb-0 ${className}`}
      {...props}
    >
      <div>
        <h3 className="text-sm font-semibold tracking-tight text-text">
          {title}
        </h3>
        {description && (
          <p className="mt-0.5 text-xs text-text-subtle">{description}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
      {children}
    </div>
  ),
);

CardHeader.displayName = "CardHeader";

interface CardContentProps extends HTMLAttributes<HTMLDivElement> {}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className = "", children, ...props }, ref) => (
    <div ref={ref} className={`p-5 pt-0 ${className}`} {...props}>
      {children}
    </div>
  ),
);

CardContent.displayName = "CardContent";

interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={`flex items-center gap-3 p-5 pt-0 border-t border-border ${className}`}
      {...props}
    >
      {children}
    </div>
  ),
);

CardFooter.displayName = "CardFooter";
