import { http, HttpResponse } from "msw";
import type { UserSettings } from "#/types/settings";

export const MOCK_DEFAULT_USER_SETTINGS: UserSettings = {
  llm_model: "gpt-4",
  llm_api_key: "",
  llm_base_url: "",
  agent_type: "default",
  theme: "dark",
  provider_tokens_set: {},
  is_new_user: false,
  mode: "code",
};

export const handlers = [
  http.get("/api/settings", () => HttpResponse.json(null, { status: 404 })),
  http.patch("/api/settings", async ({ request }) => {
    const body = (await request.json()) as Partial<UserSettings>;
    return HttpResponse.json({ ...MOCK_DEFAULT_USER_SETTINGS, ...body });
  }),
  http.get("/api/config", () =>
    HttpResponse.json({
      app_mode: "oss",
      posthog_client_key: null,
      providers_configured: ["github"],
      auth_url: null,
      feature_flags: {
        enable_billing: false,
        hide_llm_settings: false,
        enable_jira: false,
        enable_jira_dc: false,
        enable_linear: false,
        hide_users_page: false,
        hide_billing_page: false,
        hide_integrations_page: false,
        enable_onboarding: false,
      },
      maintenance_start_time: null,
      recaptcha_site_key: null,
      faulty_models: [],
      error_message: null,
      updated_at: new Date().toISOString(),
      github_app_slug: null,
    }),
  ),
  http.post("/api/auth/authenticate", () =>
    HttpResponse.json({ authenticated: true }),
  ),
  http.get("/api/git/repositories", () =>
    HttpResponse.json({ items: [], next_page_id: null }),
  ),
  http.get("/api/git/repositories/:id/branches", () =>
    HttpResponse.json({ items: [], next_page_id: null }),
  ),
];
