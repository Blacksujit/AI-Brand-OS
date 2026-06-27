"use client";

import { useState } from "react";
import { useGenerateIdeas } from "@/lib/api/hooks";
import { Button } from "@/components/ui/button";

export function IdeaList() {
  const [topicHint, setTopicHint] = useState("");
  const [count, setCount] = useState(5);
  const mutation = useGenerateIdeas();

  const handleGenerate = () => {
    mutation.mutate({ topic: topicHint || undefined, count });
  };

  return (
    <div className="space-y-4 rounded-lg border p-6">
      <h3 className="font-semibold">Content Ideas</h3>

      <div className="flex gap-3">
        <input
          type="text"
          value={topicHint}
          onChange={(e) => setTopicHint(e.target.value)}
          placeholder="Topic hint (optional)"
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <input
          type="number"
          min={1}
          max={20}
          value={count}
          onChange={(e) => setCount(Number(e.target.value))}
          className="w-20 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <Button onClick={handleGenerate} disabled={mutation.isPending}>
          {mutation.isPending ? "Generating..." : "Generate Ideas"}
        </Button>
      </div>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error?.message || "Failed to generate ideas"}
        </p>
      )}

      {mutation.data && (
        <div className="space-y-3">
          {mutation.data.map((idea) => (
            <div
              key={idea.id}
              className="rounded-md border p-3 transition-colors hover:bg-muted/50"
            >
              <div className="flex items-start justify-between gap-2">
                <h4 className="font-medium">{idea.title}</h4>
                <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                  {Math.round(idea.relevance_score * 100)}%
                </span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                {idea.description}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
