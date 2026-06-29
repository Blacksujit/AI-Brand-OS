"use client";

import Link from "next/link";
import { ArrowRight, Play } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/features/ui/Button";
import { useEntrance } from "@/lib/animations";

export function Hero() {
  const heroAnim = useEntrance("up");

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 pt-32 pb-20">
      <motion.div
        {...heroAnim}
        transition={{ duration: 0.5 }}
        className="max-w-[800px] mx-auto text-center relative z-10"
      >
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 mb-8"
        >
          <span className="flex h-2 w-2 rounded-full bg-orange-500 animate-pulse" />
          <span className="text-xs font-medium text-orange-500">v2.0 Beta Now Open</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-5xl md:text-7xl font-bold tracking-tight mb-6"
        >
          Turn today&apos;s work into tomorrow&apos;s reputation.
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
          className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12"
        >
          <Button variant="default" size="lg" className="rounded-lg text-base px-10 font-bold bg-orange-500 hover:bg-orange-400 transition-all" asChild>
            <Link href="/login">
              Start Building
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-lg text-base px-10 font-bold" asChild>
            <Link href="#product-preview">
              <Play className="mr-2 h-4 w-4" />
              Watch the demo
            </Link>
          </Button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-col items-center gap-4"
        >
          <p className="text-xs font-medium tracking-wider text-muted-foreground">TRUSTED BY 5,000+ ENGINEERS AT</p>
          <div className="flex flex-wrap justify-center gap-8 opacity-50 grayscale">
            <span className="font-bold text-xl tracking-tighter">VERCEL</span>
            <span className="font-bold text-xl tracking-tighter">LINEAR</span>
            <span className="font-bold text-xl tracking-tighter">STRIPE</span>
            <span className="font-bold text-xl tracking-tighter">RAILWAY</span>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}