"use client";

import { useState } from "react";
import { Button } from "@/features/ui/Button";
import { Input } from "@/features/ui/Input";
import { Badge } from "@/features/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { useGenerateIdeas } from "@/lib/api/hooks";
import { Idea } from "@/lib/validators/content";
import { Lightbulb, Loader2, Sparkles } from "lucide-react";

export function IdeaList() {
  const [topicHint, setTopicHint] = useState("");
  const [count, setCount] = useState(5);
  const mutation = useGenerateIdeas();

  const handleGenerate = () => {
    mutation.mutate({ topic: topicHint || undefined, count });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          Content Ideas
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-3">
          <Input
            value={topicHint}
            onChange={(e) => setTopicHint(e.target.value)}
            placeholder="Topic hint (optional)"
            className="flex-1"
          />
          <Input
            type="number"
            min={1}
            max={20}
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="w-20"
          />
          <Button onClick={handleGenerate} disabled={mutation.isPending}>
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate Ideas
              </>
            )}
          </Button>
        </div>

        {mutation.isError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {mutation.error?.message || "Failed to generate ideas"}
          </div>
        )}

        {mutation.data && (
          <div className="space-y-3">
            {mutation.data.map((idea: Idea) => (
              <div
                key={idea.id}
                className="rounded-md border p-3 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-medium">{idea.title}</h4>
                  <Badge variant="secondary" className="text-xs">
                    {Math.round(idea.relevance_score * 100)}%
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {idea.description}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}