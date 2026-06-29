"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listKnowledge,
  searchKnowledge,
  addKnowledgeEntry,
  getKnowledgeEntry,
  getKnowledgeTags,
  getKnowledgeContext,
  type KnowledgeListResponse,
  type KnowledgeEntry,
  type AddKnowledgeRequest,
} from "@/lib/api/knowledge";

export function useKnowledgeList(params: {
  page?: number;
  page_size?: number;
  tag?: string;
}) {
  return useQuery<KnowledgeListResponse>({
    queryKey: ["knowledge-list", params],
    queryFn: () => listKnowledge(params),
  });
}

export function useKnowledgeSearch(query: string) {
  return useQuery({
    queryKey: ["knowledge-search", query],
    queryFn: () => searchKnowledge(query),
    enabled: query.length > 0,
  });
}

export function useKnowledgeEntry(entryId: string | undefined) {
  return useQuery<KnowledgeEntry>({
    queryKey: ["knowledge-entry", entryId],
    queryFn: () => getKnowledgeEntry(entryId!),
    enabled: !!entryId,
  });
}

export function useAddKnowledgeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: AddKnowledgeRequest) => addKnowledgeEntry(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-list"] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-tags"] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-context"] });
    },
  });
}

export function useKnowledgeTags() {
  return useQuery({
    queryKey: ["knowledge-tags"],
    queryFn: () => getKnowledgeTags(),
  });
}

export function useKnowledgeContext(limit = 20) {
  return useQuery<KnowledgeListResponse>({
    queryKey: ["knowledge-context", limit],
    queryFn: () => getKnowledgeContext(limit),
  });
}
