import axios from "axios";
import type { GitRepository } from "#/types/git";
import type {
  AppConversationStartRequest,
  AppConversationStartTask,
  AppConversationStartTaskStatus,
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

  static async getStartTask(
    startTaskId: string,
  ): Promise<AppConversationStartTask> {
    const { data } = await api.get<AppConversationStartTask>(
      `/v1/app-conversations/start-tasks/${startTaskId}`,
    );
    return data;
  }

  static async pollUntilReady(
    startTaskId: string,
    onStatus?: (status: AppConversationStartTaskStatus) => void,
    opts?: { intervalMs?: number; timeoutMs?: number },
  ): Promise<AppConversationStartTask> {
    const intervalMs = opts?.intervalMs ?? 1500;
    const timeoutMs = opts?.timeoutMs ?? 5 * 60 * 1000;
    const deadline = Date.now() + timeoutMs;
    while (true) {
      const task = await this.getStartTask(startTaskId);
      onStatus?.(task.status);
      if (task.status === "READY" || task.status === "ERROR") {
        return task;
      }
      if (Date.now() >= deadline) {
        throw new Error(
          `Timed out after ${timeoutMs}ms waiting for conversation to start (last status: ${task.status})`,
        );
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
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
