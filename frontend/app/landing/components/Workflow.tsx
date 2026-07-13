"use client";

import { motion } from "framer-motion";
import { useEntrance, type Direction } from "@/lib/animations";

const steps = [
  {
    number: 1,
    title: "Research",
    description: "We scan your connected repositories, documentation, and chat history for unique insights.",
    panel: (
      <div className="bg-card/40 backdrop-blur-sm p-4 rounded border border-border/20 text-[10px] font-mono text-muted-foreground">
        [SYSTEM] Scanning PR #421: &ldquo;Implement Redis Cache&rdquo;... <br/>
        [SYSTEM] Found unique solution for race conditions...
      </div>
    ),
  },
  {
    number: 2,
    title: "Knowledge Engine",
    description: "The AI maps your technical decisions into a structured knowledge graph that evolves over time.",
    panel: (
      <div className="h-24 w-full rounded border border-border/20 bg-gradient-to-br from-signal-orange/5 via-card/20 to-card/10 flex items-center justify-center">
        <span className="text-[10px] text-muted-foreground font-mono">knowledge graph</span>
      </div>
    ),
  },
  {
    number: 3,
    title: "Topic Selection",
    description: "We suggest high-impact topics based on what&rsquo;s trending in tech and what you&rsquo;ve actually been working on.",
    panel: (
      <div className="flex gap-2">
        {["Edge Computing", "Rust/WASM", "DX Strategy"].map((tag) => (
          <span key={tag} className="bg-card border border-border/20 px-3 py-1 rounded text-xs text-muted-foreground">{tag}</span>
        ))}
      </div>
    ),
  },
];

export function Workflow({ direction = "left" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section id="workflow" className="py-32 px-6">
      <div className="max-w-[1200px] mx-auto">
        <motion.div
          {...sectionAnim}
          className="text-center mb-20"
        >
          <h2 className="text-4xl font-bold mb-4">Engineered for Authenticity</h2>
          <p className="text-muted-foreground max-w-[600px] mx-auto">From raw data to industry authority in six automated steps.</p>
        </motion.div>
        <div className="relative max-w-4xl mx-auto">
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border/20 -translate-x-1/2 hidden md:block" />
          <div className="space-y-24">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className={`relative flex flex-col md:flex-row items-center gap-8 md:gap-0 ${index % 2 === 1 ? "md:flex-row-reverse" : ""}`}
              >
                <div className={`md:w-1/2 ${index % 2 === 0 ? "md:pr-20 md:text-right" : "md:pl-20 md:text-left"}`}>
                  <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                   <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
                <div className="absolute left-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-background border border-border/20 text-foreground flex items-center justify-center font-bold z-10 hidden md:flex">
                  {step.number}
                </div>
                <div className={`md:w-1/2 ${index % 2 === 0 ? "md:pl-20" : "md:pr-20 md:text-right"}`}>
                  {step.panel}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}