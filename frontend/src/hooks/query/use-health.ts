import { useQuery } from "@tanstack/react-query";
import { healthApi } from "#/api/endpoints";

export function useHealthCheck() {
  return useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    retry: 3,
    retryDelay: 2_000,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
