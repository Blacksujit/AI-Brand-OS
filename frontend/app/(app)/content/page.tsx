"use client";

import { PipelineForm } from "@/components/content/pipeline-form";
import { IdeaList } from "@/components/content/idea-list";

export default function ContentPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Content</h1>
        <p className="text-muted-foreground">
          Generate and manage AI-powered content for your brand.
        </p>
      </div>
      <PipelineForm />
      <IdeaList />
    </div>
  );
}
