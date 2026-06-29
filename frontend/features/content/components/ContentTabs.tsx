"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/features/ui/Tabs";
import { ReactNode } from "react";

interface ContentTabsProps {
  generateTab: ReactNode;
  ideasTab: ReactNode;
  evaluateTab: ReactNode;
}

export function ContentTabs({ generateTab, ideasTab, evaluateTab }: ContentTabsProps) {
  return (
    <Tabs defaultValue="generate" className="w-full">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="generate">Generate</TabsTrigger>
        <TabsTrigger value="ideas">Ideas</TabsTrigger>
        <TabsTrigger value="evaluate">Evaluate</TabsTrigger>
      </TabsList>
      <TabsContent value="generate">{generateTab}</TabsContent>
      <TabsContent value="ideas">{ideasTab}</TabsContent>
      <TabsContent value="evaluate">{evaluateTab}</TabsContent>
    </Tabs>
  );
}