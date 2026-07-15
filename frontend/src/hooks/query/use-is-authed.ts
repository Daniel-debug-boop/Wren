import { useQuery } from "@tanstack/react-query";
import AuthService from "#/api/auth-service/auth-service.api";

export function useIsAuthed() {
  return useQuery<boolean>({
    queryKey: ["auth", "is-authed"],
    queryFn: () => AuthService.authenticate(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}
