"use client";

import Link from "next/link";
import { ArrowRight, Play } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/features/ui/Button";
import { useEntrance } from "@/lib/animations";

export function Hero() {
  const heroAnim = useEntrance("up");

  return (
    <section className="relative min-h-dvh flex flex-col items-center justify-center text-center pt-32 pb-20 lg:pt-56 lg:pb-28 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle,#333_1px,transparent_1px)] opacity-10 pointer-events-none" style={{ backgroundSize: "24px 24px" }} />
      <motion.div
        {...heroAnim}
        transition={{ duration: 0.5 }}
        className="max-w-[800px] mx-auto text-center relative z-10"
      >
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-orange-500/20 bg-orange-500/5 mb-8"
        >
          <span className="flex size-2 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-[10px] font-mono uppercase tracking-widest text-orange-500">v2.0 Beta Now Open</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-[1.05]"
        >
          <span className="bg-gradient-to-b from-foreground to-muted-foreground bg-clip-text text-transparent">
            Turn Today&apos;s Work into
          </span>
          <br />
          <span className="text-muted-foreground/60">
            Tomorrow&apos;s Reputation.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-lg md:text-xl text-muted-foreground mb-10 max-w-[640px] mx-auto leading-relaxed"
        >
          The AI Personal Brand Operating System for technical professionals. Not a ghostwriter&mdash;a knowledge engine built to amplify your authentic expertise.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button variant="default" size="lg" className="group rounded-[20px] text-base px-10 py-5 font-bold shadow-[0_0_40px_-10px_#CF4500]" asChild>
            <Link href="/login">
              Start Building
              <ArrowRight className="ml-2 h-4 w-4 transition-transform duration-150 group-hover:translate-x-1" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-[20px] text-base px-10 py-5 font-bold" asChild>
            <Link href="#product-preview">
              <Play className="mr-2 h-4 w-4" />
              Watch Demo
            </Link>
          </Button>
        </motion.div>
      </motion.div>
    </section>
  );
}