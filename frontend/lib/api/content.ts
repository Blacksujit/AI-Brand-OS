import { apiGet, apiPatch, apiPost } from "./client";

export interface PipelineRequest {
  topic?: string;
  platform?: string;
  tone?: string;
  max_length?: number;
  pipeline_type?: "daily_brief" | "draft_generation" | "analytics";
}

export interface PipelineStatus {
  pipeline_id: string;
  is_complete: boolean;
  current_step: string;
  steps_completed: string[];
  errors: { step: string; error: string }[];
  duration_ms: number;
  requires_human_approval: boolean;
}

export interface IdeasRequest {
  topic?: string;
  platform?: string;
  count?: number;
}

export interface Idea {
  id: string;
  title: string;
  description: string;
  relevance_score: number;
  platform: string;
}

export interface EvaluateRequest {
  title: string;
  body: string;
  platform?: string;
}

export interface EvaluateResponse {
  score: number;
  verdict: string;
  feedback: string;
  issues: string[];
  strengths: string[];
}

export interface GeneratedPost {
  id: string;
  title: string;
  body: string;
  hook: string | null;
  call_to_action: string | null;
  hashtags: string[];
  quality_score: number | null;
  review_feedback: string | null;
  status: "draft" | "published" | "archived";
  platform: string;
  created_at: string;
  published_at: string | null;
}

export interface HistoryResponse {
  records: GeneratedPost[];
  total: number;
  page: number;
  page_size: number;
}

export async function generateContent(
  request: PipelineRequest,
): Promise<PipelineStatus> {
  return apiPost<PipelineStatus>("/content/generate", request);
}

export async function getPipelineStatus(
  pipelineId: string,
): Promise<PipelineStatus> {
  return apiGet<PipelineStatus>(`/content/pipeline/${pipelineId}`);
}

export async function getPipelineOutput(
  pipelineId: string,
): Promise<Record<string, unknown>> {
  return apiGet(`/content/pipeline/${pipelineId}/output`);
}

export async function generateIdeas(
  request: IdeasRequest,
): Promise<Idea[]> {
  return apiPost<Idea[]>("/content/ideas", request);
}

export async function evaluateContent(
  request: EvaluateRequest,
): Promise<EvaluateResponse> {
  return apiPost<EvaluateResponse>("/content/evaluate", request);
}

export async function getHistory(params: {
  page?: number;
  page_size?: number;
  platform?: string;
  status?: string;
}): Promise<HistoryResponse> {
  return apiGet<HistoryResponse>("/content/history", params as Record<string, string | number | undefined>);
}

export async function getHistoryRecord(
  recordId: string,
): Promise<GeneratedPost> {
  return apiGet<GeneratedPost>(`/content/history/${recordId}`);
}

export async function updateRecordStatus(
  recordId: string,
  status: "draft" | "published" | "archived",
): Promise<GeneratedPost> {
  return apiPatch<GeneratedPost>(
    `/content/history/${recordId}/status?status=${status}`,
  );
}
