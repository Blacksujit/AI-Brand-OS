"use client";

import { motion } from "framer-motion";

export function WorkspacePreview() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-12"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          A Premium Desktop Experience
        </h2>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-6xl mx-auto"
      >
        <div className="aspect-video rounded-xl border border-border/50 bg-muted/30 flex items-center justify-center">
          <p className="text-lg font-medium text-muted-foreground">Workspace Screenshot</p>
        </div>
      </motion.div>
    </section>
  );
}
