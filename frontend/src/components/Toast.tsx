import { Toaster } from "react-hot-toast";

export function ToastProvider() {
  return (
    <Toaster
      position="top-right"
      gutter={8}
      containerStyle={{
        top: 16,
        right: 16,
        zIndex: 9999,
      }}
      toastOptions={{
        duration: 4000,
        style: {
          background:
            "color-mix(in srgb, var(--glass-surface) 90%, transparent)",
          backdropFilter: "blur(24px) saturate(160%)",
          WebkitBackdropFilter: "blur(24px) saturate(160%)",
          border: "1px solid var(--glass-border-strong)",
          borderRadius: "10px",
          boxShadow: "var(--shadow-glass-lg)",
          color: "var(--glass-text-primary)",
          fontSize: "0.85rem",
          padding: "0.875rem 1rem",
          fontFamily: "var(--font-sans)",
        },
        success: {
          iconTheme: {
            primary: "var(--glass-success)",
            secondary: "var(--glass-bg)",
          },
          style: {
            borderColor:
              "color-mix(in srgb, var(--glass-success) 30%, transparent)",
          },
        },
        error: {
          iconTheme: {
            primary: "var(--glass-error)",
            secondary: "var(--glass-bg)",
          },
          style: {
            borderColor:
              "color-mix(in srgb, var(--glass-error) 30%, transparent)",
          },
        },
      }}
    />
  );
}
