import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoutesStub } from "react-router";
import ApiKeySetup from "#/routes/login";

const { getAllMock, saveMock } = vi.hoisted(() => ({
  getAllMock: vi.fn(),
  saveMock: vi.fn(),
}));

vi.mock("#/components/ui/Nav", () => ({
  Nav: () => <nav data-testid="nav" />,
}));

vi.mock("#/components/ui/Footer", () => ({
  Footer: () => <footer data-testid="footer" />,
}));

vi.mock("#/api/api-keys-service/api-keys-service.api", () => ({
  default: {
    getAll: getAllMock,
    save: saveMock,
  },
  PROVIDER_METADATA: {
    openai: {
      name: "OpenAI",
      description: "GPT-4o, GPT-4 Turbo, GPT-4o-mini",
      url: "https://platform.openai.com/api-keys",
      color: "#10A37F",
      models: ["gpt-4o"],
    },
    anthropic: {
      name: "Anthropic",
      description: "Claude 3.5 Sonnet, Claude 3 Haiku",
      url: "https://console.anthropic.com/settings/keys",
      color: "#D97757",
      models: ["claude-3-5-sonnet-20241022"],
    },
  },
}));

describe("ApiKeySetup", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getAllMock.mockReturnValue([]);
    saveMock.mockImplementation(() => []);
    localStorage.clear();
  });

  const renderPage = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const RouterStub = createRoutesStub([
      {
        Component: ApiKeySetup,
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

  it("renders heading and subtitle", () => {
    renderPage();
    expect(screen.getByText("Bring Your Own API Key")).toBeInTheDocument();
    expect(
      screen.getByText(/Paste your LLM provider API key below/),
    ).toBeInTheDocument();
  });

  it("renders API key input and disabled Get Started button", () => {
    renderPage();
    expect(
      screen.getByPlaceholderText("Paste your API key here..."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /get started/i })).toBeDisabled();
  });

  it("enables button when key is 8+ characters", async () => {
    const user = userEvent.setup();
    renderPage();

    const input = screen.getByPlaceholderText("Paste your API key here...");
    await user.type(input, "sk-test12345678");

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /get started/i }),
      ).toBeEnabled();
    });
  });

  it("detects provider from API key prefix", async () => {
    const user = userEvent.setup();
    renderPage();

    const input = screen.getByPlaceholderText("Paste your API key here...");
    await user.type(input, "sk-ant-test12345");

    await waitFor(() => {
      expect(screen.getByText(/Detected: Anthropic/)).toBeInTheDocument();
    });
  });

  it("shows success state after saving", async () => {
    const user = userEvent.setup();
    renderPage();

    const input = screen.getByPlaceholderText("Paste your API key here...");
    await user.type(input, "sk-test12345678");

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /get started/i }),
      ).toBeEnabled();
    });

    await user.click(screen.getByRole("button", { name: /get started/i }));

    await waitFor(() => {
      expect(screen.getByText("API Key saved!")).toBeInTheDocument();
    });
  });

  it("shows existing providers notice when providers exist", () => {
    getAllMock.mockReturnValue([
      { provider: "openai", model: "gpt-4o", apiKey: "sk-xxx" },
    ]);

    renderPage();

    expect(
      screen.getByText(/1 provider already configured/),
    ).toBeInTheDocument();
  });
});
