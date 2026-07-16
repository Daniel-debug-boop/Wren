import { type ReactElement, type ReactNode } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AgentStatusProvider } from "#/components/layout/AgentStatusContext";

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  queryClient?: QueryClient;
}

function AllTheProviders({
  children,
  queryClient = createTestQueryClient(),
}: {
  children: ReactNode;
  queryClient?: QueryClient;
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <AgentStatusProvider>{children}</AgentStatusProvider>
    </QueryClientProvider>
  );
}

function customRender(
  ui: ReactElement,
  options?: CustomRenderOptions,
) {
  const { queryClient, ...renderOptions } = options ?? {};
  return {
    user: userEvent.setup(),
    ...render(ui, {
      wrapper: ({ children }) => (
        <AllTheProviders queryClient={queryClient}>
          {children}
        </AllTheProviders>
      ),
      ...renderOptions,
    }),
  };
}

export * from "@testing-library/react";
export { customRender as render };
