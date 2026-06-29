"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";
import { Brain, ShieldCheck, SearchX, Eye, GitBranch } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

const colorMap = {
  orange: { icon: "bg-orange-500/10 text-orange-400 border-orange-500/20", accent: "bg-orange-500/5" },
  blue: { icon: "bg-blue-500/10 text-blue-400 border-blue-500/20", accent: "bg-blue-500/5" },
  green: { icon: "bg-green-500/10 text-green-400 border-green-500/20", accent: "bg-green-500/5" },
  purple: { icon: "bg-purple-500/10 text-purple-400 border-purple-500/20", accent: "bg-purple-500/5" },
  teal: { icon: "bg-teal-500/10 text-teal-400 border-teal-500/20", accent: "bg-teal-500/5" },
};

type ColorKey = keyof typeof colorMap;

interface Differentiator {
  icon: LucideIcon;
  title: string;
  description: string;
  color: ColorKey;
}

const differentiators: Differentiator[] = [
  {
    icon: Brain,
    title: "Knowledge-First AI",
    description: "Every draft is grounded in your actual knowledge base — GitHub repos, research papers, personal notes. No hallucinated experience.",
    color: "orange",
  },
  {
    icon: ShieldCheck,
    title: "Human Review Required",
    description: "BrandOS never auto-posts. You review, edit, and approve every piece before it goes live. Full editorial control, always.",
    color: "blue",
  },
  {
    icon: SearchX,
    title: "No Hallucinated Experience",
    description: "Unlike ChatGPT, BrandOS won&apos;t invent credentials. It only writes from what you&apos;ve actually done and stored in your knowledge base.",
    color: "green",
  },
  {
    icon: Eye,
    title: "Transparent Reasoning",
    description: "See exactly how the AI arrived at each angle, hook, and sentence. Every draft comes with a provenance trail back to your source material.",
    color: "purple",
  },
  {
    icon: GitBranch,
    title: "Modern AI Architecture",
    description: "Built on LangGraph multi-agent orchestration — not a single LLM call. Separate agents for research, drafting, review, and style analysis.",
    color: "teal",
  },
];

export function WhyBrandOS({ direction = "left" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        {...sectionAnim}
        className="max-w-3xl mx-auto text-center mb-16"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-mc-heading mb-6">
          Why BrandOS
        </h2>
        <p className="text-lg text-muted-foreground">
          We built this because every other AI writing tool failed the &ldquo;would I publish this under my name?&rdquo; test.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-5xl mx-auto">
        {differentiators.map((item, index) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -3 }}
            className={cn(
              "group p-5 rounded-[20px] border border-border/50 bg-muted/20 transition-all duration-300",
              index === 0 && "lg:col-span-2 lg:row-span-1",
            )}
          >
            <div className="flex items-start gap-4">
              <div className={cn("p-2.5 rounded-[14px] border shrink-0", colorMap[item.color].icon)}>
                <item.icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold text-base mb-1.5">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.description}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}