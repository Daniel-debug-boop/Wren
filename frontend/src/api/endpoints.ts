import apiClient from "./client";
import type {
  ApiKey,
  Conversation,
  ConversationMessage,
  GenerationRequest,
  GenerationResult,
  HealthResponse,
  PipelineStatus,
  Profile,
  ProfilesResponse,
  Secret,
  Settings,
  Skill,
  UserInfo,
} from "#/types/api";

/* ── Health ── */
export const healthApi = {
  check: () => apiClient.get<HealthResponse>("/alive").then((r) => r.data),
};

/* ── Settings ── */
export const settingsApi = {
  get: () => apiClient.get<Settings>("/settings").then((r) => r.data),
  update: (settings: Partial<Settings>) =>
    apiClient.post<Settings>("/settings", settings).then((r) => r.data),
};

/* ── Profiles (LLM) ── */
export const profilesApi = {
  list: () =>
    apiClient.get<ProfilesResponse>("/settings/profiles").then((r) => r.data),
  create: (name: string, config: Partial<Settings>) =>
    apiClient
      .post<Profile>(`/settings/profiles/${encodeURIComponent(name)}`, config)
      .then((r) => r.data),
  delete: (name: string) =>
    apiClient
      .delete(`/settings/profiles/${encodeURIComponent(name)}`)
      .then((r) => r.data),
  activate: (name: string) =>
    apiClient
      .post(`/settings/profiles/${encodeURIComponent(name)}/activate`)
      .then((r) => r.data),
};

/* ── Secrets ── */
export const secretsApi = {
  list: () => apiClient.get<Secret[]>("/secrets").then((r) => r.data),
  set: (name: string, value: string) =>
    apiClient.post("/secrets", { name, value }).then((r) => r.data),
  delete: (name: string) =>
    apiClient
      .delete(`/secrets/${encodeURIComponent(name)}`)
      .then((r) => r.data),
};

/* ── Users ── */
export const userApi = {
  me: () => apiClient.get<UserInfo>("/users/me").then((r) => r.data),
};

/* ── Conversations ── */
export const conversationsApi = {
  list: () =>
    apiClient.get<Conversation[]>("/conversations").then((r) => r.data),
  get: (id: string) =>
    apiClient.get<Conversation>(`/conversations/${id}`).then((r) => r.data),
  create: (title?: string) =>
    apiClient
      .post<Conversation>("/conversations", { title })
      .then((r) => r.data),
  delete: (id: string) =>
    apiClient.delete(`/conversations/${id}`).then((r) => r.data),
  messages: (id: string) =>
    apiClient
      .get<ConversationMessage[]>(`/conversations/${id}/messages`)
      .then((r) => r.data),
  sendMessage: (id: string, content: string) =>
    apiClient
      .post<ConversationMessage>(`/conversations/${id}/messages`, { content })
      .then((r) => r.data),
};

/* ── Generation / Pipeline ── */
export const generationApi = {
  start: (req: GenerationRequest) =>
    apiClient
      .post<{ task_id: string }>("/auto-generations", req)
      .then((r) => r.data),
  status: (taskId: string) =>
    apiClient
      .get<PipelineStatus>(`/auto-generations/${taskId}/status`)
      .then((r) => r.data),
  result: (taskId: string) =>
    apiClient
      .get<GenerationResult>(`/auto-generations/${taskId}/result`)
      .then((r) => r.data),
};

/* ── API Keys ── */
export const apiKeysApi = {
  list: () => apiClient.get<ApiKey[]>("/api-keys").then((r) => r.data),
  create: (name: string) =>
    apiClient.post<ApiKey>("/api-keys", { name }).then((r) => r.data),
  delete: (id: string) =>
    apiClient.delete(`/api-keys/${id}`).then((r) => r.data),
};

/* ── Skills ── */
export const skillsApi = {
  list: () => apiClient.get<Skill[]>("/skills").then((r) => r.data),
  toggle: (name: string, enabled: boolean) =>
    apiClient
      .post(`/skills/${encodeURIComponent(name)}/toggle`, { enabled })
      .then((r) => r.data),
};

/* ── Auth ── */
export const authApi = {
  login: (username: string, password: string) =>
    apiClient
      .post<{ token: string; user: UserInfo }>("/auth/login", {
        username,
        password,
      })
      .then((r) => r.data),
  logout: () => apiClient.post("/auth/logout").then((r) => r.data),
};
