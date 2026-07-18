import { Component, type ErrorInfo, type ReactNode } from "react";
import { motion } from "framer-motion";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    const { onError } = this.props;
    if (onError) {
      onError(error, info);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    const { hasError, error } = this.state;
    const { fallback, children } = this.props;

    if (hasError) {
      if (fallback) return fallback;

      /* eslint-disable i18next/no-literal-string */
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          role="alert"
          aria-live="assertive"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "3rem 1.5rem",
            textAlign: "center",
            minHeight: 300,
          }}
        >
          <div
            className="card-elevated"
            style={{
              padding: "2rem",
              maxWidth: 420,
              width: "100%",
            }}
          >
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: "50%",
                background: "rgba(212, 90, 90, 0.12)",
                border: "1px solid rgba(212, 90, 90, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 1rem",
              }}
              aria-hidden="true"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--color-error)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h2
              style={{
                fontSize: "1.1rem",
                fontWeight: 600,
                color: "var(--color-text-primary)",
                margin: "0 0 0.5rem",
              }}
            >
              Something went wrong
            </h2>
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--color-text-tertiary)",
                margin: "0 0 1.25rem",
                lineHeight: 1.5,
              }}
            >
              {error?.message ||
                "An unexpected error occurred. Please try again."}
            </p>
            <button
              type="button"
              className="btn-accent"
              onClick={this.handleReset}
              aria-label="Try again"
              style={{ width: "100%" }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
              </svg>
              Try Again
            </button>
          </div>
        </motion.div>
      );
      /* eslint-enable i18next/no-literal-string */
    }

    return children;
  }
}
