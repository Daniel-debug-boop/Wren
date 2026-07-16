import { Links, Outlet } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

export default function Root() {
  return (
    <html lang="en" className="dark">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Links />
        <meta
          name="theme-color"
          content="#0A0A0B"
          media="(prefers-color-scheme: dark)"
        />
        <meta
          name="description"
          content="Wren — Premium AI Engineering Platform. Code with your own LLM API key."
        />
        <title>Wren — AI Engineering Platform</title>
        <link rel="icon" href="/favicon.ico" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="application-name" content="Wren AI" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Wren" />
        <meta name="mobile-web-app-capable" content="yes" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body>
        <a href="#main" className="skip-link">
          Skip to main content
        </a>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
          <Toaster
            position="bottom-right"
            gutter={8}
            toastOptions={{
              duration: 4000,
              style: {
                background:
                  "color-mix(in srgb, var(--surface-hover) 85%, transparent)",
                backdropFilter: "blur(24px) saturate(160%)",
                WebkitBackdropFilter: "blur(24px) saturate(160%)",
                border: "1px solid var(--border-strong)",
                borderRadius: "var(--radius-xl)",
                color: "var(--text)",
                fontSize: "0.85rem",
                padding: "0.875rem 1rem",
                boxShadow: "var(--shadow-lg)",
              },
              success: {
                iconTheme: {
                  primary: "var(--success)",
                  secondary: "var(--bg)",
                },
              },
              error: {
                iconTheme: {
                  primary: "var(--error)",
                  secondary: "var(--bg)",
                },
              },
            }}
          />
        </QueryClientProvider>
      </body>
    </html>
  );
}
