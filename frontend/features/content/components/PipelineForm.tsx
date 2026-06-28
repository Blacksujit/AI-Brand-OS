"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useGenerateContent } from "@/lib/api/hooks";
import { useAppStore } from "@/lib/stores/app-store";
import { Button } from "@/features/ui/Button";
import { Input } from "@/features/ui/Input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/features/ui/Select";
import { Card, CardContent, CardHeader, CardTitle } from "@/features/ui/Card";
import { Badge } from "@/features/ui/Badge";
import { Sparkles, Loader2, PenSquare, Type, Maximize } from "lucide-react";

const PLATFORMS = ["linkedin", "twitter", "medium", "newsletter"] as const;
const TONES = [
  "professional",
  "conversational",
  "thought-leadership",
  "educational",
] as const;

export function PipelineForm() {
  const searchParams = useSearchParams();
  const initialTopic = searchParams.get("topic") || "";

  const [topic, setTopic] = useState(initialTopic);
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
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Generate Content
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="topic" className="text-sm font-medium">
              Topic
            </label>
            <div className="relative">
              <PenSquare className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="topic"
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter a topic or leave blank for AI-picked"
                className="pl-10"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Leave empty to let AI pick from trending topics
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label htmlFor="platform" className="text-sm font-medium">
                Platform
              </label>
              <Select value={platform} onValueChange={setPlatform}>
                <SelectTrigger id="platform">
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  {PLATFORMS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label htmlFor="tone" className="text-sm font-medium">
                Tone
              </label>
              <Select value={tone} onValueChange={setTone}>
                <SelectTrigger id="tone">
                  <SelectValue placeholder="Select tone" />
                </SelectTrigger>
                <SelectContent>
                  {TONES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t
                        .split("-")
                        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                        .join(" ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label htmlFor="maxLength" className="text-sm font-medium">
                Max Length
              </label>
              <div className="relative">
                <Type className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="maxLength"
                  type="number"
                  min={50}
                  max={3000}
                  value={maxLength}
                  onChange={(e) => setMaxLength(Number(e.target.value))}
                  className="pl-10"
                />
              </div>
              <p className="text-xs text-muted-foreground">Characters (50-3000)</p>
            </div>
          </div>

          <Button type="submit" disabled={mutation.isPending} className="w-full" size="lg">
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting Pipeline...
              </>
            ) : (
              <>
                <Maximize className="mr-2 h-4 w-4" />
                Generate Content
              </>
            )}
          </Button>

          {mutation.isError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {mutation.error?.message || "Generation failed"}
            </div>
          )}

          {mutation.data && (
            <div className="rounded-md border border-primary/20 bg-primary/5 p-3 text-sm">
              <p className="font-medium flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Pipeline started
              </p>
              <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                <div>
                  <span className="font-medium">ID:</span> {mutation.data.pipeline_id.slice(0, 8)}...
                </div>
                <div>
                  <span className="font-medium">Status:</span>{" "}
                  <Badge variant={mutation.data.is_complete ? "success" : "info"}>
                    {mutation.data.is_complete ? "Complete" : "Running"}
                  </Badge>
                </div>
                <div>
                  <span className="font-medium">Steps:</span>{" "}
                  {mutation.data.steps_completed.length}/{9}
                </div>
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}