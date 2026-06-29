"use client";

import Link from "next/link";
import { ArrowRight, Sparkles, Github } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/features/ui/Button";

export function Hero() {
  return (
    <section className="relative px-4 lg:px-8 pt-32 pb-20 lg:pt-48 lg:pb-32 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center max-w-4xl mx-auto"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-muted/50 border border-border/50 mb-8"
        >
          <Sparkles className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">AI Personal Brand Operating System</span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-5xl lg:text-7xl font-bold tracking-tight mb-6"
        >
          Turn Today&apos;s Work Into
          <br />
          <span className="text-primary">Tomorrow&apos;s Reputation</span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto"
        >
          The AI-powered platform that transforms your daily engineering work into authentic, high-quality content that builds lasting authority.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12"
        >
          <Button variant="default" size="lg" className="rounded-[20px] text-base px-8" asChild>
            <Link href="/login">
              Start Building Your AI Brand
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-[20px] text-base px-8" asChild>
            <Link href="#how-it-works">See How It Works</Link>
          </Button>
        </motion.div>

        {/* Trust Indicators */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="flex flex-wrap gap-6 justify-center items-center text-sm text-muted-foreground"
        >
          <div className="flex items-center gap-2">
            <Github className="h-4 w-4" />
            <span>Open Source</span>
          </div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            <span>LangGraph Powered</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span>Privacy First</span>
          </div>
        </motion.div>
      </motion.div>

      {/* Product Preview Placeholder */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="mt-20 relative"
      >
        <div className="relative rounded-2xl border border-border/50 bg-muted/30 p-2 shadow-2xl">
          <div className="aspect-video rounded-xl bg-gradient-to-br from-background via-muted/20 to-background flex items-center justify-center">
            <div className="text-center">
              <Sparkles className="h-16 w-16 mx-auto mb-4 text-primary/50" />
              <p className="text-lg font-medium text-muted-foreground">Product Preview</p>
              <p className="text-sm text-muted-foreground/60 mt-2">Interactive workspace coming soon</p>
            </div>
          </div>
        </div>
        {/* Glow effect */}
        <div className="absolute inset-0 bg-primary/5 blur-3xl -z-10 rounded-full" />
      </motion.div>
    </section>
  );
}
