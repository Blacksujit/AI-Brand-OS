import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type EvaluateRequest,
  type GeneratedPost,
  type HistoryResponse,
  type PipelineRequest,
  type PipelineStatus,
  generateContent,
  generateIdeas,
  evaluateContent,
  getHistory,
  getHistoryRecord,
  updateRecordStatus,
} from "./content";
import { getTrendingTopics, type TrendTopicListResponse } from "./trends";

// ─── Pipeline ───────────────────────────────────────────────────────────────

export function useGenerateContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: PipelineRequest) => generateContent(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-history"] });
    },
  });
}

// ─── Ideas ──────────────────────────────────────────────────────────────────

export function useGenerateIdeas() {
  return useMutation({
    mutationFn: (request: { topic?: string; platform?: string; count?: number }) =>
      generateIdeas(request),
  });
}

// ─── Evaluation ─────────────────────────────────────────────────────────────

export function useEvaluateContent() {
  return useMutation({
    mutationFn: (request: EvaluateRequest) => evaluateContent(request),
  });
}

// ─── History ────────────────────────────────────────────────────────────────

export function useContentHistory(params: {
  page?: number;
  page_size?: number;
  platform?: string;
  status?: string;
}) {
  return useQuery<HistoryResponse>({
    queryKey: ["content-history", params],
    queryFn: () => getHistory(params),
  });
}

export function useContentRecord(recordId: string | undefined) {
  return useQuery<GeneratedPost>({
    queryKey: ["content-record", recordId],
    queryFn: () => getHistoryRecord(recordId!),
    enabled: !!recordId,
  });
}

export function useUpdateRecordStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      recordId,
      status,
    }: {
      recordId: string;
      status: "draft" | "published" | "archived";
    }) => updateRecordStatus(recordId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["content-history"] });
    },
  });
}

// ─── Briefs ──────────────────────────────────────────────────────────────────

export function useBriefs(params?: { limit?: number }) {
  return useQuery({
    queryKey: ["briefs", params],
    queryFn: async () => {
      // Generate brief ideas on-the-fly. Falls back gracefully if not supported.
      try {
        const ideas = await generateIdeas({ count: params?.limit ?? 5 });
        return ideas.length > 0
          ? [
              {
                id: "today",
                title: "Today's Content Brief",
                ideas,
                created_at: new Date().toISOString(),
              },
            ]
          : [];
      } catch {
        return [];
      }
    },
    staleTime: 5 * 60_000,
    retry: false,
  });
}

// ─── Trends ──────────────────────────────────────────────────────────────────

export function useTrendingTopics(params?: { limit?: number }) {
  return useQuery<TrendTopicListResponse>({
    queryKey: ["trending-topics", params],
    queryFn: () => getTrendingTopics(params ?? {}),
  });
}

// ─── Pipeline Polling ───────────────────────────────────────────────────────

const PIPELINE_POLL_INTERVAL = 2000;

export function usePipelinePolling(pipelineId: string | null) {
  return useQuery<PipelineStatus>({
    queryKey: ["pipeline-status", pipelineId],
    queryFn: async () => {
      const { getPipelineStatus } = await import("./content");
      return getPipelineStatus(pipelineId!);
    },
    enabled: !!pipelineId,
    refetchInterval: (query) =>
      query.state.data?.is_complete ? false : PIPELINE_POLL_INTERVAL,
  });
}
