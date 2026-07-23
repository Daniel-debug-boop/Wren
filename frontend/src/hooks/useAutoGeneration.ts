import { useCallback, useEffect, useRef } from "react";
import { useGenerationStore } from "#/stores/useGenerationStore";
import AutoGenerationApi from "#/api/auto-generation-service/auto-generation-service.api";

export function useAutoGeneration() {
  const store = useGenerationStore();
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ── Timer for elapsed display ── */
  useEffect(() => {
    if (store.status === "running") {
      tickRef.current = setInterval(() => {
        useGenerationStore.getState().tick();
      }, 200);
    }
    return () => {
      if (tickRef.current) {
        clearInterval(tickRef.current);
        tickRef.current = null;
      }
    };
  }, [store.status]);

  /* ── Start generation ── */
  const startGeneration = useCallback(
    async (prompt: string, options?: { model?: string; validate?: boolean }) => {
      const api = useGenerationStore.getState();

      try {
        /* ── 1. Initiate via API ── */
        const { task_id } = await AutoGenerationApi.startGeneration({
          prompt,
          model: options?.model ?? "gpt-4o",
          validate: options?.validate ?? true,
        });

        /* ── 2. Update store ── */
        useGenerationStore.getState().startGeneration(prompt, task_id);

        /* ── 3. Poll until done ── */
        const result = await AutoGenerationApi.pollUntilDone(
          task_id,
          (event) => {
            const state = useGenerationStore.getState();
            const stageIndex = event.stage - 1;

            if (stageIndex >= 0 && stageIndex < state.stages.length) {
              switch (event.status) {
                case "running":
                  state.setStageStatus(stageIndex, "running");
                  break;
                case "done":
                  state.setStageStatus(stageIndex, "done", event.detail);
                  break;
                case "error":
                  state.setStageStatus(stageIndex, "error", event.detail);
                  break;
              }
            }

            if (event.file_path) {
              state.updateFileStatus(event.file_path, {
                path: event.file_path,
                status:
                  event.status === "done"
                    ? "done"
                    : event.status === "error"
                      ? "error"
                      : event.status === "correcting"
                        ? "correcting"
                        : "generating",
              });
            }
          },
        );

        /* ── 4. Complete ── */
        useGenerationStore.getState().completeResult(result);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Generation failed unexpectedly";
        useGenerationStore.getState().setError(message);
      }
    },
    [],
  );

  /* ── Cancel generation ── */
  const cancelGeneration = useCallback(async () => {
    const { taskId } = useGenerationStore.getState();
    if (taskId) {
      try {
        await AutoGenerationApi.cancelGeneration(taskId);
      } catch {
        // ignore cleanup errors
      }
    }
    useGenerationStore.getState().reset();
  }, []);

  /* ── Reset ── */
  const reset = useCallback(() => {
    useGenerationStore.getState().reset();
  }, []);

  return {
    /* ── State ── */
    status: store.status,
    prompt: store.prompt,
    projectName: store.projectName,
    stages: store.stages,
    files: store.files,
    result: store.result,
    error: store.error,
    elapsedMs: store.elapsedMs,

    /* ── Derived ── */
    isRunning: store.status === "running",
    isDone: store.status === "done",
    isError: store.status === "error",
    fileCount: store.files.length,
    stageCount: store.stages.length,

    /* ── Actions ── */
    startGeneration,
    cancelGeneration,
    reset,
  };
}
