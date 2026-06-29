"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const features = [
  {
    outcome: "Never wonder what to write",
    feature: "Research Today's AI",
  },
  {
    outcome: "Write from your real experience",
    feature: "Knowledge Engine",
  },
  {
    outcome: "Generate authentic technical posts",
    feature: "Writing Assistant",
  },
  {
    outcome: "Improve clarity and originality",
    feature: "Review AI",
  },
];

export function FeatureGrid() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-16"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Features That Deliver Outcomes
        </h2>
      </motion.div>

      <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
        {features.map((item, index) => (
          <motion.div
            key={item.feature}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="p-6 rounded-xl border border-border/50 bg-muted/30 hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 p-2 rounded-lg bg-primary/10">
                <ArrowRight className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">{item.outcome}</h3>
                <p className="text-sm text-muted-foreground">{item.feature}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
