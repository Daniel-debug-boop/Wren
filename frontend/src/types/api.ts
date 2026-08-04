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
  // Flat fields returned by the Wren backend (wren/server.py)
  provider?: string;
  model?: string;
  base_url?: string;
  api_key_set?: boolean;
  api_key?: string;
  temperature?: number;
  max_tokens?: number;
  theme?: string;
  font_size?: number;
  tab_size?: number;
  word_wrap?: boolean;
  // Legacy v1 shape kept for backward compatibility
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
export type PipelineStage =
  "architect" | "planner" | "writer" | "reviewer" | "complete";

export interface PipelineStatus {
  task_id: string;
  status: "queued" | "running" | "completed" | "error";
  stage?: PipelineStage;
  progress: number;
  message: string;
  error?: string | null;
}

export interface GenerationRequest {
  prompt: string;
  model?: string;
  output_dir?: string;
  validate?: boolean;
}

export interface GeneratedFile {
  path: string;
  language: string;
  lines: number;
  size_bytes: number;
}

export interface GenerationResult {
  success: boolean;
  project_path?: string;
  files: GeneratedFile[];
  total_files?: number;
  total_lines?: number;
  write_errors?: string[];
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
