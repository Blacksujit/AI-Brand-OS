"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { Button } from "@/features/ui/Button";

export function CTA() {
  return (
    <section className="px-4 lg:px-8 py-20 lg:py-32 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center"
      >
        <div className="flex justify-center mb-6">
          <div className="p-3 rounded-full bg-primary/10">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
        </div>
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Start Building Your AI Brand Today
        </h2>
        <p className="text-xl text-muted-foreground mb-10">
          Turn your daily engineering work into authentic content that builds lasting authority.
        </p>
        <Button variant="default" size="lg" className="rounded-[20px] text-base px-8" asChild>
          <Link href="/login">
            Get Started Free
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </motion.div>
    </section>
  );
}
