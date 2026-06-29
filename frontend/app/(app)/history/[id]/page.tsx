"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useContentRecord } from "@/lib/api/hooks";
import { GeneratedContentView } from "@/features/content/components/GeneratedContentView";
import { Button } from "@/features/ui/Button";
import { Skeleton } from "@/features/ui/Skeleton";

export default function HistoryRecordPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: post, isLoading, isError, error } = useContentRecord(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !post) {
    return (
      <div className="space-y-6">
        <Link href="/app/history">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to History
          </Button>
        </Link>
        <div className="rounded-md bg-destructive/10 p-4 text-sm text-destructive">
          {error?.message || "Failed to load content record"}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link href="/app/history">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to History
        </Button>
      </Link>
      <GeneratedContentView post={post} onRegenerate={() => {}} />
    </div>
  );
}
