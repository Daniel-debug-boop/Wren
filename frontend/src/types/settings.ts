import type { ModeId } from "./mode";

export interface UserSettings {
  llm_model: string;
  llm_api_key: string;
  llm_base_url: string;
  agent_type: string;
  theme: "light" | "dark" | "system";
  provider_tokens_set: Record<string, string>;
  is_new_user: boolean;
  mode: ModeId;
  ui_theme?: "light" | "dark" | "system";
  ui_density?: "compact" | "normal" | "comfortable";
  display_name?: string;
}

export interface ProviderToken {
  provider: string;
  token: string;
}

export interface LLMProfile {
  id: string;
  name: string;
  model: string;
  api_key: string;
  base_url: string;
}
