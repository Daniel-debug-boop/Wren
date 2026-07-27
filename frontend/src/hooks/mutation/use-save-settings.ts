import { useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsApi } from "#/api/endpoints";
import type { Settings } from "#/types/api";

export function useSaveSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: Partial<Settings>) => settingsApi.update(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}
