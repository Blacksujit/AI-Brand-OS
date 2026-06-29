"use client";

import { motion } from "framer-motion";
import { LayoutDashboard, Settings, Search, FileText, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEntrance } from "@/lib/animations";

const sidebarItems = [
  { icon: LayoutDashboard, active: false },
  { icon: Settings, active: false },
  { icon: Search, active: true },
  { icon: FileText, active: false },
  { icon: BarChart3, active: false },
];

function DotGrid() {
  return (
    <svg className="absolute inset-0 w-full h-full opacity-[0.03]" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="dot-grid" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse">
          <circle cx="4" cy="4" r="0.75" fill="currentColor" />
        </pattern>
      </defs>
      <rect width="100" height="100" fill="url(#dot-grid)" />
    </svg>
  );
}

function SidebarMock() {
  return (
    <div className="flex flex-col items-center gap-3 py-4 px-2 border-r border-border/50 bg-muted/10 w-[52px]">
      {sidebarItems.map((item, i) => {
        const Icon = item.icon;
        return (
          <div
            key={i}
            className={cn(
              "w-7 h-7 rounded-[12px] flex items-center justify-center transition-colors",
              item.active
                ? "bg-orange-500/15 text-orange-400"
                : "text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/20",
            )}
          >
            <Icon className="h-3.5 w-3.5" />
          </div>
        );
      })}
    </div>
  );
}

function HeaderMock() {
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border/50 bg-muted/10">
      <div className="flex-1 h-7 max-w-xs rounded-[20px] border border-border/50 bg-muted/20" />
      <div className="w-6 h-6 rounded-full bg-muted/30" />
    </div>
  );
}

function ChatPanel() {
  return (
    <div className="flex flex-col flex-1 min-w-0">
      <HeaderMock />
      <div className="flex-1 p-3 space-y-3 overflow-hidden">
        <div className="flex items-start gap-2">
          <div className="w-6 h-6 rounded-full bg-orange-500/20 shrink-0 mt-1" />
          <div className="flex-1 rounded-[20px] bg-muted/20 border border-border/50 p-3">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              I&apos;ve analyzed your GitHub activity for this week. You spent most time on the API refactor.
            </p>
              <div className="flex gap-2 mt-2">
                <div className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400">
                  <span className="w-1.5 h-1.5 rotate-45 bg-orange-400 shrink-0" /> Signal
                </div>
              <div className="text-[10px] text-muted-foreground">2m ago</div>
            </div>
          </div>
        </div>
        <div className="flex items-start gap-2 flex-row-reverse">
          <div className="w-6 h-6 rounded-full bg-muted/30 shrink-0 mt-1" />
          <div className="flex-1 rounded-[20px] bg-orange-500/10 border border-orange-500/20 p-3">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Can you draft a post about the multi-agent patterns we implemented?
            </p>
          </div>
        </div>
        <div className="flex items-start gap-2">
          <div className="w-6 h-6 rounded-full bg-orange-500/20 shrink-0 mt-1" />
          <div className="flex-1 rounded-[20px] bg-muted/20 border border-border/50 p-3">
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Sure. I pulled the LangGraph migration notes and found 3 strong hooks. Drafting now.
            </p>
            <div className="flex gap-1 mt-2">
              <div className="h-1.5 w-12 rounded-full bg-muted/30 overflow-hidden">
                <div className="h-full w-4/5 rounded-full bg-orange-500/50" />
              </div>
              <span className="text-[10px] text-muted-foreground">Writing...</span>
            </div>
          </div>
        </div>
      </div>
      <div className="px-3 py-2 border-t border-border/50">
        <div className="h-8 rounded-[20px] border border-border/50 bg-muted/20 px-3 flex items-center gap-2">
          <span className="text-[11px] text-muted-foreground/50">Ask BrandOS...</span>
          <div className="ml-auto w-5 h-5 rounded-full border border-border/50 flex items-center justify-center">
            <span className="text-[10px] text-muted-foreground">↑</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function SidePanel() {
  return (
    <div className="w-[180px] border-l border-border/50 bg-muted/10 p-3 space-y-3 hidden md:flex flex-col">
      <div className="flex items-center gap-2 pb-2 border-b border-border/50">
        <div className="w-2 h-2 rounded-full bg-green-400" />
        <span className="text-[11px] font-medium">Live Signals</span>
      </div>
      {[
        { label: "PR #142 merged", type: "git", time: "2m" },
        { label: "3 trending topics in AI", type: "trend", time: "12m" },
        { label: "Draft ready for review", type: "doc", time: "24m" },
      ].map((item, i) => (
        <div key={i} className="rounded-[12px] border border-border/40 p-2 bg-muted/10">
          <p className="text-[11px] font-medium truncate">{item.label}</p>
          <p className="text-[9px] text-muted-foreground mt-0.5">{item.time} ago</p>
        </div>
      ))}
      <div className="mt-auto pt-2 border-t border-border/50">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-orange-500" />
          <span className="text-[10px] text-muted-foreground">Style Match 84%</span>
        </div>
      </div>
    </div>
  );
}

export function WorkspacePreview({ direction = "up" }: { direction?: "up" | "left" | "right" }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section id="workspace" className="px-4 lg:px-8 py-16 lg:py-24 max-w-7xl mx-auto">
      <motion.div
        {...sectionAnim}
        className="max-w-3xl mx-auto text-center mb-12"
      >
        <h2 className="text-3xl lg:text-5xl font-bold tracking-mc-heading mb-6">
          A Premium Desktop Experience
        </h2>
        <p className="text-lg text-muted-foreground">
          Workspace that adapts to your workflow — chat, signals, drafts, and knowledge in one place
        </p>
      </motion.div>

      <motion.div
        {...sectionAnim}
        transition={{ delay: 0.15 }}
        className="max-w-5xl mx-auto"
      >
        <div className="relative rounded-[20px] overflow-hidden border border-border/50 bg-gradient-to-b from-muted/30 to-muted/10 shadow-mc-1">
          <DotGrid />
          {/* Mock browser chrome */}
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border/50 bg-muted/20 relative">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
            </div>
            <div className="flex-1 max-w-[200px] mx-auto h-6 rounded-[12px] border border-border/50 bg-muted/20 flex items-center px-3">
              <span className="text-[10px] text-muted-foreground/50">app.brandos.dev</span>
            </div>
          </div>
          {/* Mock app shell */}
          <div className="flex h-[380px] sm:h-[460px] relative">
            <SidebarMock />
            <ChatPanel />
            <SidePanel />
          </div>
        </div>
      </motion.div>
    </section>
  );
}