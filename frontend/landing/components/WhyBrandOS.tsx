"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";

const differentiators = [
  "Knowledge-first AI",
  "Human review required",
  "No hallucinated experience",
  "Transparent reasoning",
  "Modern AI architecture (LangGraph)",
];

export function WhyBrandOS() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-12"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Why BrandOS
        </h2>
      </motion.div>

      <div className="max-w-2xl mx-auto space-y-4">
        {differentiators.map((item, index) => (
          <motion.div
            key={item}
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="flex items-center gap-3 p-4 rounded-lg border border-border/50 bg-muted/30"
          >
            <Check className="h-5 w-5 text-primary flex-shrink-0" />
            <span className="font-medium">{item}</span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
