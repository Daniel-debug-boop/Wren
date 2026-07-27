import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { profilesApi } from "#/api/endpoints";

export function useProfiles() {
  return useQuery({
    queryKey: ["profiles"],
    queryFn: profilesApi.list,
    staleTime: 60_000,
  });
}

export function useActivateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => profilesApi.activate(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profiles"] });
    },
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => profilesApi.delete(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profiles"] });
    },
  });
}
