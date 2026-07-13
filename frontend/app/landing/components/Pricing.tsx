"use client";

import { motion } from "framer-motion";
import { Check, X } from "lucide-react";
import { Button } from "@/features/ui/Button";
import { useEntrance, type Direction } from "@/lib/animations";

const plans = [
  {
    name: "Personal",
    price: "$0",
    period: "/ month",
    description: "For individuals getting started with their technical brand.",
    features: [
      { text: "1 Knowledge Source (GitHub)", included: true },
      { text: "2 Drafts / Week", included: true },
      { text: "Custom Quality Scores", included: false },
    ],
    cta: "Start Free",
    popular: false,
  },
  {
    name: "Professional",
    price: "$49",
    period: "/ month",
    description: "For senior engineers and tech leaders building authority.",
    features: [
      { text: "Unlimited Knowledge Sources", included: true },
      { text: "Daily Draft Generation", included: true },
      { text: "Priority AI Review", included: true },
      { text: "Multi-platform Publishing", included: true },
    ],
    cta: "Go Pro",
    popular: true,
  },
  {
    name: "Teams",
    price: "$199",
    period: "/ month",
    description: "For DevRel teams and engineering departments.",
    features: [
      { text: "Shared Knowledge Graph", included: true },
      { text: "Collaborative Review", included: true },
      { text: "Brand Guidelines Lock", included: true },
    ],
    cta: "Contact Sales",
    popular: false,
  },
];

export function Pricing({ direction = "up" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section id="pricing" className="py-24 px-6 border-t border-border/20">
      <div className="max-w-[1200px] mx-auto">
        <motion.div
          {...sectionAnim}
          className="text-center mb-20"
        >
          <h2 className="text-4xl font-bold mb-4">Simple, transparent pricing.</h2>
          <p className="text-muted-foreground">Choose the plan that fits your career stage.</p>
        </motion.div>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className={`p-8 rounded-[40px] flex flex-col relative ${
                plan.popular
                  ? "border-2 border-foreground shadow-2xl bg-card/50 scale-105"
                  : "border border-border/20 bg-transparent"
              }`}
            >
              {plan.popular && (
                <div className="absolute top-0 right-8 -translate-y-1/2 bg-foreground text-background text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider">
                  Most Popular
                </div>
              )}
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-4">{plan.name}</p>
              <h3 className="text-4xl font-bold mb-2">
                {plan.price}
                <span className="text-sm text-muted-foreground font-normal">{plan.period}</span>
              </h3>
              <p className="text-sm text-muted-foreground mb-8">{plan.description}</p>
              <ul className="space-y-4 mb-8 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature.text} className={`flex items-center gap-3 text-sm ${feature.included ? "" : "text-muted-foreground/50"}`}>
                    {feature.included ? (
                      <Check className="h-4 w-4 text-green-400 shrink-0" />
                    ) : (
                      <X className="h-4 w-4 text-muted-foreground/50 shrink-0" />
                    )}
                    {feature.text}
                  </li>
                ))}
              </ul>
              <Button
                variant={plan.popular ? "default" : "outline"}
                className={`w-full rounded-[40px] font-bold ${plan.popular ? "bg-foreground text-background hover:bg-foreground/90" : ""}`}
                asChild
              >
                <a href="/login">{plan.cta}</a>
              </Button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}