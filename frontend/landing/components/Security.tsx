"use client";

import { motion } from "framer-motion";
import { Shield, Lock, Database, Eye } from "lucide-react";

const securityFeatures = [
  {
    icon: Shield,
    title: "Privacy First",
    description: "Your data stays yours",
  },
  {
    icon: Lock,
    title: "Secure Architecture",
    description: "Enterprise-grade security",
  },
  {
    icon: Database,
    title: "Local Knowledge",
    description: "Your expertise, stored locally",
  },
  {
    icon: Eye,
    title: "Transparent",
    description: "See how AI uses your data",
  },
];

export function Security() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-12"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Built for Trust
        </h2>
        <p className="text-xl text-muted-foreground">
          Professional-grade security for professional users
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {securityFeatures.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="p-6 rounded-xl border border-border/50 bg-muted/30 text-center"
          >
            <div className="flex justify-center mb-4">
              <div className="p-3 rounded-full bg-primary/10">
                <feature.icon className="h-6 w-6 text-primary" />
              </div>
            </div>
            <h3 className="font-semibold mb-2">{feature.title}</h3>
            <p className="text-sm text-muted-foreground">{feature.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
