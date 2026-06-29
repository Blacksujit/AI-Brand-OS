"use client";

import { motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";

export function Problem() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center"
      >
        <div className="flex justify-center mb-6">
          <div className="p-3 rounded-full bg-destructive/10 border border-destructive/20">
            <AlertTriangle className="h-6 w-6 text-destructive" />
          </div>
        </div>
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Why AI Writing Tools Fail Technical Professionals
        </h2>
        <p className="text-xl text-muted-foreground mb-12">
          Generic content. No personal knowledge. No technical authenticity. No consistency.
        </p>
      </motion.div>
    </section>
  );
}
