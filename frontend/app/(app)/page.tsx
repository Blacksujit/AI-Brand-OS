"use client";

import Link from "next/link";
import { Suspense } from "react";
import { Sparkles, ExternalLink, Star, Hash, ArrowUpRight } from "lucide-react";
import { useContentHistory, useTrendingTopics } from "@/lib/api/hooks";
import { useBriefs } from "@/lib/api/hooks";
import { Button } from "@/features/ui/Button";
import { QualityBadge } from "@/features/ui/QualityBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { Badge } from "@/features/ui/Badge";
import { Skeleton } from "@/features/ui/Skeleton";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { MetricCardsGridSkeleton } from "@/components/dashboard/MetricCardsGridSkeleton";
import { RecentContentSkeleton } from "@/components/dashboard/RecentContentSkeleton";

function DashboardMetrics() {
  const { data: historyData, isLoading } = useContentHistory({ page: 1, page_size: 5 });

  if (isLoading) return <MetricCardsGridSkeleton />;

  const totalCount = historyData?.total ?? 0;
  const publishedCount = historyData?.records.filter((r) => r.status === "published").length ?? 0;
  const avgScore = historyData?.records.length
    ? historyData.records.reduce((sum, r) => sum + (r.quality_score ?? 0), 0) / historyData.records.length
    : 0;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        icon={Sparkles}
        label="Pieces Generated"
        value={totalCount}
        subtext="All time"
        className="hover:shadow-md transition-shadow duration-200"
      />
      <MetricCard
        icon={ExternalLink}
        label="Published"
        value={publishedCount}
        subtext={`${totalCount > 0 ? Math.round((publishedCount / totalCount) * 100) : 0}% publish rate`}
        className="hover:shadow-md transition-shadow duration-200"
      />
      <MetricCard
        icon={Star}
        label="Avg Quality Score"
        value={avgScore > 0 ? `${Math.round(avgScore * 100)}%` : "—"}
        trend={avgScore > 0.5 ? { value: 12, positive: true } : undefined}
        className="hover:shadow-md transition-shadow duration-200"
      />
      <MetricCard
        icon={Hash}
        label="Ideas Available"
        value="—"
        subtext="Connect GitHub to start"
        className="hover:shadow-md transition-shadow duration-200"
      />
    </div>
  );
}

function BriefCard() {
  const { data: briefs, isLoading } = useBriefs({ limit: 1 });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const brief = briefs?.[0];

  if (!brief?.ideas?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Today&apos;s Content Brief
          </CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Sparkles}
            title="No brief yet"
            description="Connect GitHub and save knowledge items to get personalized content suggestions."
            action={{ label: "Go to Knowledge", href: "/app/knowledge" }}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-mc-1 hover:shadow-mc-2 transition-shadow duration-300">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          Today&apos;s Content Brief
        </CardTitle>
        <Link href="/app/briefs" className="text-sm text-primary hover:underline font-medium">
          View all briefs
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {brief.ideas.slice(0, 4).map((idea, idx) => (
            <Link
              key={idx}
              href={idea.id ? `/app/content/new?idea=${idea.id}` : "#"}
              className="group flex items-start gap-3 rounded-[20px] border p-4 hover:bg-accent/50 hover:border-primary/20 transition-all duration-200"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">{idea.title}</p>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {idea.description}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant="outline" className="text-xs bg-background">
                  {idea.platform || "LinkedIn"}
                </Badge>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all duration-200" />
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function RecentContent() {
  const { data: historyData, isLoading } = useContentHistory({ page: 1, page_size: 5 });

  if (isLoading) return <RecentContentSkeleton />;

  const records = historyData?.records ?? [];

  if (!records.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Content</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Sparkles}
            title="No content yet"
            description="Generate your first piece of content to get started."
            action={{ label: "New Content", href: "/app/content" }}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-mc-1 hover:shadow-mc-2 transition-shadow duration-300">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">Recent Content</CardTitle>
        <Link href="/app/history" className="text-sm text-primary hover:underline font-medium">
          View all
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {records.map((record) => (
            <div
              key={record.id}
              className="group flex items-center justify-between rounded-[20px] border p-4 hover:bg-accent/50 hover:border-primary/20 transition-all duration-200"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">{record.title}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {record.platform} &middot;{" "}
                  {new Date(record.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                  })}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <QualityBadge score={record.quality_score} />
                <Badge variant="outline" className="text-xs capitalize bg-background">
                  {record.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function TrendPanel() {
  const { data: trendsData, isLoading } = useTrendingTopics({ limit: 4 });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const topics = trendsData?.topics ?? [];

  if (!topics.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Trending Topics</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Sparkles}
            title="No trends yet"
            description="Trending topics will appear here once data sources are connected."
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-mc-1 hover:shadow-mc-2 transition-shadow duration-300">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-lg">Trending Topics</CardTitle>
        <Link href="/app/trends" className="text-sm text-primary hover:underline font-medium">
          View all
        </Link>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {topics.map((topic) => (
            <Link
              key={topic.id}
              href={`/app/content?topic=${encodeURIComponent(topic.name)}`}
              className="group flex items-center justify-between rounded-[20px] border p-4 hover:bg-accent/50 hover:border-primary/20 transition-all duration-200"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">{topic.name}</p>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {topic.description}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <Badge variant="secondary" className="text-xs bg-background">
                  {topic.category}
                </Badge>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {topic.signal_count ?? 0} signals
                </span>
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-fade-in">
      <PageHeader
        title="Dashboard"
        description="Your content at a glance"
        actions={
          <Link href="/app/content">
            <Button className="rounded-[20px] shadow-mc-1 hover:shadow-mc-2 transition-shadow duration-300">
              <Sparkles className="mr-2 h-4 w-4" />
              New Content
            </Button>
          </Link>
        }
      />

      <Suspense fallback={<MetricCardsGridSkeleton />}>
        <DashboardMetrics />
      </Suspense>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Suspense fallback={<RecentContentSkeleton />}>
            <BriefCard />
          </Suspense>
          <Suspense fallback={<RecentContentSkeleton />}>
            <RecentContent />
          </Suspense>
        </div>
        <div className="space-y-6">
          <Suspense fallback={<RecentContentSkeleton />}>
            <TrendPanel />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
