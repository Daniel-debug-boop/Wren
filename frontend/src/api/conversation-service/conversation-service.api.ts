import axios from "axios";
import type { GitRepository } from "#/types/git";
import type {
  AppConversationStartRequest,
  AppConversationStartTask,
  AppConversation,
  AppConversationPage,
} from "#/types/app-conversation";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface AppConversationStartRequest {
  sandbox_id?: string;
  conversation_id?: string;
  initial_message?: {
    role: "user";
    content: Array<{ type: "text"; text: string }>;
  };
  system_message_suffix?: string;
  llm_model?: string;
  selected_repository?: string;
  selected_branch?: string;
  git_provider?: string;
  title?: string;
  trigger?: string;
  agent_type?: "default" | "plan";
  mode?: "plan" | "code" | "review" | "debug" | "ask" | "video";
  plugins?: Array<{
    source: string;
    ref?: string;
    repo_path?: string;
    parameters?: Record<string, unknown>;
  }>;
  secrets?: Record<string, string>;
}

export class ConversationApi {
  static async startConversation(
    request: AppConversationStartRequest,
  ): Promise<AppConversationStartTask> {
    const { data } = await api.post<AppConversationStartTask>(
      "/v1/app-conversations",
      request,
    );
    return data;
  }

  static async getConversation(id: string): Promise<AppConversation> {
    const { data } = await api.get<AppConversation>(
      `/v1/app-conversations/${id}`,
    );
    return data;
  }

  static async listConversations(params?: {
    page_id?: string;
    sort_order?: string;
    trigger?: string;
  }): Promise<AppConversationPage> {
    const { data } = await api.get<AppConversationPage>(
      "/v1/app-conversations",
      { params },
    );
    return data;
  }

  static async sendMessage(
    conversationId: string,
    content: string,
  ): Promise<{ success: boolean; sandbox_status: string; message?: string }> {
    const { data } = await api.post(
      `/v1/app-conversations/${conversationId}/send-message`,
      {
        role: "user",
        content: [{ type: "text", text: content }],
        run: true,
      },
    );
    return data;
  }

  static async resumeConversation(
    conversationId: string,
  ): Promise<{ success: boolean }> {
    const { data } = await api.post(
      `/v1/app-conversations/${conversationId}/resume`,
    );
    return data;
  }

  static async getRepositories(): Promise<{ items: GitRepository[] }> {
    const { data } = await api.get("/v1/git/repositories");
    return data;
  }

  static async getBranches(repositoryId: string): Promise<{
    items: Array<{ name: string; commit_sha: string; protected: boolean }>;
  }> {
    const { data } = await api.get(
      `/v1/git/repositories/${repositoryId}/branches`,
    );
    return data;
  }
}
