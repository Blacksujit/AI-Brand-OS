"use client";

import { motion } from "framer-motion";
import { CheckCircle } from "lucide-react";

const pillars = [
  { title: "Research", description: "Trend detection and topic discovery" },
  { title: "Knowledge", description: "Your expertise, stored and retrieved" },
  { title: "Reasoning", description: "Strategic thinking for every post" },
  { title: "Writing", description: "Authentic voice, technical depth" },
  { title: "Review", description: "Quality assurance and improvement" },
  { title: "Publish", description: "Multi-platform distribution" },
];

export function Solution() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-16"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Knowledge-First AI. Human-Reviewed Content.
        </h2>
        <p className="text-xl text-muted-foreground">
          A complete pipeline from research to publish, built on your actual expertise.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {pillars.map((pillar, index) => (
          <motion.div
            key={pillar.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="p-6 rounded-xl border border-border/50 bg-muted/30"
          >
            <div className="flex items-center gap-3 mb-3">
              <CheckCircle className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">{pillar.title}</h3>
            </div>
            <p className="text-sm text-muted-foreground">{pillar.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
