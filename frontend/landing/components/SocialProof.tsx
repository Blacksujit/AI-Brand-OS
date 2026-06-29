"use client";

import { motion } from "framer-motion";
import { Github, FileText, Clock, Users } from "lucide-react";

const metrics = [
  {
    icon: Github,
    value: "0",
    label: "GitHub Stars",
  },
  {
    icon: FileText,
    value: "0",
    label: "Posts Generated",
  },
  {
    icon: Clock,
    value: "0",
    label: "Hours Saved",
  },
  {
    icon: Users,
    value: "0",
    label: "Active Developers",
  },
];

export function SocialProof() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto border-t border-border/50">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="text-center"
          >
            <div className="flex justify-center mb-3">
              <div className="p-3 rounded-full bg-muted/50 border border-border/50">
                <metric.icon className="h-6 w-6 text-primary" />
              </div>
            </div>
            <div className="text-3xl lg:text-4xl font-bold tracking-tight mb-1">{metric.value}</div>
            <div className="text-sm text-muted-foreground">{metric.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
