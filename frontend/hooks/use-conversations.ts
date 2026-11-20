"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { chatService } from "@/services/chat-service";

export function useConversations() {
  return useQuery({
    queryKey: ["conversations"],
    queryFn: () => chatService.listConversations(),
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: ["conversations", conversationId],
    queryFn: () => chatService.getConversation(conversationId as string),
    enabled: Boolean(conversationId),
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (conversationId: string) => chatService.deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
}
