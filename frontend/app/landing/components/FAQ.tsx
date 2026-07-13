"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

const faqs = [
  {
    question: "Who is BrandOS for?",
    answer: "BrandOS is designed for AI engineers, developers, researchers, founders, and technical creators who want to build a professional brand on LinkedIn and other platforms.",
  },
  {
    question: "How is it different from ChatGPT?",
    answer: "Unlike generic AI tools, BrandOS learns from your actual work—GitHub commits, research papers, notes, and projects—to generate authentic content that reflects your unique expertise and voice.",
  },
  {
    question: "How does the AI learn my voice?",
    answer: "BrandOS analyzes your existing writing samples across 12+ dimensions including vocabulary, sentence structure, and tone. It continuously improves as you rate and edit generated content.",
  },
  {
    question: "Do you auto-post to LinkedIn?",
    answer: "No. BrandOS generates content for your review. You maintain full control over what gets published and when.",
  },
  {
    question: "Can I use my own writing samples?",
    answer: "Yes. You can import your existing posts, articles, and notes to help the AI learn your voice and style faster.",
  },
  {
    question: "What data do you store?",
    answer: "We store your knowledge base, writing samples, and generated content in your personal workspace. Your data is encrypted and never used to train other models.",
  },
];

export function FAQ({ direction = "left" }: { direction?: Direction }) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const sectionAnim = useEntrance(direction);

  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        {...sectionAnim}
        className="max-w-3xl mx-auto text-center mb-12"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Frequently Asked Questions
        </h2>
      </motion.div>

      <div className="max-w-3xl mx-auto space-y-4">
        {faqs.map((faq, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.05 }}
            className="border border-border/50 rounded-xl bg-muted/30 overflow-hidden"
          >
            <button
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
              className="w-full px-6 py-4 flex items-center justify-between text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <span className="font-medium">{faq.question}</span>
              <ChevronDown
                className={`h-5 w-5 transition-transform ${
                  openIndex === index ? "rotate-180" : ""
                }`}
              />
            </button>
            <AnimatePresence initial={false}>
              {openIndex === index && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-4 text-sm text-muted-foreground">
                    {faq.answer}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
