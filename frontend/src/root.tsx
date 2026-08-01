import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  isRouteErrorResponse,
  useRouteError,
} from "react-router";
import { useTranslation } from "react-i18next";

import "./index.css";
import "./i18n";

export const links = () => [
  { rel: "icon", href: "/favicon.ico" },
  { rel: "manifest", href: "/manifest.json" },
  { rel: "apple-touch-icon", href: "/icons/icon-192.png" },
];

export const meta = () => [
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
  {
    name: "apple-mobile-web-app-status-bar-style",
    content: "black-translucent",
  },
  { name: "mobile-web-app-capable", content: "yes" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  return (
    <html lang="en" className="dark">
      <head>
        <Meta />
        <Links />
      </head>
      <body>
        <a href="#main" className="skip-link">
          {t("COMMON$SKIP_TO_CONTENT")}
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
  const { t } = useTranslation();

  if (isRouteErrorResponse(error)) {
    return (
      <div className="flex min-h-screen items-center justify-center p-8">
        <div className="card p-8 max-w-md w-full text-center">
          <h1
            className="text-lg font-semibold mb-2"
            style={{ color: "var(--text-primary)" }}
          >
            {error.status} — {error.statusText}
          </h1>
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
            {error.data?.message || t("ERROR$DEFAULT_MESSAGE")}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <div className="card p-8 max-w-md w-full text-center">
        <h1
          className="text-lg font-semibold mb-2"
          style={{ color: "var(--text-primary)" }}
        >
          {t("ERROR$UNEXPECTED_TITLE")}
        </h1>
        <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>
          {t("ERROR$UNEXPECTED_MESSAGE")}
        </p>
      </div>
    </div>
  );
}
