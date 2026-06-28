"use client";

import Link from "next/link";
import { useContentHistory } from "@/lib/api/hooks";
import { useTrendingTopics } from "@/lib/api/hooks";
import { Button } from "@/features/ui";
import { QualityBadge } from "@/features/ui/QualityBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { Badge } from "@/features/ui/Badge";
import { ArrowUpRight, ExternalLink, Loader2, Sparkles } from "lucide-react";

export default function Dashboard() {
  const { data: historyData, isLoading: historyLoading } = useContentHistory({ page: 1, page_size: 5 });
  const { data: trendsData, isLoading: trendsLoading } = useTrendingTopics({ limit: 5 });

  const totalCount = historyData?.total ?? 0;
  const publishedCount = historyData?.records.filter((r) => r.status === "published").length ?? 0;
  const avgScore = historyData?.records.length
    ? historyData.records.reduce((sum, r) => sum + (r.quality_score ?? 0), 0) / historyData.records.length
    : 0;

  const stats = [
    { label: "Pieces Generated", value: totalCount, icon: Sparkles },
    { label: "Published", value: publishedCount, icon: ExternalLink },
    { label: "Avg Quality Score", value: avgScore > 0 ? `${Math.round(avgScore * 100)}%` : "N/A", icon: ArrowUpRight },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Welcome to BrandOS. Your AI content engine is ready.</p>
        </div>
        <Link href="/app/content">
          <Button>New Content</Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {stats.map((stat, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <stat.icon className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-3xl font-bold">{stat.value}</p>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">Recent Content</CardTitle>
            <Link href="/app/history" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded-md bg-muted" />
                ))}
              </div>
            ) : historyData?.records.length ? (
              <div className="space-y-3">
                {historyData.records.map((record) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between rounded-md p-3 hover:bg-muted/50 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{record.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {record.platform} · {new Date(record.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <QualityBadge score={record.quality_score} />
                      <Badge variant="outline" className="text-xs">
                        {record.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Sparkles className="h-10 w-10 text-muted-foreground/50 mb-3" />
                <p className="text-muted-foreground">No content yet</p>
                <p className="text-sm text-muted-foreground">Generate your first piece of content!</p>
                <Link href="/app/content" className="mt-4">
                  <Button size="sm"><Sparkles className="mr-2 h-4 w-4" /> New Content</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg">Trending Topics</CardTitle>
            <Link href="/app/trends" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {trendsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded-md bg-muted" />
                ))}
              </div>
            ) : trendsData?.topics.length ? (
              <div className="space-y-3">
                {trendsData.topics.map((topic) => (
                  <Link
                    key={topic.id}
                    href={`/app/content?topic=${encodeURIComponent(topic.name)}`}
                    className="block rounded-md p-3 hover:bg-muted/50 transition-colors"
                  >
                    <p className="font-medium truncate">{topic.name}</p>
                    <p className="text-xs text-muted-foreground truncate mt-1">{topic.description}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">{topic.category}</Badge>
                      <span>Velocity: {Math.round(topic.velocity_score * 100)}%</span>
                      <span>{topic.signal_count} signals</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Loader2 className="h-10 w-10 text-muted-foreground/50 animate-spin mb-3" />
                <p className="text-muted-foreground">No trending topics available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}