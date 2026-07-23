import axios from "axios";

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

/* ── Types ── */

export interface FileSpec {
  path: string;
  purpose: string;
}

export interface Manifest {
  project_name: string;
  files: FileSpec[];
}

export interface GenerationStage {
  name: string;
  index: number;
  total: number;
  status: "pending" | "running" | "done" | "error";
  detail?: string;
  duration_s?: number;
}

export interface FileStatus {
  path: string;
  status: "pending" | "generating" | "done" | "error" | "correcting";
  error?: string;
}

export interface GenerationResult {
  success: boolean;
  project_name: string;
  output_dir: string;
  files: Array<{
    path: string;
    success: boolean;
    error?: string;
  }>;
  stages: GenerationStage[];
  total_duration_s: number;
}

export interface GenerationProgressEvent {
  stage: number;
  stage_name: string;
  file_index: number;
  file_total: number;
  file_path: string;
  status: string;
  detail?: string;
}

/* ── Options for starting generation ── */

export interface StartGenerationRequest {
  prompt: string;
  model?: string;
  base_url?: string;
  output_dir?: string;
  max_tokens?: number;
  temperature?: number;
  validate?: boolean;
  resume?: boolean;
}

/* ── API Service ── */

export class AutoGenerationApi {
  /**
   * Start a new auto-generation pipeline.
   * Returns a task ID that can be polled for progress.
   */
  static async startGeneration(
    request: StartGenerationRequest,
  ): Promise<{ task_id: string; project_name: string }> {
    const { data } = await api.post("/v1/auto-generation/start", request);
    return data;
  }

  /**
   * Poll generation task status.
   */
  static async getGenerationStatus(
    taskId: string,
  ): Promise<{
    status: "queued" | "running" | "done" | "error";
    progress?: GenerationProgressEvent;
    result?: GenerationResult;
    error?: string;
  }> {
    const { data } = await api.get(`/v1/auto-generation/${taskId}/status`);
    return data;
  }

  /**
   * Cancel a running generation task.
   */
  static async cancelGeneration(taskId: string): Promise<{ success: boolean }> {
    const { data } = await api.post(`/v1/auto-generation/${taskId}/cancel`);
    return data;
  }

  /**
   * List all completed generation projects.
   */
  static async listProjects(): Promise<{
    items: Array<{
      project_name: string;
      output_dir: string;
      created_at: string;
      file_count: number;
      success: boolean;
    }>;
  }> {
    const { data } = await api.get("/v1/auto-generation/projects");
    return data;
  }

  /**
   * Poll until generation completes, with progress callback.
   */
  static async pollUntilDone(
    taskId: string,
    onProgress?: (event: GenerationProgressEvent) => void,
    opts?: { intervalMs?: number; timeoutMs?: number },
  ): Promise<GenerationResult> {
    const intervalMs = opts?.intervalMs ?? 1500;
    const timeoutMs = opts?.timeoutMs ?? 10 * 60 * 1000;
    const deadline = Date.now() + timeoutMs;

    while (true) {
      const status = await this.getGenerationStatus(taskId);

      if (status.progress && onProgress) {
        onProgress(status.progress);
      }

      if (status.status === "done" && status.result) {
        return status.result;
      }

      if (status.status === "error") {
        throw new Error(status.error ?? "Generation failed");
      }

      if (Date.now() >= deadline) {
        throw new Error(`Timed out after ${timeoutMs}ms waiting for generation`);
      }

      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
  }
}

export default AutoGenerationApi;
