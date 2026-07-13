"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useSpring, useMotionValue } from "framer-motion";
import { FileText, Clock, Users } from "lucide-react";
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

function GithubIcon({ className }: { className?: string }) {
  return <svg className={className} fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>;
}

const metrics = [
  { icon: GithubIcon, value: 12800, suffix: "+", label: "GitHub Stars" },
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
