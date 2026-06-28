"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/features/ui/Tabs";
import { ReactNode } from "react";

interface ContentTabsProps {
  children: {
    generate: ReactNode;
    ideas: ReactNode;
    evaluate: ReactNode;
  };
}

export function ContentTabs({ children }: ContentTabsProps) {
  return (
    <Tabs defaultValue="generate" className="w-full">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="generate">Generate</TabsTrigger>
        <TabsTrigger value="ideas">Ideas</TabsTrigger>
        <TabsTrigger value="evaluate">Evaluate</TabsTrigger>
      </TabsList>
      <TabsContent value="generate">{children.generate}</TabsContent>
      <TabsContent value="ideas">{children.ideas}</TabsContent>
      <TabsContent value="evaluate">{children.evaluate}</TabsContent>
    </Tabs>
  );
}