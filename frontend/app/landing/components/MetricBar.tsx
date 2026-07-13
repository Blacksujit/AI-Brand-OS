"use client";

import { motion } from "framer-motion";
import { Star, FileText, Timer, Terminal } from "lucide-react";

const metrics = [
  { icon: Star, value: "12.4k", label: "GitHub Stars", color: "text-orange-500" },
  { icon: FileText, value: "450k+", label: "Posts Generated", color: "text-orange-500" },
  { icon: Timer, value: "82k", label: "Hours Saved", color: "text-orange-500" },
  { icon: Terminal, value: "100%", label: "Human Verified", color: "text-orange-500" },
];

export function MetricBar() {
  return (
    <section className="max-w-[1200px] mx-auto px-6 mb-24">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-8 rounded-[40px] border border-gray-800 bg-gray-950/50 backdrop-blur-sm">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="flex flex-col items-center text-center px-4 border-r border-gray-800/30 last:border-0"
          >
            <span className="flex h-2 w-2 rounded-full bg-orange-500 animate-pulse mb-2" />
            <span className="text-3xl md:text-4xl font-bold text-white">{metric.value}</span>
            <span className="text-[10px] font-mono uppercase text-gray-400 tracking-tighter">{metric.label}</span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}