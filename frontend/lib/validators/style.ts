import { z } from "zod";

export const StyleProfileSchema = z.object({
  style_params: z.record(z.string(), z.number()),
  voice_embedding: z.array(z.number()).nullable(),
  learning_rate: z.number(),
  confidence: z.number(),
  total_ratings: z.number(),
  total_edits: z.number(),
  total_approved: z.number(),
});

export const RateDraftRequestSchema = z.object({
  draft_id: z.string().uuid(),
  score: z.number().int().min(1).max(5),
  comment: z.string().optional(),
  dimension_scores: z.record(z.string(), z.number().int().min(1).max(5)).optional(),
});

export const StyleAnalysisResponseSchema = z.object({
  lexical_match: z.number(),
  syntactic_match: z.number(),
  tonal_match: z.number(),
  structural_match: z.number(),
  overall_match: z.number(),
  deviations: z.record(z.string(), z.string()),
});

export const StyleInsightItemSchema = z.object({
  dimension: z.string(),
  message: z.string(),
  severity: z.enum(["info", "warning", "critical"]),
});

export const StyleInsightsResponseSchema = z.object({
  insights: z.array(StyleInsightItemSchema),
});

export const StyleProgressResponseSchema = z.object({
  progress: z.array(z.object({
    timestamp: z.string().datetime(),
    confidence: z.number(),
    signal_count: z.number(),
  })),
});

export type StyleProfile = z.infer<typeof StyleProfileSchema>;
export type RateDraftRequest = z.infer<typeof RateDraftRequestSchema>;
export type StyleAnalysisResponse = z.infer<typeof StyleAnalysisResponseSchema>;
export type StyleInsightItem = z.infer<typeof StyleInsightItemSchema>;
export type StyleInsightsResponse = z.infer<typeof StyleInsightsResponseSchema>;
export type StyleProgressResponse = z.infer<typeof StyleProgressResponseSchema>;