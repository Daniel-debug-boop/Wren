import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  isRouteErrorResponse,
  useRouteError,
} from "react-router";

import type { Route } from "./+types/root";
import "./index.css";

export const links: Route.LinksFunction = () => [
  { rel: "icon", href: "/favicon.ico" },
  { rel: "manifest", href: "/manifest.json" },
  { rel: "apple-touch-icon", href: "/icons/icon-192.png" },
];

export const meta: Route.MetaFunction = () => [
  { title: "Wren — AI Engineering Platform" },
  { charSet: "utf-8" },
  { name: "viewport", content: "width=device-width, initial-scale=1" },
  { name: "theme-color", content: "#000000" },
  {
    name: "description",
    content:
      "Wren — Premium AI Engineering Platform. Generate complete apps with a 4-agent AI pipeline. Architect, Plan, Write, Review.",
  },
  { name: "application-name", content: "Wren AI" },
  { name: "apple-mobile-web-app-capable", content: "yes" },
  { name: "apple-mobile-web-app-status-bar-style", content: "black-translucent" },
  { name: "mobile-web-app-capable", content: "yes" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <Meta />
        <Links />
      </head>
      <body>
        <a href="#main" className="skip-link">
          Skip to main content
        </a>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <div className="glass-shell-outer max-w-md w-full">
          <div className="glass-shell-inner p-8 text-center">
            <h1 className="text-lg font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
              {error.status} — {error.statusText}
            </h1>
            <p className="text-sm" style={{ color: "var(--color-text-tertiary)" }}>
              {error.data?.message || "Something went wrong."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="glass-shell-outer max-w-md w-full">
        <div className="glass-shell-inner p-8 text-center">
          <h1 className="text-lg font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
            Unexpected Error
          </h1>
          <p className="text-sm" style={{ color: "var(--color-text-tertiary)" }}>
            An unexpected error occurred. Please try again.
          </p>
        </div>
      </div>
    </div>
  );
}
