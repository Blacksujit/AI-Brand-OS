"use client";

import { BookOpen } from "lucide-react";
import { useKnowledgeContext } from "@/features/knowledge/hooks/useKnowledge";
import { Skeleton } from "@/features/ui/Skeleton";
import { Badge } from "@/features/ui/Badge";

export function KnowledgeContextPanel() {
  const { data, isLoading } = useKnowledgeContext(5);

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  const items = data?.items ?? [];

  if (items.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <BookOpen className="h-3 w-3" />
        Recent Knowledge
      </h4>
      <div className="space-y-1.5">
        {items.slice(0, 5).map((entry) => (
          <div
            key={entry.id}
            className="rounded-md border bg-card p-2 text-xs"
          >
            <p className="font-medium truncate">{entry.title}</p>
            {entry.summary && (
              <p className="mt-0.5 line-clamp-1 text-muted-foreground">
                {entry.summary}
              </p>
            )}
            {entry.tags.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {entry.tags.slice(0, 3).map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="text-[9px] px-1 py-0"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
