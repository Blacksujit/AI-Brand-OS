"use client";

import { motion } from "framer-motion";
import { Folder, Terminal, FileText, MessageSquare, ChevronRight } from "lucide-react";
import { useEntrance, type Direction } from "@/lib/animations";

const knowledgeSources = [
  { icon: Terminal, name: "GitHub: repo/main", active: true },
  { icon: FileText, name: "Notion: Engineering", active: false },
  { icon: MessageSquare, name: "Slack: #eng-design", active: false },
];

const contentIdeas = [
  { title: "React Server Components", progress: 80 },
  { title: "Postgres Indexing Strategy", progress: 66 },
];

export function ProductPreview({ direction = "up" }: { direction?: Direction }) {
  const sectionAnim = useEntrance(direction);

  return (
    <section id="product-preview" className="px-6 pb-32 max-w-7xl mx-auto">
      <motion.div
        {...sectionAnim}
        className="rounded-xl overflow-hidden shadow-2xl border border-border/50 bg-gradient-to-b from-muted/30 to-muted/10 backdrop-blur-sm"
      >
        <div className="bg-muted/20 border-b border-border/50 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex gap-1.5">
              <div className="size-3 rounded-full bg-zinc-700" />
              <div className="size-3 rounded-full bg-zinc-700" />
              <div className="size-3 rounded-full bg-zinc-700" />
            </div>
            <div className="h-4 w-px bg-border/50 mx-2" />
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <Folder className="h-3.5 w-3.5" />
              projects / brand-engine / dashboard
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-secondary bg-secondary/10 px-2 py-0.5 rounded font-mono">Syncing...</span>
            <div className="size-8 rounded-full bg-muted/30 border border-border/50" />
          </div>
        </div>
        <div className="grid grid-cols-12 min-h-[600px]">
          <aside className="col-span-3 border-r border-border/50 bg-muted/20 p-6">
            <div className="mb-8">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4">Knowledge Sources</p>
              <ul className="space-y-3">
                {knowledgeSources.map((source) => (
                  <li
                    key={source.name}
                    className={`flex items-center gap-3 text-sm p-2 rounded border ${
                      source.active
                        ? "text-foreground bg-muted/30 border-border/50"
                        : "text-muted-foreground border-transparent hover:bg-muted/20"
                    } transition-colors`}
                  >
                    <source.icon className="h-4 w-4" />
                    {source.name}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-4">Content Ideas</p>
              <div className="space-y-4">
                {contentIdeas.map((idea) => (
                  <div key={idea.title} className="p-3 bg-background border border-border/50 rounded">
                    <p className="text-xs font-medium text-foreground mb-1">{idea.title}</p>
                    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full bg-secondary" style={{ width: `${idea.progress}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </aside>
          <main className="col-span-9 p-8 flex flex-col gap-6">
            <div className="flex items-end justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-1">Draft: Edge Runtime Optimization</h2>
                <p className="text-sm text-muted-foreground">Synthesized from 4 PRs and 1 Architectural Decision Record</p>
              </div>
              <div className="flex gap-2">
                <button className="px-4 py-2 text-xs font-bold border border-border/50 rounded hover:bg-muted/30 transition-colors">
                  Edit Prompt
                </button>
                <button className="px-4 py-2 text-xs font-bold bg-foreground text-background rounded hover:bg-foreground/90 transition-colors">
                  Approve &amp; Queue
                </button>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-6 flex-1">
              <div className="col-span-2 rounded-lg border border-border/50 bg-muted/20 backdrop-blur-sm p-6 flex flex-col gap-4">
                <div className="flex items-center justify-between pb-4 border-b border-border/50">
                  <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">AI Suggestion</span>
                  <span className="flex items-center gap-1.5 text-xs text-green-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                    High Authenticity
                  </span>
                </div>
                <div className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                  Last week we moved our auth middleware to the edge. The cold start latency was killing our LCP.
                  {"\n\n"}
                  The fix wasn&apos;t caching&mdash;it was moving the logic to a WASM module. Here&apos;s why most &quot;edge ready&quot; libraries still fail under load...
                  {"\n\n"}
                  [Insert code snippet showing the fetch interceptor pattern]
                  {"\n\n"}
                  1. Shared state is your enemy.
                  {"\n"}
                  2. Binary protocols outperform JSON at scale.
                  {"\n"}
                  3. Cold starts are actually bundle size problems in disguise.
                </div>
              </div>
              <div className="col-span-1 flex flex-col gap-4">
                <div className="bg-muted/20 rounded-lg p-5 border border-border/50">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-4">Quality Score</h3>
                  <div className="flex items-center gap-4 mb-4">
                    <div className="text-4xl font-black text-foreground">94</div>
                    <div className="text-[10px] text-muted-foreground font-medium">Top 5% for<br />Technical Depth</div>
                  </div>
                  <div className="space-y-3">
                    {[
                      { label: "Clarity", value: "98%" },
                      { label: "Unique Insights", value: "91%" },
                      { label: "Personal Tone", value: "92%" },
                    ].map((item) => (
                      <div key={item.label} className="flex justify-between text-xs">
                        <span className="text-muted-foreground">{item.label}</span>
                        <span className="text-foreground">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-muted/20 rounded-lg p-5 border border-border/50">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Refinement Loop</h3>
                  <div className="space-y-3">
                    {["Add more code context", "Explain the 'Why' deeper"].map((action) => (
                      <button
                        key={action}
                        className="w-full text-left p-2 rounded hover:bg-muted/30 text-xs flex items-center justify-between group transition-all"
                      >
                        <span>{action}</span>
                        <ChevronRight className="h-3.5 w-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </motion.div>
    </section>
  );
}
