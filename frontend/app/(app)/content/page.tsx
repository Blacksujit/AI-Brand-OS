"use client";

import { PipelineForm } from "@/features/content/components/PipelineForm";
import { IdeaList } from "@/features/content/components/IdeaList";
import { EvaluateForm } from "@/features/content/components/EvaluateForm";
import { ContentTabs } from "@/features/content/components/ContentTabs";

export default function ContentPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Content</h1>
        <p className="text-muted-foreground">
          Generate and manage AI-powered content for your brand.
        </p>
      </div>
      <ContentTabs
        children={{
          generate: <PipelineForm />,
          ideas: <IdeaList />,
          evaluate: <EvaluateForm />,
        }}
      />
    </div>
  );
}