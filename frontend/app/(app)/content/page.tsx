"use client";

import { useState, useCallback } from "react";
import { PipelineForm } from "@/features/content/components/PipelineForm";
import { PipelineProgress } from "@/features/content/components/PipelineProgress";
import { GeneratedContentView } from "@/features/content/components/GeneratedContentView";
import { IdeaList } from "@/features/content/components/IdeaList";
import { EvaluateForm } from "@/features/content/components/EvaluateForm";
import { ContentTabs } from "@/features/content/components/ContentTabs";
import { useGeneratedContent } from "@/features/content/hooks/useRegenerateContent";
import { Button } from "@/features/ui/Button";
import { ArrowLeft } from "lucide-react";

type Stage = "form" | "progress" | "result";

export default function ContentPage() {
  const [stage, setStage] = useState<Stage>("form");
  const [pipelineId, setPipelineId] = useState<string | null>(null);

  const { data: generatedPost, isLoading: outputLoading } = useGeneratedContent(
    stage === "result" ? pipelineId : null
  );

  const handlePipelineStart = useCallback((id: string) => {
    setPipelineId(id);
    setStage("progress");
  }, []);

  const handlePipelineComplete = useCallback(() => {
    setStage("result");
  }, []);

  const handleReset = useCallback(() => {
    setStage("form");
    setPipelineId(null);
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Content</h1>
        <p className="text-muted-foreground">
          Generate and manage AI-powered content for your brand.
        </p>
      </div>

      {stage === "form" ? (
        <ContentTabs
          children={{
            generate: <PipelineForm onPipelineStart={handlePipelineStart} />,
            ideas: <IdeaList />,
            evaluate: <EvaluateForm />,
          }}
        />
      ) : stage === "progress" && pipelineId ? (
        <div className="max-w-2xl mx-auto">
          <Button variant="ghost" onClick={handleReset} className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to form
          </Button>
          <PipelineProgress
            pipelineId={pipelineId}
            onComplete={handlePipelineComplete}
          />
        </div>
      ) : stage === "result" && pipelineId ? (
        <div className="max-w-3xl mx-auto">
          <Button variant="ghost" onClick={handleReset} className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Generate more
          </Button>
          {outputLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">Loading result...</p>
            </div>
          ) : generatedPost ? (
            <GeneratedContentView
              post={generatedPost}
              onRegenerate={handleReset}
            />
          ) : (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">No content found</p>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
