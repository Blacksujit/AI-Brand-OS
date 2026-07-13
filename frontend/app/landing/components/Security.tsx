"use client";

import { motion } from "framer-motion";
import { Shield } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

export function Security({ direction = "right" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section id="security" className="py-32 px-6">
      <div className="max-w-[1000px] mx-auto rounded-stadium border border-border/20 bg-card/30 backdrop-blur-sm p-12 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <Shield className="h-40 w-40 text-foreground" />
        </div>
        <motion.div {...sectionAnim} className="relative z-10">
          <h2 className="text-4xl font-bold mb-6">Privacy by Design.</h2>
          <p className="text-lg text-muted-foreground mb-10 max-w-[600px]">
            Your knowledge base is yours. We use secure architecture to ensure your proprietary code and private documentation never leave your control.
          </p>
          <div className="grid sm:grid-cols-3 gap-8">
            {[
              { title: "Local Knowledge", description: "Vector embeddings are processed securely and never used for global model training." },
              { title: "Data Ownership", description: "Export your entire knowledge graph at any time in open formats." },
              { title: "Enterprise Ready", description: "SOC2 compliant infrastructure with SSO and role-based access." },
            ].map((item) => (
              <div key={item.title}>
                <h4 className="font-bold text-foreground mb-2">{item.title}</h4>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}