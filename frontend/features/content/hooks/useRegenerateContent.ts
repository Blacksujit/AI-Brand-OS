import { useMutation, useQuery } from "@tanstack/react-query";
import { apiPost, apiGet } from "@/lib/api/client";
import { PipelineStatus, GeneratedPost } from "@/lib/validators/content";

export function useRegenerateContent() {
  return useMutation({
    mutationFn: (pipelineId: string) =>
      apiPost<PipelineStatus>("/content/regenerate", { pipeline_id: pipelineId }),
  });
}

export function useGeneratedContent(pipelineId: string | null) {
  return useQuery<GeneratedPost>({
    queryKey: ["pipeline-output", pipelineId],
    queryFn: () => apiGet<GeneratedPost>(`/content/pipeline/${pipelineId}/output`),
    enabled: !!pipelineId,
  });
}