"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/features/ui/Tabs";

const tabs = [
  { id: "research", label: "Research" },
  { id: "knowledge", label: "Knowledge" },
  { id: "hooks", label: "Hooks" },
  { id: "draft", label: "Draft" },
  { id: "review", label: "Review" },
];

export function ProductPreview() {
  const [activeTab, setActiveTab] = useState("research");

  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-12"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          See BrandOS in Action
        </h2>
        <p className="text-xl text-muted-foreground">
          An interactive preview of the AI workspace
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-5xl mx-auto"
      >
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            {tabs.map((tab) => (
              <TabsTrigger key={tab.id} value={tab.id}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {tabs.map((tab) => (
            <TabsContent key={tab.id} value={tab.id}>
              <div className="aspect-video rounded-xl border border-border/50 bg-muted/30 flex items-center justify-center">
                <p className="text-lg font-medium text-muted-foreground">{tab.label} Panel</p>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </motion.div>
    </section>
  );
}
