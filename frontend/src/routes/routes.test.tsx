import { describe, it, expect, vi, beforeAll } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import RootLayout from "./root-layout";
import HomePage from "./home";
import GenerationPage from "./generation";
import ConversationPage from "./conversation";
import SettingsPage from "./settings";
import ApiKeysPage from "./api-keys";
import SkillsPage from "./skills";
import OrchestrationPage from "./orchestration";
import WorkspacePage from "./workspace";
import LoginPage from "./login";

/* jsdom + MSW-node cannot intercept XHR, so API-dependent modules are mocked
 * at the module boundary. Mocks return realistic shapes from types/api.ts. */

vi.mock("#/api/endpoints", () => {
  const deferred = <T,>(v: T) => new Promise<T>(() => {}); // never resolves: loading state
  return {
    settingsApi: {
      get: () => Promise.resolve({}), // resolve so the page exits its loading state
      update: deferred,
    },
    healthApi: { check: () => Promise.resolve({ status: "ok" }) },
    profilesApi: {
      list: deferred,
      create: deferred,
      delete: deferred,
      activate: deferred,
    },
    secretsApi: { list: deferred, set: deferred, delete: deferred },
    userApi: { me: deferred },
    conversationsApi: {
      list: () => Promise.resolve([]),
      get: deferred,
      create: deferred,
      delete: deferred,
      messages: () => Promise.resolve([]),
      sendMessage: deferred,
    },
    generationApi: { start: deferred, status: deferred, result: deferred },
    apiKeysApi: {
      list: () => Promise.resolve([]),
      create: deferred,
      delete: deferred,
    },
    skillsApi: { list: deferred, toggle: deferred },
    authApi: { login: deferred, logout: deferred },
  };
});

vi.mock("../pages/Workspace", () => ({
  Workspace: () => (
    <div>
      <h1>Workspace</h1>
      <div role="region" aria-label="file tree" />
    </div>
  ),
}));

function renderAt(path: string) {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <RootLayout />,
        children: [
          { index: true, element: <HomePage /> },
          { path: "generation", element: <GenerationPage /> },
          { path: "conversation", element: <ConversationPage /> },
          { path: "settings", element: <SettingsPage /> },
          { path: "api-keys", element: <ApiKeysPage /> },
          { path: "skills", element: <SkillsPage /> },
          { path: "orchestration", element: <OrchestrationPage /> },
          { path: "workspace", element: <WorkspacePage /> },
          { path: "login", element: <LoginPage /> },
        ],
      },
    ],
    { initialEntries: [path] },
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

beforeAll(() => {
  window.localStorage.setItem("wren_llm_api_key", "test-key");
});

describe("route rendering (smoke)", () => {
  it("home renders and shows brand", async () => {
    renderAt("/");
    await waitFor(() => {
      expect(screen.getAllByText(/wren/i).length).toBeGreaterThan(0);
    });
  });

  it("generation renders header", async () => {
    renderAt("/generation");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 }).textContent).toMatch(
        /project generator/i,
      );
    });
  });

  it("conversation renders", async () => {
    renderAt("/conversation");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 2 })).toBeInTheDocument();
    });
  });

  it("settings renders header", async () => {
    renderAt("/settings");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });
  });

  it("api-keys renders header", async () => {
    renderAt("/api-keys");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });
  });

  it("skills renders header", async () => {
    renderAt("/skills");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });
  });

  it("orchestration renders header", async () => {
    renderAt("/orchestration");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });
  });

  it("workspace renders", async () => {
    renderAt("/workspace");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });
  });

  it("login renders header", async () => {
    renderAt("/login");
    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    });
  });
});

describe("theme toggle", () => {
  it("toggles dark class and persists to localStorage", async () => {
    const user = userEvent.setup();
    renderAt("/skills");
    const toggle = screen.getByRole("button", { name: /switch to dark/i });
    await user.click(toggle);
    expect(document.documentElement.classList.contains("dark")).toBe(true);
    expect(window.localStorage.getItem("wren-theme")).toBe("dark");
    await user.click(screen.getByRole("button", { name: /switch to light/i }));
    expect(document.documentElement.classList.contains("dark")).toBe(false);
    expect(window.localStorage.getItem("wren-theme")).toBe("light");
  });
});
