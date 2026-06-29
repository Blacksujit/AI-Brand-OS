"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const steps = [
  { title: "Research" },
  { title: "Knowledge" },
  { title: "Topic" },
  { title: "Draft" },
  { title: "Review" },
  { title: "Publish" },
];

export function Workflow() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-16"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          From Research to Publish
        </h2>
        <p className="text-xl text-muted-foreground">
          A seamless workflow that transforms your expertise into content
        </p>
      </motion.div>

      <div className="max-w-4xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-2"
            >
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
                <span className="text-sm font-semibold text-primary">{index + 1}</span>
              </div>
              <span className="font-medium">{step.title}</span>
              {index < steps.length - 1 && (
                <ArrowRight className="h-4 w-4 text-muted-foreground hidden md:block" />
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
