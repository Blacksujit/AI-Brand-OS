import { z } from "zod";

export const GenerateRequestSchema = z.object({
  topic: z.string().optional(),
  platform: z.enum(["linkedin", "twitter", "medium", "newsletter"]),
  tone: z.enum(["professional", "conversational", "thought-leadership", "educational"]),
  max_length: z.number().int().min(50).max(3000).optional(),
});

export const PipelineStatusSchema = z.object({
  pipeline_id: z.string().uuid(),
  is_complete: z.boolean(),
  current_step: z.string(),
  steps_completed: z.array(z.string()),
  errors: z.array(z.object({ step: z.string(), error: z.string() })),
  duration_ms: z.number(),
  requires_human_approval: z.boolean(),
});

export const GeneratedPostSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  body: z.string(),
  hook: z.string().nullable(),
  call_to_action: z.string().nullable(),
  hashtags: z.array(z.string()),
  quality_score: z.number().nullable(),
  review_feedback: z.string().nullable(),
  status: z.enum(["draft", "published", "archived"]),
  platform: z.string(),
  created_at: z.string().datetime(),
  published_at: z.string().datetime().nullable(),
});

export const HistoryResponseSchema = z.object({
  records: z.array(GeneratedPostSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
});

export const RegenerateRequestSchema = z.object({
  pipeline_id: z.string().uuid(),
});

export const EvaluateRequestSchema = z.object({
  title: z.string(),
  body: z.string(),
  platform: z.string().optional(),
});

export const EvaluateResponseSchema = z.object({
  score: z.number(),
  verdict: z.string(),
  feedback: z.string(),
  issues: z.array(z.string()),
  strengths: z.array(z.string()),
});

export const IdeasRequestSchema = z.object({
  topic: z.string().optional(),
  platform: z.string().optional(),
  count: z.number().int().min(1).max(20).optional(),
});

export const IdeaSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  description: z.string(),
  relevance_score: z.number(),
  platform: z.string(),
});

export type GenerateRequest = z.infer<typeof GenerateRequestSchema>;
export type PipelineStatus = z.infer<typeof PipelineStatusSchema>;
export type GeneratedPost = z.infer<typeof GeneratedPostSchema>;
export type HistoryResponse = z.infer<typeof HistoryResponseSchema>;
export type RegenerateRequest = z.infer<typeof RegenerateRequestSchema>;
export type EvaluateRequest = z.infer<typeof EvaluateRequestSchema>;
export type EvaluateResponse = z.infer<typeof EvaluateResponseSchema>;
export type IdeasRequest = z.infer<typeof IdeasRequestSchema>;
export type Idea = z.infer<typeof IdeaSchema>;