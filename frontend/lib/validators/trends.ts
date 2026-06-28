import { z } from "zod";

export const TrendTopicSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string(),
  signal_count: z.number(),
  velocity_score: z.number(),
  relevance_score: z.number(),
  category: z.string(),
  created_at: z.string().datetime(),
});

export const TrendTopicListResponseSchema = z.object({
  topics: z.array(TrendTopicSchema),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
});

export const TrendAnalysisResponseSchema = z.object({
  insights: z.string(),
  recommendations: z.array(z.string()).nullable(),
  confidence: z.number(),
  generated_for: z.string().nullable(),
});

export type TrendTopic = z.infer<typeof TrendTopicSchema>;
export type TrendTopicListResponse = z.infer<typeof TrendTopicListResponseSchema>;
export type TrendAnalysisResponse = z.infer<typeof TrendAnalysisResponseSchema>;