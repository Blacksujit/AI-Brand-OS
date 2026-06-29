"use client";

import { motion } from "framer-motion";
import { Search, Sparkles, FileText } from "lucide-react";

const features = [
  {
    icon: Search,
    title: "Research Today's AI",
    description: "Stop staring at a blank screen. We surface the most relevant technical topics from your own work history daily.",
  },
  {
    icon: Sparkles,
    title: "Knowledge Engine",
    description: "Write from real experience. Our engine links your posts directly to code commits, ensuring technical accuracy every time.",
  },
  {
    icon: FileText,
    title: "Review AI",
    description: "An automated editorial layer that improves clarity and originality while stripping away the generic &ldquo;AI flavor.&rdquo;",
  },
];

export function FeatureGrid() {
  return (
    <section id="features" className="py-24 px-6 bg-muted/10">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -3 }}
                className="rounded-xl border border-border/50 bg-muted/20 backdrop-blur-sm p-8 transition-all duration-300"
              >
                <div className="size-12 rounded bg-primary/10 flex items-center justify-center mb-6">
                  <Icon className="h-6 w-6 text-foreground" />
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
