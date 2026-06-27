import { apiGet, apiPost } from "./client";

export interface TrendTopic {
  id: string;
  name: string;
  description: string;
  signal_count: number;
  velocity_score: number;
  relevance_score: number;
  category: string;
  created_at: string;
}

export interface TrendTopicListResponse {
  topics: TrendTopic[];
  total: number;
  page: number;
  page_size: number;
}

export async function getTrendingTopics(params: {
  limit?: number;
  page?: number;
  page_size?: number;
}): Promise<TrendTopicListResponse> {
  return apiGet<TrendTopicListResponse>(
    "/trends/topics",
    params as Record<string, string | number | undefined>,
  );
}
