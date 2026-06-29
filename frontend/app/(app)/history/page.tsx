"use client";

import { useState } from "react";
import Link from "next/link";
import { useContentHistory, useUpdateRecordStatus } from "@/lib/api/hooks";
import { QualityBadge } from "@/features/ui/QualityBadge";
import { Button } from "@/features/ui/Button";

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "draft", label: "Drafts" },
  { value: "published", label: "Published" },
  { value: "archived", label: "Archived" },
] as const;

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const { data, isLoading, isError, error } = useContentHistory({
    page,
    page_size: 20,
    status: statusFilter || undefined,
  });
  const updateStatus = useUpdateRecordStatus();

  const handleStatusChange = (
    recordId: string,
    status: "draft" | "published" | "archived",
  ) => {
    updateStatus.mutate({ recordId, status });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">History</h1>
          <p className="text-muted-foreground">
            All your generated content in one place.
          </p>
        </div>
        <div className="flex gap-2">
          {STATUS_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              variant={statusFilter === opt.value ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setStatusFilter(opt.value);
                setPage(1);
              }}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      )}

      {isError && (
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {error?.message || "Failed to load history"}
        </div>
      )}

      {data && data.records.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <p className="text-muted-foreground">No content yet</p>
            <p className="text-sm text-muted-foreground">
              Generate your first piece of content to see it here.
            </p>
          </div>
        </div>
      )}

      {data && data.records.length > 0 && (
        <div className="space-y-3">
          {data.records.map((record) => (
            <div
              key={record.id}
              className="rounded-lg border transition-colors hover:bg-muted/30"
            >
              <Link href={`/app/history/${record.id}`} className="block p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h3 className="font-medium truncate">{record.title}</h3>
                    <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                      {record.body}
                    </p>
                    <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <span className="capitalize">{record.platform}</span>
                      <span>{new Date(record.created_at).toLocaleDateString()}</span>
                      {record.hook && <span>Has hook</span>}
                      {record.call_to_action && <span>Has CTA</span>}
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <QualityBadge score={record.quality_score} />
                  </div>
                </div>
              </Link>
              <div className="border-t px-4 pb-3 pt-3 flex items-center gap-2">
                {record.status === "draft" && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleStatusChange(record.id, "published")}
                    >
                      Publish
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleStatusChange(record.id, "archived")}
                    >
                      Archive
                    </Button>
                  </>
                )}
                {record.status === "published" && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleStatusChange(record.id, "archived")}
                  >
                    Archive
                  </Button>
                )}
                {record.status === "archived" && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleStatusChange(record.id, "draft")}
                  >
                    Restore
                  </Button>
                )}
                <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs capitalize text-muted-foreground">
                  {record.status}
                </span>
              </div>
            </div>
          ))}

          {data && data.total > data.page * data.page_size && (
            <div className="flex justify-center pt-4">
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
              >
                Load More
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
