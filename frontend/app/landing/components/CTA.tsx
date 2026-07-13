"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/features/ui/Button";
import { Users, Clock, Shield, CheckCircle } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

const trustIndicators = [
  { icon: Users, text: "5,000+ developers" },
  { icon: Clock, text: "5 min setup" },
  { icon: Shield, text: "SOC2 certified" },
  { icon: CheckCircle, text: "No credit card" },
];

export function CTA({ direction = "up" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section className="relative py-32 px-6 max-w-[1200px] mx-auto overflow-hidden">
      <motion.div
        {...sectionAnim}
        className="max-w-[800px] mx-auto text-center relative z-10"
      >
        <h2 className="text-4xl lg:text-6xl font-bold tracking-tight mb-6">
          Your reputation doesn&apos;t build itself.
          <br />
          <span className="bg-gradient-to-r from-orange-500 to-orange-400 bg-clip-text text-transparent">
            Start today.
          </span>
        </h2>
        
        <p className="text-lg lg:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
          Join 5,000+ engineers who&apos;ve transformed their GitHub activity into technical authority.
          No ghostwriting. No generic AI. Just your authentic expertise amplified.
        </p>

        {/* Trust indicators */}
        <div className="flex flex-wrap justify-center gap-6 mb-10">
          {trustIndicators.map((item, index) => (
            <motion.div
              key={item.text}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.05 }}
              className="flex items-center gap-2 text-sm text-gray-400"
            >
              <item.icon className="h-4 w-4 text-orange-500" />
              <span className="font-medium text-white">{item.text}</span>
            </motion.div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-10">
          <Button variant="default" size="lg" className="rounded-lg text-base px-10 py-4 font-black bg-orange-500 hover:bg-orange-400 hover:shadow-[0_0_40px_-10px_#CF4500] transition-all" asChild>
            <Link href="/login">Get Started for Free</Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-lg text-base px-10 py-4 font-bold" asChild>
            <Link href="#product-preview">Watch the Demo</Link>
          </Button>
        </div>

        <p className="text-sm text-gray-400">
          No credit card required · Cancel anytime · 14-day free trial
        </p>

        {/* Featured user logos */}
        <div className="mt-16">
          <p className="text-xs font-medium tracking-wider text-gray-400 mb-6">TRUSTED BY ENGINEERS AT</p>
          <div className="flex flex-wrap justify-center gap-8 opacity-50 grayscale">
            <span className="font-bold text-xl tracking-tighter">VERCEL</span>
            <span className="font-bold text-xl tracking-tighter">LINEAR</span>
            <span className="font-bold text-xl tracking-tighter">STRIPE</span>
            <span className="font-bold text-xl tracking-tighter">RAILWAY</span>
          </div>
        </div>
      </motion.div>
    </section>
  );
}