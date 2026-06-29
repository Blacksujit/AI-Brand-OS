"use client";

import { motion } from "framer-motion";
import { X, Verified } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

export function Problem({ direction = "left" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section className="py-24 px-6 border-y border-border/50">
      <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-20 items-center">
        <motion.div {...sectionAnim}>
          <h2 className="text-4xl font-bold mb-6">Generic AI fails technical professionals.</h2>
          <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
            Most LinkedIn &ldquo;AI tools&rdquo; feel fake because they are just LLMs guessing based on generic trends. They don&apos;t know you, your code, or your unique perspective.
          </p>
          <div className="space-y-6">
            <div className="flex items-start gap-4">
              <div className="p-2 rounded bg-red-500/10 text-red-400">
                <X className="h-4 w-4" />
              </div>
              <div>
                <h4 className="font-bold">The &ldquo;Ghostwriter&rdquo; Problem</h4>
                <p className="text-sm text-muted-foreground">Polished but empty posts that everyone scrolls past.</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <div className="p-2 rounded bg-red-500/10 text-red-400">
                <X className="h-4 w-4" />
              </div>
              <div>
                <h4 className="font-bold">Missing Context</h4>
                <p className="text-sm text-muted-foreground">Generic AI doesn&apos;t know about that 3 AM bug fix that changed your perspective.</p>
              </div>
            </div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, x: 40 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative aspect-square rounded-2xl overflow-hidden border border-border/50 bg-muted/20 backdrop-blur-sm p-1"
        >
          <div className="w-full h-full rounded-xl bg-gradient-to-br from-orange-500/10 via-muted/30 to-muted/20 flex items-center justify-center">
            <div className="bg-background/80 backdrop-blur-md border border-border/50 p-6 rounded-lg text-center max-w-xs shadow-2xl">
              <Verified className="h-10 w-10 text-secondary mx-auto mb-4" />
              <p className="text-sm font-medium">BrandOS connects to your real work to build authentic authority.</p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
