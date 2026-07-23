import { create } from "zustand";
import type { GenerationStage, FileStatus, GenerationResult } from "#/api/auto-generation-service/auto-generation-service.api";

export type PipelineStatus = "idle" | "running" | "done" | "error";

interface GenerationState {
  /* ── Pipeline state ── */
  status: PipelineStatus;
  prompt: string;
  projectName: string;

  /* ── Stages ── */
  stages: GenerationStage[];

  /* ── Files ── */
  files: FileStatus[];

  /* ── Result ── */
  result: GenerationResult | null;
  error: string | null;

  /* ── Timing ── */
  startedAt: number | null;
  elapsedMs: number;

  /* ── Task tracking ── */
  taskId: string | null;

  /* ── Actions ── */
  startGeneration: (prompt: string, taskId: string) => void;
  updateStage: (stageIndex: number, updates: Partial<GenerationStage>) => void;
  updateFileStatus: (filePath: string, updates: Partial<FileStatus>) => void;
  setStageStatus: (stageIndex: number, status: GenerationStage["status"], detail?: string) => void;
  completeResult: (result: GenerationResult) => void;
  setError: (error: string) => void;
  tick: () => void;
  reset: () => void;
}

export const useGenerationStore = create<GenerationState>((set) => ({
  status: "idle",
  prompt: "",
  projectName: "",
  stages: [],
  files: [],
  result: null,
  error: null,
  startedAt: null,
  elapsedMs: 0,
  taskId: null,

  startGeneration: (prompt, taskId) =>
    set({
      status: "running",
      prompt,
      taskId,
      startedAt: Date.now(),
      elapsedMs: 0,
      stages: [
        { name: "File Tree Blueprinting", index: 1, total: 3, status: "running" },
        { name: "Sequential File Generation", index: 2, total: 3, status: "pending" },
        { name: "Validation & Self-Correction", index: 3, total: 3, status: "pending" },
      ],
      files: [],
      result: null,
      error: null,
    }),

  updateStage: (stageIndex, updates) =>
    set((s) => ({
      stages: s.stages.map((st, i) =>
        i === stageIndex ? { ...st, ...updates } : st,
      ),
    })),

  updateFileStatus: (filePath, updates) =>
    set((s) => {
      const exists = s.files.find((f) => f.path === filePath);
      if (exists) {
        return {
          files: s.files.map((f) =>
            f.path === filePath ? { ...f, ...updates } : f,
          ),
        };
      }
      return {
        files: [
          ...s.files,
          {
            path: filePath,
            status: "pending",
            ...updates,
          } as FileStatus,
        ],
      };
    }),

  setStageStatus: (stageIndex, status, detail) =>
    set((s) => ({
      stages: s.stages.map((st, i) =>
        i === stageIndex
          ? { ...st, status, detail: detail ?? st.detail }
          : st,
      ),
    })),

  completeResult: (result) =>
    set((s) => ({
      status: result.success ? "done" : "error",
      result,
      projectName: result.project_name,
      error: result.success ? null : "Generation completed with errors",
      stages: result.stages.map((st) => ({
        ...st,
        status: st.success ? "done" : "error",
      })) as GenerationStage[],
      files: result.files.map((f) => ({
        path: f.path,
        status: f.success ? "done" : "error",
        error: f.error,
      })),
      elapsedMs: Date.now() - (s.startedAt ?? Date.now()),
    })),

  setError: (error) =>
    set({
      status: "error",
      error,
    }),

  tick: () =>
    set((s) => ({
      elapsedMs: s.startedAt ? Date.now() - s.startedAt : s.elapsedMs,
    })),

  reset: () =>
    set({
      status: "idle",
      prompt: "",
      projectName: "",
      stages: [],
      files: [],
      result: null,
      error: null,
      startedAt: null,
      elapsedMs: 0,
      taskId: null,
    }),
}));
