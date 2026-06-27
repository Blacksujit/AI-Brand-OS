import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  type EvaluateRequest,
  type HistoryResponse,
  type Idea,
  type PipelineRequest,
  type PipelineStatus,
  generateContent,
  generateIdeas,
  evaluateContent,
  getHistory,
  getHistoryRecord,
  updateRecordStatus,
} from "./content";

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
  return useQuery({
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
