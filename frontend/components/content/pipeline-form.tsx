"use client";

import { useState } from "react";
import { useGenerateContent } from "@/lib/api/hooks";
import { useAppStore } from "@/lib/stores";
import { Button } from "@/components/ui/button";

const PLATFORMS = ["linkedin", "twitter", "medium", "newsletter"] as const;
const TONES = [
  "professional",
  "conversational",
  "thought-leadership",
  "educational",
] as const;

export function PipelineForm() {
  const [topic, setTopic] = useState("");
  const [platform, setPlatform] = useState<string>("linkedin");
  const [tone, setTone] = useState<string>("professional");
  const [maxLength, setMaxLength] = useState(300);

  const mutation = useGenerateContent();
  const addPipelineHistory = useAppStore((s) => s.addPipelineHistory);
  const setActivePipeline = useAppStore((s) => s.setActivePipeline);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await mutation.mutateAsync({
      topic: topic || undefined,
      platform,
      tone,
      max_length: maxLength,
    });

    const record = {
      pipelineId: result.pipeline_id,
      topic: topic || "Untitled",
      status: result.is_complete ? ("complete" as const) : ("running" as const),
      startedAt: new Date().toISOString(),
    };
    addPipelineHistory(record);
    setActivePipeline(record);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border p-6">
      <div className="space-y-2">
        <label htmlFor="topic" className="text-sm font-medium">
          Topic
        </label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter a topic or leave blank for AI-picked"
          className="w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-2">
          <label htmlFor="platform" className="text-sm font-medium">
            Platform
          </label>
          <select
            id="platform"
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {PLATFORMS.map((p) => (
              <option key={p} value={p}>
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label htmlFor="tone" className="text-sm font-medium">
            Tone
          </label>
          <select
            id="tone"
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            {TONES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label htmlFor="maxLength" className="text-sm font-medium">
            Max Length
          </label>
          <input
            id="maxLength"
            type="number"
            min={50}
            max={3000}
            value={maxLength}
            onChange={(e) => setMaxLength(Number(e.target.value))}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      <Button type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Generating..." : "Generate Content"}
      </Button>

      {mutation.isError && (
        <p className="text-sm text-destructive">
          {mutation.error?.message || "Generation failed"}
        </p>
      )}

      {mutation.data && (
        <div className="rounded-md bg-muted p-3 text-sm">
          <p className="font-medium">Pipeline started</p>
          <p className="text-muted-foreground">
            ID: {mutation.data.pipeline_id}
          </p>
          <p className="text-muted-foreground">
            Status: {mutation.data.is_complete ? "Complete" : "Running"}
          </p>
          <p className="text-muted-foreground">
            Steps: {mutation.data.steps_completed.length}
          </p>
        </div>
      )}
    </form>
  );
}
