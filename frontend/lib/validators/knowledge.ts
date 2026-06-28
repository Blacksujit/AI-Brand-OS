import { z } from "zod";

export const KnowledgeEntrySchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  content: z.string(),
  summary: z.string().nullable(),
  source_type: z.string(),
  source_id: z.string().nullable(),
  tags: z.array(z.string()),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime().nullable(),
});

export const KnowledgeSearchResponseSchema = z.object({
  results: z.array(KnowledgeEntrySchema),
  total: z.number(),
});

export const KnowledgeListResponseSchema = z.object({
  items: z.array(KnowledgeEntrySchema),
  tags: z.array(z.object({ name: z.string(), count: z.number() })),
  total_count: z.number(),
});

export const AddKnowledgeRequestSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(10),
  source_type: z.string().optional(),
  source_id: z.string().optional(),
  tags: z.array(z.string()).optional(),
});

export type KnowledgeEntry = z.infer<typeof KnowledgeEntrySchema>;
export type KnowledgeSearchResponse = z.infer<typeof KnowledgeSearchResponseSchema>;
export type KnowledgeListResponse = z.infer<typeof KnowledgeListResponseSchema>;
export type AddKnowledgeRequest = z.infer<typeof AddKnowledgeRequestSchema>;