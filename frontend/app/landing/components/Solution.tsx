"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Compass, BookOpen, Lightbulb, FileText, Sparkles, Rocket } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

const pillars = [
  {
    icon: Compass,
    title: "Research",
    outcome: "Discover what to write about",
    description: "Trend detection finds topics at the intersection of your expertise and what your audience cares about.",
    color: "orange",
  },
  {
    icon: BookOpen,
    title: "Knowledge",
    outcome: "Write from real expertise",
    description: "Your GitHub, notes, papers, and projects become a searchable knowledge base the AI consults before every draft.",
    color: "blue",
  },
  {
    icon: Lightbulb,
    title: "Strategy",
    outcome: "Know which angle works",
    description: "The AI scores each content angle against your voice, audience, and trending signals to pick the strongest hook.",
    color: "yellow",
  },
  {
    icon: FileText,
    title: "Draft",
    outcome: "Generate in your authentic voice",
    description: "LangGraph-powered agents write in a style that matches yours — learned from your existing writing, not generic training data.",
    color: "green",
  },
  {
    icon: Sparkles,
    title: "Review",
    outcome: "Ship with confidence",
    description: "AI quality scoring checks authenticity, clarity, originality, and style match before you publish.",
    color: "purple",
  },
  {
    icon: Rocket,
    title: "Publish",
    outcome: "Schedule across platforms",
    description: "One-click publish or schedule to LinkedIn, Twitter, and more — with platform-optimized formatting.",
    color: "teal",
  },
];

export function Solution({ direction = "right" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        {...sectionAnim}
        className="max-w-3xl mx-auto text-center mb-16"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-mc-heading mb-6">
          Knowledge-First AI. Human-Reviewed Content.
        </h2>
        <p className="text-lg text-muted-foreground">
          A complete pipeline from research to publish — built on your actual work, not generic training data.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {pillars.map((pillar, index) => {
          const colorMap: Record<string, string> = {
            orange: "bg-orange-500/10 text-orange-400 border-orange-500/20",
            blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
            yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
            green: "bg-green-500/10 text-green-400 border-green-500/20",
            purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
            teal: "bg-teal-500/10 text-teal-400 border-teal-500/20",
          };
          const glowMap: Record<string, string> = {
            orange: "shadow-[0_0_24px_rgba(249,115,22,0.06)]",
            blue: "shadow-[0_0_24px_rgba(59,130,246,0.06)]",
            yellow: "shadow-[0_0_24px_rgba(234,179,8,0.06)]",
            green: "shadow-[0_0_24px_rgba(34,197,94,0.06)]",
            purple: "shadow-[0_0_24px_rgba(168,85,247,0.06)]",
            teal: "shadow-[0_0_24px_rgba(20,184,166,0.06)]",
          };

          return (
            <motion.div
              key={pillar.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -4 }}
              className={cn(
                "group relative p-5 rounded-[20px] border border-border/50 bg-muted/20 transition-all duration-300",
                glowMap[pillar.color],
              )}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={cn("p-2.5 rounded-[14px] border", colorMap[pillar.color])}>
                  <pillar.icon className="h-4 w-4" />
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Step {index + 1}
                </span>
              </div>
              <h3 className="font-semibold text-base mb-1">{pillar.title}</h3>
              <p className="text-sm font-medium text-foreground/80 mb-2">{pillar.outcome}</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{pillar.description}</p>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}