"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Layers, Database, Waves } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

const problems = [
  {
    icon: AlertTriangle,
    title: "Generic Tone",
    description: "Chatbots use overly polite, fluffy language that immediately signals &ldquo;AI-generated&rdquo; to technical peers.",
  },
  {
    icon: Layers,
    title: "Lack of Depth",
    description: "Surface-level summaries that miss the nuanced architectural trade-offs engineers care about.",
  },
  {
    icon: Database,
    title: "No Context",
    description: "Tools don&apos;t know your previous work, your tech stack, or your unique perspective on system design.",
  },
  {
    icon: Waves,
    title: "Inconsistent Voice",
    description: "One post sounds like a marketing intern, the next like an academic paper. Your brand becomes noise.",
  },
];

export function Problem({ direction = "left" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section className="py-24 px-6 max-w-[1200px] mx-auto">
      <motion.div {...sectionAnim} className="flex flex-col md:flex-row justify-between items-end mb-16 gap-8">
        <div className="max-w-xl">
          <span className="text-signal-orange font-mono text-[12px] uppercase tracking-[0.2em] mb-4 block">The Challenge</span>
          <h2 className="text-4xl md:text-5xl font-bold leading-tight">Why AI Writing Tools Fail Engineers.</h2>
        </div>
        <p className="text-muted-foreground max-w-sm mb-2">Most AI tools prioritize volume over depth. For technical professionals, that&apos;s a recipe for a shallow reputation.</p>
      </motion.div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {problems.map((problem, index) => (
          <motion.div
            key={problem.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -2 }}
            className="p-8 rounded-stadium border border-border/20 bg-card/30 transition-all duration-300 hover:border-border/50"
          >
            <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mb-6">
              <problem.icon className="h-6 w-6 text-signal-orange" />
            </div>
            <h3 className="text-xl font-bold mb-3">{problem.title}</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">{problem.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}