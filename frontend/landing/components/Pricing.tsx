"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { Button } from "@/features/ui/Button";

const plans = [
  {
    name: "Free",
    price: "$0",
    description: "For individuals getting started",
    features: ["Basic research", "5 posts/month", "Knowledge base (100 items)", "Community support"],
  },
  {
    name: "Pro",
    price: "$29",
    description: "For serious content creators",
    features: ["Advanced research", "Unlimited posts", "Unlimited knowledge", "Priority support", "API access"],
    popular: true,
  },
  {
    name: "Team",
    price: "$99",
    description: "For teams and organizations",
    features: ["Everything in Pro", "Team collaboration", "Admin dashboard", "SSO", "Custom integrations"],
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "For large organizations",
    features: ["Everything in Team", "Dedicated support", "SLA", "Custom deployment", "Training"],
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="max-w-3xl mx-auto text-center mb-16"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-tight mb-6">
          Simple, Transparent Pricing
        </h2>
        <p className="text-xl text-muted-foreground">
          Start free, scale as you grow
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan, index) => (
          <motion.div
            key={plan.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className={`p-6 rounded-xl border ${
              plan.popular ? "border-primary/50 bg-primary/5" : "border-border/50 bg-muted/30"
            }`}
          >
            {plan.popular && (
              <div className="text-xs font-medium text-primary mb-4">Most Popular</div>
            )}
            <h3 className="font-semibold text-lg mb-2">{plan.name}</h3>
            <div className="text-3xl font-bold mb-2">{plan.price}</div>
            <p className="text-sm text-muted-foreground mb-6">{plan.description}</p>
            <ul className="space-y-3 mb-6">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm">
                  <Check className="h-4 w-4 text-primary flex-shrink-0 mt-0.5" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <Button variant={plan.popular ? "default" : "outline"} className="w-full rounded-[20px]" asChild>
              <a href="/login">Get Started</a>
            </Button>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
