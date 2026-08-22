import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

// Minimal MSW server for vitest environment
export const server = setupServer(http.all("*", () => HttpResponse.json({})));
