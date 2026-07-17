import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoutesStub } from "react-router";
import ProviderSetup from "#/routes/login";

const { useConfigMock } = vi.hoisted(() => ({
  useConfigMock: vi.fn(() => ({
    data: undefined,
    isLoading: false,
  })),
}));

vi.mock("#/hooks/query/use-config", () => ({
  useConfig: () => useConfigMock(),
}));

vi.mock("#/components/ui/Nav", () => ({
  Nav: () => <nav data-testid="nav" />,
}));

vi.mock("#/components/ui/Footer", () => ({
  Footer: () => <footer data-testid="footer" />,
}));

describe("ProviderSetup", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  const renderPage = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const RouterStub = createRoutesStub([
      {
        Component: ProviderSetup,
        path: "/login",
      },
    ]);
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    return render(<RouterStub initialEntries={["/login"]} />, {
      wrapper: Wrapper,
    });
  };

  it("renders connect your LLM heading", () => {
    renderPage();
    expect(screen.getByText("Connect your LLM")).toBeInTheDocument();
  });

  it("renders provider cards for known providers", () => {
    renderPage();
    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("Anthropic")).toBeInTheDocument();
    expect(screen.getByText("Ollama")).toBeInTheDocument();
    expect(screen.getByText("Groq")).toBeInTheDocument();
  });

  it("renders subtitle text", () => {
    renderPage();
    expect(
      screen.getByText(/Choose a provider, pick a model/),
    ).toBeInTheDocument();
  });
});
