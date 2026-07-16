export interface AppConfig {
  app_mode: "oss" | "saas";
  posthog_client_key: string | null;
  providers_configured: string[];
  auth_url: string | null;
  feature_flags: FeatureFlags;
  maintenance_start_time: string | null;
  recaptcha_site_key: string | null;
  faulty_models: string[];
  error_message: string | null;
  updated_at: string;
  github_app_slug: string | null;
  github_client_id?: string | null;
  user?: { email?: string; name?: string; avatar_url?: string };
  llm_provider?: string;
}

export interface FeatureFlags {
  enable_billing: boolean;
  hide_llm_settings: boolean;
  enable_jira: boolean;
  enable_jira_dc: boolean;
  enable_linear: boolean;
  hide_users_page: boolean;
  hide_billing_page: boolean;
  hide_integrations_page: boolean;
  enable_onboarding?: boolean;
  deployment_mode?: "cloud" | "self_hosted";
}
