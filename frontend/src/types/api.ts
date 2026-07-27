/* ── Health & Status ── */
export interface HealthResponse {
  status: string;
}

/* ── LLM Config ── */
export interface LLMConfig {
  model: string;
  base_url?: string | null;
  api_key?: string;
  max_tokens?: number;
  temperature?: number;
}

/* ── Settings ── */
export interface Settings {
  llm_config?: LLMConfig;
  username?: string;
  language?: string;
  sandbox_type?: string;
}

export interface ApiSettings {
  llm_config?: LLMConfig;
  username?: string;
  language?: string;
  sandbox_type?: string;
}

/* ── Conversation ── */
export interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  status: "running" | "stopped" | "error";
  selected_repository?: string | null;
  selected_branch?: string | null;
}

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

/* ── Generation / Pipeline ── */
export type PipelineStage = "architect" | "planner" | "writer" | "reviewer" | "complete";

export interface PipelineStatus {
  stage: PipelineStage;
  progress: number;
  message: string;
}

export interface GenerationRequest {
  prompt: string;
  model?: string;
  output_dir?: string;
  validate?: boolean;
}

export interface GenerationResult {
  success: boolean;
  project_path?: string;
  files: string[];
  error?: string;
}

/* ── API Keys ── */
export interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  created_at: string;
}

/* ── Profile ── */
export interface Profile {
  name: string;
  model: string;
  base_url: string | null;
  api_key_set: boolean;
}

export interface ProfilesResponse {
  profiles: Profile[];
  active_profile: string | null;
}

/* ── Secrets ── */
export interface Secret {
  name: string;
}

/* ── Skills ── */
export interface Skill {
  name: string;
  description: string;
  triggers?: string[];
  enabled: boolean;
}

/* ── User ── */
export interface UserInfo {
  id: string;
  username: string;
  email?: string;
  created_at: string;
}
