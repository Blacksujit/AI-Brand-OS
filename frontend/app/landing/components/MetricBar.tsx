"use client";

import { motion } from "framer-motion";
import { Github, FileText, Timer, Shield } from "lucide-react";

const metrics = [
  { icon: Github, value: "12.4k", label: "GitHub Stars", color: "text-brand-orange" },
  { icon: FileText, value: "450k+", label: "Posts Generated", color: "text-brand-orange" },
  { icon: Timer, value: "82k", label: "Hours Saved", color: "text-brand-orange" },
  { icon: Shield, value: "100%", label: "Human Verified", color: "text-brand-orange" },
];

export function MetricBar() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <div className="max-w-3xl mx-auto text-center mb-16">
        <h3 className="text-2xl lg:text-3xl font-bold tracking-tight mb-4">
          Trusted by engineers at world-class teams
        </h3>
        <p className="text-lg text-muted-foreground">
          Join thousands of developers building their reputation with BrandOS
        </p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="flex flex-col items-center text-center px-4"
          >
            <div className="w-16 h-16 rounded-2xl bg-brand-orange/10 flex items-center justify-center mb-4 mx-auto">
              <metric.icon className="h-8 w-8 text-brand-orange" />
            </div>
            <span className="text-3xl lg:text-5xl font-bold text-foreground mb-2">{metric.value}</span>
            <span className="text-sm lg:text-base font-medium text-muted-foreground">{metric.label}</span>
          </motion.div>
        ))}
      </div>
      <div className="mt-16 max-w-2xl mx-auto">
        <div className="flex flex-wrap justify-center gap-8 opacity-50 grayscale">
          <span className="font-bold text-xl tracking-tighter">VERCEL</span>
          <span className="font-bold text-xl tracking-tighter">LINEAR</span>
          <span className="font-bold text-xl tracking-tighter">STRIPE</span>
          <span className="font-bold text-xl tracking-tighter">RAILWAY</span>
        </div>
      </div>
    </section>
  );
}