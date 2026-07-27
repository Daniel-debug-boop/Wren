import { useMutation, useQuery } from "@tanstack/react-query";
import { generationApi } from "#/api/endpoints";
import type { GenerationRequest } from "#/types/api";

export function useStartGeneration() {
  return useMutation({
    mutationFn: (req: GenerationRequest) => generationApi.start(req),
  });
}

export function useGenerationStatus(taskId: string | null) {
  return useQuery({
    queryKey: ["generation", taskId, "status"],
    queryFn: () => generationApi.status(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.stage === "complete" ? false : 2_000;
    },
  });
}

export function useGenerationResult(taskId: string | null) {
  return useQuery({
    queryKey: ["generation", taskId, "result"],
    queryFn: () => generationApi.result(taskId!),
    enabled: !!taskId,
  });
}
