import { MetricCardsGridSkeleton } from "@/components/dashboard/MetricCardsGridSkeleton";

export default function AppLoading() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="space-y-1 mb-6">
        <div className="h-8 w-40 animate-pulse rounded-md bg-muted" />
        <div className="h-4 w-64 animate-pulse rounded-md bg-muted" />
      </div>
      <MetricCardsGridSkeleton />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-lg border p-6 space-y-3">
            <div className="h-5 w-32 animate-pulse rounded-md bg-muted" />
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        </div>
        <div className="space-y-6">
          <div className="rounded-lg border p-6 space-y-3">
            <div className="h-5 w-32 animate-pulse rounded-md bg-muted" />
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
