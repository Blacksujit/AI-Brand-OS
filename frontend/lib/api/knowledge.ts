import { apiGet, apiPost } from "./client";

export interface KnowledgeEntry {
  id: string;
  title: string;
  content: string;
  summary?: string;
  source_type: string;
  source_id?: string;
  tags: string[];
  created_at: string;
  updated_at?: string;
}

export interface KnowledgeSearchResponse {
  results: KnowledgeEntry[];
  total: number;
}

export interface KnowledgeListResponse {
  items: KnowledgeEntry[];
  tags: { name: string; count: number }[];
  total_count: number;
}

export interface AddKnowledgeRequest {
  title: string;
  content: string;
  source_type?: string;
  source_id?: string;
  tags?: string[];
}

export async function searchKnowledge(
  query: string,
  limit = 10,
): Promise<KnowledgeSearchResponse> {
  return apiGet<KnowledgeSearchResponse>(
    `/knowledge/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
}

export async function listKnowledge(params: {
  page?: number;
  page_size?: number;
  tag?: string;
}): Promise<KnowledgeListResponse> {
  return apiGet<KnowledgeListResponse>(
    "/knowledge/entries",
    params as Record<string, string | number | undefined>,
  );
}

export async function getKnowledgeEntry(
  entryId: string,
): Promise<KnowledgeEntry> {
  return apiGet<KnowledgeEntry>(`/knowledge/entries/${entryId}`);
}

export async function addKnowledgeEntry(
  request: AddKnowledgeRequest,
): Promise<KnowledgeEntry> {
  return apiPost<KnowledgeEntry>("/knowledge/entries", request);
}

export async function getKnowledgeTags(): Promise<
  { name: string; count: number }[]
> {
  return apiGet("/knowledge/tags");
}

export async function getKnowledgeContext(
  limit = 20,
): Promise<KnowledgeListResponse> {
  return apiGet<KnowledgeListResponse>(
    `/knowledge/context?limit=${limit}`,
  );
}
