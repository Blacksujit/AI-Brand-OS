"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react";
import { Button } from "@/features/ui/Button";
import { cn } from "@/lib/utils";

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav className={cn(
      "fixed top-8 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-32px)] max-w-[800px]",
      scrolled && "shadow-2xl"
    )}>
      <div className="glass-pill px-6 py-3 rounded-full flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-foreground font-bold tracking-tight text-xl">BrandOS</span>
          </Link>
        </div>
        <nav className="hidden md:flex items-center gap-8">
          <a href="#workflow" className="text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Workflow</a>
          <a href="#features" className="text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Platform</a>
          <a href="#pricing" className="text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Pricing</a>
        </nav>
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="hidden sm:inline-flex rounded-lg text-xs font-mono uppercase px-5 py-2" asChild>
            <Link href="/login">Sign In</Link>
          </Button>
          <Button variant="default" className="rounded-lg text-xs font-mono uppercase px-5 py-2 bg-signal-orange hover:bg-signal-orange/90 text-background" asChild>
            <Link href="/login">Get Started</Link>
          </Button>
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-muted/20 transition-colors"
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>
      {isOpen && (
        <div className="md:hidden mt-2 glass-pill rounded-xl px-6 py-4 space-y-3">
          <a href="#workflow" className="block text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground py-2" onClick={() => setIsOpen(false)}>Workflow</a>
          <a href="#features" className="block text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground py-2" onClick={() => setIsOpen(false)}>Platform</a>
          <a href="#pricing" className="block text-xs font-mono uppercase tracking-widest text-muted-foreground hover:text-foreground py-2" onClick={() => setIsOpen(false)}>Pricing</a>
          <div className="pt-2 space-y-2">
            <Button variant="ghost" className="w-full rounded-lg text-xs font-mono uppercase" asChild>
              <Link href="/login" onClick={() => setIsOpen(false)}>Sign In</Link>
            </Button>
            <Button variant="default" className="w-full rounded-lg text-xs font-mono uppercase" asChild>
              <Link href="/login" onClick={() => setIsOpen(false)}>Get Started</Link>
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
}