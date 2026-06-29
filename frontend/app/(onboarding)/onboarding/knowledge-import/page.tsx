"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Terminal,
  FileText,
  Globe,
  BookOpen,
  Check,
  ArrowRight,
  Upload,
  Link,
  Database,
  Shield,
  Loader2,
  ChevronRight,
} from "lucide-react";

type ConnectionSource = "github" | "resume" | "portfolio" | "notes";

interface SourceConfig {
  id: ConnectionSource;
  icon: typeof Terminal;
  title: string;
  description: string;
  tag: string;
  actionLabel: string;
  actionIcon: typeof Upload;
}

const sources: SourceConfig[] = [
  { id: "github", icon: Terminal, title: "GitHub", description: "Sync repositories and contribution patterns to build your technical graph.", tag: "Git", actionLabel: "Connect Repo", actionIcon: ArrowRight },
  { id: "resume", icon: FileText, title: "Resume", description: "Extract career narrative, achievements, and formal education history.", tag: "PDF", actionLabel: "Upload PDF", actionIcon: Upload },
  { id: "portfolio", icon: Globe, title: "Portfolio", description: "Crawl your personal site to capture design language and project stories.", tag: "URL", actionLabel: "Input URL", actionIcon: Link },
  { id: "notes", icon: BookOpen, title: "Learning Notes", description: "Connect Notion or Obsidian to import your knowledge base and thought logs.", tag: "JSON", actionLabel: "Sync Notes", actionIcon: Database },
];

const terminalLogs = [
  { type: "info" as const, text: "Connecting to OAuth gateway..." },
  { type: "info" as const, text: "Authorization successful. Scoping repositories." },
  { type: "scan" as const, text: "Scanning /main branch: architecture.md found." },
  { type: "scan" as const, text: "Analyzing language distribution: TypeScript (82%), Rust (12%)." },
  { type: "topic" as const, text: "Identified Expertise: Distributed Systems" },
  { type: "topic" as const, text: "Identified Expertise: LLM Orchestration" },
  { type: "info" as const, text: "Parsing commit history... 1,240 commits indexed." },
  { type: "topic" as const, text: "Topic detected: API Design" },
  { type: "scan" as const, text: "Extracting tech stack metadata: Vite, TailwindCSS, Drizzle." },
  { type: "info" as const, text: "Cross-referencing documentation with project structure." },
  { type: "topic" as const, text: "Project Highlight: Vector Database Integration" },
  { type: "info" as const, text: "Finalizing knowledge graph nodes..." },
];

function StepperDot({ step, current, label }: { step: number; current: number; label: string }) {
  const completed = step < current;
  const active = step === current;
  return (
    <div className="flex flex-col items-center gap-3 bg-background px-4 relative z-10">
      <div className={cn(
        "w-8 h-8 rounded-full border flex items-center justify-center text-xs font-bold transition-all duration-300",
        completed && "bg-primary/10 border-primary text-primary",
        active && "border-2 border-primary text-primary",
        !completed && !active && "border-border/50 text-muted-foreground",
      )}>
        {completed ? <Check className="h-4 w-4" /> : step}
      </div>
      <span className={cn(
        "text-[11px] font-mono uppercase tracking-[0.08em] transition-colors duration-300",
        active && "text-foreground",
        !active && "text-muted-foreground/60",
      )}>
        {label}
      </span>
    </div>
  );
}

function ConnectionCard({ source, index, onConnect }: { source: SourceConfig; index: number; onConnect: (id: ConnectionSource) => void }) {
  const Icon = source.icon;
  const ActionIcon = source.actionIcon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      className="group relative bg-muted/30 border border-border/50 p-6 rounded-[16px] hover:border-foreground/30 transition-all duration-300 cursor-pointer overflow-hidden"
    >
      <div className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div className="absolute top-0 left-0 right-0 h-1/2 bg-gradient-to-b from-foreground/[0.02] to-transparent scanline" />
      </div>
      <div className="flex justify-between items-start mb-8">
        <div className="w-12 h-12 bg-muted/50 border border-border/50 rounded-[10px] flex items-center justify-center">
          <Icon className="h-5 w-5 text-foreground" />
        </div>
        <span className="text-[11px] font-mono uppercase tracking-[0.08em] bg-muted/50 px-2 py-1 border border-border/50 rounded text-muted-foreground/60">
          {source.tag}
        </span>
      </div>
      <h3 className="text-lg font-semibold text-foreground mb-1">{source.title}</h3>
      <p className="text-sm text-muted-foreground leading-relaxed mb-6">{source.description}</p>
      <button
        onClick={() => onConnect(source.id)}
        className="w-full py-2.5 rounded-[10px] border border-border/50 text-[11px] font-mono uppercase tracking-[0.08em] hover:bg-foreground hover:text-background transition-all duration-200 flex items-center justify-center gap-2"
      >
        <ActionIcon className="h-3.5 w-3.5" />
        {source.actionLabel}
      </button>
    </motion.div>
  );
}

const logColors: Record<string, string> = {
  info: "text-muted-foreground",
  scan: "text-blue-400",
  topic: "text-foreground",
};

function cn(...inputs: (string | boolean | undefined | null)[]) {
  return inputs.filter(Boolean).join(" ");
}

export default function KnowledgeImportPage() {
  const [connecting, setConnecting] = useState<ConnectionSource | null>(null);
  const [showConsole, setShowConsole] = useState(false);
  const [logIndex, setLogIndex] = useState(0);
  const [stats, setStats] = useState({ entities: 0, topics: 0 });
  const [complete, setComplete] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  const handleConnect = useCallback((source: ConnectionSource) => {
    setConnecting(source);
    setShowConsole(true);
    setLogIndex(0);
    setStats({ entities: 0, topics: 0 });
    setComplete(false);
  }, []);

  useEffect(() => {
    if (!connecting || complete) return;
    if (logIndex >= terminalLogs.length) {
      setComplete(true);
      return;
    }

    const timer = setTimeout(() => {
      const log = terminalLogs[logIndex]!;
      setStats((prev) => ({
        entities: prev.entities + (log.type === "scan" ? Math.floor(Math.random() * 5) + 1 : 0),
        topics: prev.topics + (log.type === "topic" ? 1 : 0),
      }));
      setLogIndex((i) => i + 1);
    }, 400 + Math.random() * 300);

    return () => clearTimeout(timer);
  }, [logIndex, connecting, complete]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logIndex]);

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-foreground/20">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border/30 h-16 flex items-center px-6 md:px-10">
        <div className="max-w-[1200px] mx-auto w-full flex justify-between items-center">
          <span className="text-lg font-bold tracking-tight text-foreground">BrandOS</span>
          <div className="hidden md:flex gap-8 items-center">
            <span className="text-[11px] font-mono uppercase tracking-[0.08em] text-muted-foreground/60 cursor-not-allowed">Onboarding Phase: Active</span>
            <button className="bg-foreground text-background px-5 py-2 rounded-[10px] text-[11px] font-mono uppercase tracking-[0.08em] font-bold hover:opacity-90 transition-opacity">
              Exit Setup
            </button>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 px-6 md:px-10 max-w-[1200px] mx-auto">
        {/* Progress Stepper */}
        <div className="flex justify-between items-center max-w-xl mx-auto mb-16 relative">
          <div className="absolute top-4 left-0 w-full h-[1px] bg-border/30 -z-10" />
          <StepperDot step={1} current={2} label="Welcome" />
          <StepperDot step={2} current={2} label="Connect" />
          <StepperDot step={3} current={2} label="Style" />
          <StepperDot step={4} current={2} label="Index" />
        </div>

        {/* Hero */}
        <header className="text-center mb-20">
          <h1 className="text-2xl md:text-3xl font-semibold text-foreground mb-3 tracking-tight">
            Introduce yourself to the system.
          </h1>
          <p className="text-base text-muted-foreground max-w-xl mx-auto leading-relaxed">
            Connect your technical sources. BrandOS will analyze your repos, notes, and history to build your digital twin and professional index.
          </p>
        </header>

        {/* Connection Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-12">
          {sources.map((source, i) => (
            <ConnectionCard key={source.id} source={source} index={i} onConnect={handleConnect} />
          ))}
        </div>

        {/* Indexing Console */}
        <AnimatePresence>
          {showConsole && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="bg-muted/20 border border-border/50 rounded-[16px] overflow-hidden shadow-2xl mb-12"
            >
              {/* Terminal header */}
              <div className="px-4 py-3 border-b border-border/50 bg-muted/30 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/40" />
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/40" />
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/40" />
                  </div>
                  <span className="text-[11px] font-mono uppercase tracking-[0.08em] text-muted-foreground/60">BRAND_OS_INDEXER_V1.0</span>
                </div>
                <div className="flex items-center gap-2" id="indexing-status">
                  {!complete ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-foreground" />
                      <span className="text-[11px] font-mono uppercase tracking-[0.08em] text-foreground animate-pulse">
                        Indexing: {connecting && connecting.charAt(0).toUpperCase() + connecting.slice(1)}
                      </span>
                    </>
                  ) : (
                    <>
                      <Check className="h-3.5 w-3.5 text-green-400" />
                      <span className="text-[11px] font-mono uppercase tracking-[0.08em] text-green-400">Indexing Complete</span>
                    </>
                  )}
                </div>
              </div>

              {/* Terminal body */}
              <div className="p-6 h-56 overflow-y-auto bg-black/30 font-mono text-xs leading-relaxed space-y-1.5">
                <div className="text-muted-foreground/60 mb-2">[SYSTEM] Initialization complete. Starting deep discovery...</div>
                {terminalLogs.slice(0, logIndex).map((log, i) => {
                  const prefix = log.type === "scan" ? "SCAN" : log.type === "topic" ? "TOPIC" : "LOG";
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="opacity-0"
                      style={{ animation: "none" }}
                    >
                      <span className="text-muted-foreground/40">[{prefix}] </span>
                      <span className={logColors[log.type]}>{log.text}</span>
                    </motion.div>
                  );
                })}
                <div ref={logEndRef} />
              </div>

              {/* Terminal footer */}
              <div className="p-5 bg-muted/20 border-t border-border/50 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-[0.08em] text-muted-foreground/60 block mb-1">Entities Identified</span>
                  <span className="text-2xl font-semibold text-foreground tabular-nums">{stats.entities}</span>
                </div>
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-[0.08em] text-muted-foreground/60 block mb-1">Topics Extracted</span>
                  <span className="text-2xl font-semibold text-foreground tabular-nums">{stats.topics}</span>
                </div>
                <div className="flex items-center justify-end">
                  <button
                    disabled={!complete}
                    className={cn(
                      "bg-foreground text-background px-6 py-2.5 rounded-[10px] text-[11px] font-mono uppercase tracking-[0.08em] font-bold transition-all duration-200 flex items-center gap-2",
                      complete ? "hover:opacity-90" : "opacity-30 cursor-not-allowed",
                    )}
                  >
                    Confirm Connections
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Private & Encrypted */}
        <div className="relative h-48 rounded-[16px] overflow-hidden border border-border/50 bg-gradient-to-t from-background to-muted/10 flex items-center justify-center text-center p-8">
          <div className="max-w-lg">
            <Shield className="h-6 w-6 text-muted-foreground mx-auto mb-3" />
            <h2 className="text-lg font-semibold text-foreground mb-1">Private &amp; Encrypted</h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              All imported data is processed locally within your instance. BrandOS never stores your source credentials or raw documents beyond the indexing phase.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-10 bg-muted/20 border-t border-border/30">
        <div className="max-w-[1200px] mx-auto px-6 md:px-10 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex flex-col gap-1">
            <span className="text-lg font-bold tracking-tight text-foreground">BrandOS</span>
            <p className="text-sm text-muted-foreground">&copy; 2024 BrandOS. Engineered for clarity.</p>
          </div>
          <div className="flex gap-8">
            {["Security", "Privacy", "Terms", "Changelog"].map((link) => (
              <a key={link} href="#" className="text-[11px] font-mono uppercase tracking-[0.08em] text-muted-foreground/60 hover:text-foreground transition-all duration-200">
                {link}
              </a>
            ))}
          </div>
        </div>
      </footer>

      {/* Scanline animation keyframes */}
      <style jsx>{`
        .scanline {
          background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.03), transparent);
          animation: scanline 4s linear infinite;
          pointer-events: none;
        }
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
      `}</style>
    </div>
  );
}
