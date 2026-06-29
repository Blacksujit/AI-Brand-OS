"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useSpring, useMotionValue } from "framer-motion";
import { Github, FileText, Clock, Users } from "lucide-react";
import { cn } from "@/lib/utils";

function AnimatedCounter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  const motionValue = useMotionValue(0);
  const spring = useSpring(motionValue, { damping: 30, stiffness: 80 });
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry?.isIntersecting) { setInView(true); observer.disconnect(); } },
      { threshold: 0.3 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (inView) motionValue.set(to);
  }, [inView, to, motionValue]);

  useEffect(() => {
    const unsubscribe = spring.on("change", (v) => setDisplay(Math.round(v).toLocaleString()));
    return unsubscribe;
  }, [spring]);

  return <div ref={ref} className="text-3xl lg:text-4xl font-bold tracking-mc-heading mb-1 tabular-nums">{display}{suffix}</div>;
}

const metrics = [
  { icon: Github, value: 12800, suffix: "+", label: "GitHub Stars" },
  { icon: FileText, value: 5000, suffix: "+", label: "Posts Generated" },
  { icon: Clock, value: 1200, suffix: "+", label: "Hours Saved" },
  { icon: Users, value: 850, suffix: "+", label: "Active Developers" },
];

export function SocialProof() {
  return (
    <section className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto border-t border-border/50">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="text-center"
          >
            <div className="flex justify-center mb-3">
              <div className={cn(
                "p-3 rounded-[20px] border",
                index === 0 ? "bg-orange-500/10 border-orange-500/20" :
                index === 1 ? "bg-blue-500/10 border-blue-500/20" :
                index === 2 ? "bg-green-500/10 border-green-500/20" :
                "bg-purple-500/10 border-purple-500/20",
              )}>
                <metric.icon className={cn(
                  "h-6 w-6",
                  index === 0 ? "text-orange-400" :
                  index === 1 ? "text-blue-400" :
                  index === 2 ? "text-green-400" :
                  "text-purple-400",
                )} />
              </div>
            </div>
            <AnimatedCounter to={metric.value} suffix={metric.suffix} />
            <div className="text-sm text-muted-foreground">{metric.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
