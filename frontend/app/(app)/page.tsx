"use client";

import Link from "next/link";
import { useContentHistory } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";
import { QualityBadge } from "@/components/content/quality-badge";

export default function Dashboard() {
  const { data: historyData } = useContentHistory({ page: 1, page_size: 5 });

  const totalCount = historyData?.total ?? 0;
  const publishedCount =
    historyData?.records.filter((r) => r.status === "published").length ?? 0;
  const avgScore = historyData?.records.length
    ? historyData.records.reduce(
        (sum, r) => sum + (r.quality_score ?? 0),
        0,
      ) / historyData.records.length
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to BrandOS. Your AI content engine is ready.
          </p>
        </div>
        <Link href="/content">
          <Button>New Content</Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border p-4">
          <p className="text-3xl font-bold">{totalCount}</p>
          <p className="text-sm text-muted-foreground">Pieces Generated</p>
        </div>
        <div className="rounded-lg border p-4">
          <p className="text-3xl font-bold">{publishedCount}</p>
          <p className="text-sm text-muted-foreground">Published</p>
        </div>
        <div className="rounded-lg border p-4">
          <p className="text-3xl font-bold">
            {avgScore > 0 ? `${Math.round(avgScore * 100)}%` : "N/A"}
          </p>
          <p className="text-sm text-muted-foreground">Avg Quality Score</p>
        </div>
      </div>

      <div className="rounded-lg border p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Recent Content</h3>
          <Link
            href="/history"
            className="text-sm text-primary hover:underline"
          >
            View all
          </Link>
        </div>
        {historyData?.records.length ? (
          <div className="space-y-2">
            {historyData.records.map((record) => (
              <div
                key={record.id}
                className="flex items-center justify-between rounded-md p-2 hover:bg-muted/50 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">
                    {record.title}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {record.platform} ·{" "}
                    {new Date(record.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <QualityBadge score={record.quality_score} />
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs capitalize text-muted-foreground">
                    {record.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No content yet. Generate your first piece!
          </p>
        )}
      </div>
    </div>
  );
}
