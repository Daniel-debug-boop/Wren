import { useQuery } from "@tanstack/react-query";
import OptionService from "#/api/option-service/option-service.api";
import type { AppConfig } from "#/types/config";

export function useConfig() {
  return useQuery<AppConfig>({
    queryKey: ["config"],
    queryFn: () => OptionService.getConfig(),
    staleTime: 10 * 60 * 1000,
  });
}
