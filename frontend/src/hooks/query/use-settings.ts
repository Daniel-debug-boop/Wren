import { useQuery } from "@tanstack/react-query";
import { settingsApi } from "#/api/endpoints";

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: settingsApi.get,
    staleTime: 60_000,
  });
}
