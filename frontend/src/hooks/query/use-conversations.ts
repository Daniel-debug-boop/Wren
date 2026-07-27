import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { conversationsApi } from "#/api/endpoints";
import type { Conversation } from "#/types/api";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: conversationsApi.list,
    staleTime: 30_000,
  });
}

export function useConversation(id: string) {
  return useQuery({
    queryKey: ["conversation", id],
    queryFn: () => conversationsApi.get(id),
    enabled: !!id,
  });
}

export function useConversationMessages(id: string) {
  return useQuery({
    queryKey: ["conversation", id, "messages"],
    queryFn: () => conversationsApi.messages(id),
    enabled: !!id,
    refetchInterval: 5_000,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => conversationsApi.create(title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => conversationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => conversationsApi.sendMessage(conversationId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversation", conversationId, "messages"] });
    },
  });
}
