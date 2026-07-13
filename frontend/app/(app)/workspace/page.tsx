"use client";

import { useState } from "react";
import {
  LayoutDashboard,
  FileText,
  Brain,
  Settings,
  History,
  GitBranch,
  Sparkles,
  TrendingUp,
  BookOpen,
} from "lucide-react";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/app", active: false },
  { icon: FileText, label: "Content", href: "/app/content", active: false },
  { icon: Brain, label: "Strategy", href: "/app/workspace", active: true },
  { icon: History, label: "History", href: "/app/history", active: false },
];

const recentDrafts = [
  { title: "The Engineering Paradox", time: "2h ago" },
  { title: "Modular UI Systems", time: "Yesterday" },
  { title: "Building in Public: A Framework", time: "3d ago" },
];

const knowledgeContext = [
  { title: "The Mythical Man-Month", source: "Local PDF Library" },
  { title: "Tailwind v4 Specification", source: "Web Index" },
];

const aiTags = ["SYSTEMS", "ARCHITECTURE", "MODULARITY", "EFFICIENCY"];

export default function WorkspacePage() {
  const [publishing, setPublishing] = useState(false);

  const handlePublish = async () => {
    setPublishing(true);
    await new Promise((r) => setTimeout(r, 1500));
    setPublishing(false);
  };

  return (
    <div className="flex h-[calc(100vh-56px)] overflow-hidden bg-[#09090b]">
      {/* Left Sidebar */}
      <aside className="w-64 hidden lg:flex flex-col bg-zinc-950/50 border-r border-zinc-800 h-full py-6 px-3">
        <div className="mb-8">
          <div className="flex items-center gap-3 px-2 py-2 mb-6">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center text-black text-sm font-bold">B</div>
            <div>
              <div className="text-sm font-semibold text-white leading-tight">Personal OS</div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">System Active</div>
            </div>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm ${
                  item.active
                    ? "text-white bg-zinc-800/60 border-l-2 border-white"
                    : "text-zinc-400 hover:text-white hover:bg-zinc-800/30"
                }`}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.label}</span>
              </a>
            ))}
          </nav>
        </div>

        <div className="flex-1">
          <h3 className="px-3 text-[10px] font-mono uppercase tracking-widest text-zinc-600 mb-3">Recent Drafts</h3>
          <div className="space-y-1">
            {recentDrafts.map((draft) => (
              <div
                key={draft.title}
                className="group px-3 py-2 rounded-lg hover:bg-zinc-800/30 cursor-pointer transition-colors"
              >
                <p className="text-sm text-zinc-300 truncate group-hover:text-white transition-colors">{draft.title}</p>
                <p className="text-[11px] text-zinc-600 font-mono">{draft.time}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-auto pt-6 border-t border-zinc-800">
          <a
            href="/app/settings"
            className="flex items-center gap-3 px-3 py-2 text-zinc-400 hover:text-white transition-colors rounded-lg text-sm"
          >
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </a>
        </div>
      </aside>

      {/* Center Pane: Editor */}
      <section className="flex-1 flex flex-col overflow-y-auto px-6 md:px-12 py-8">
        <div className="w-full max-w-[720px] mx-auto">
          {/* Metadata bar */}
          <div className="flex items-center gap-3 mb-6">
            <span className="px-2 py-0.5 bg-zinc-900 border border-zinc-800 rounded text-[10px] font-mono text-zinc-400 uppercase tracking-wider">DRAFT</span>
            <span className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest">1,204 WORDS</span>
            <div className="ml-auto flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-400"></span>
              </span>
              <span className="text-[10px] font-mono text-zinc-500">AI Indexing</span>
            </div>
            <button
              onClick={handlePublish}
              disabled={publishing}
              className="bg-white text-black px-4 py-1.5 rounded-lg text-xs font-medium hover:bg-zinc-200 transition-all active:scale-95 disabled:opacity-50"
            >
              {publishing ? "Publishing..." : "Publish"}
            </button>
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-5xl font-semibold text-white leading-tight mb-4 focus:outline-none">
            Engineering Precision: The Future of Modular Architecture
          </h1>

          {/* Meta */}
          <div className="flex items-center gap-4 text-zinc-500 text-sm mb-12">
            <div className="flex items-center gap-1.5">
              <GitBranch className="h-4 w-4" />
              <span>Lead Architect</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Sparkles className="h-4 w-4" />
              <span>Oct 24, 2024</span>
            </div>
          </div>

          {/* Editor content */}
          <div className="space-y-6 text-zinc-300 leading-relaxed text-base">
            <p>
              In the rapidly evolving landscape of technical infrastructure, the transition from monolithic systems to granular, modular architectures is no longer a luxury&mdash;it is a fundamental requirement for scaling at velocity.
            </p>

            <div className="my-12 p-8 bg-zinc-900/50 border border-zinc-800 rounded-xl">
              <div className="aspect-video bg-zinc-800/50 rounded-lg flex items-center justify-center text-zinc-600">
                <div className="text-center">
                  <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p className="text-xs font-mono">Architecture visualization</p>
                </div>
              </div>
              <p className="mt-4 text-center text-xs font-mono text-zinc-600 italic">
                Fig 1.1 &mdash; Visualization of systemic modularity in distributed networks.
              </p>
            </div>

            <p>
              True sophistication in design is achieved not when there is nothing more to add, but when there is nothing left to take away. As we examine the metrics of performance across these new frameworks, we observe a consistent 40% reduction in cognitive overhead for developers interacting with well-defined APIs.
            </p>

            <blockquote className="border-l-2 border-white/30 pl-8 my-10 text-xl text-zinc-200 italic">
              &ldquo;The primary goal of architecture is to minimize the effort required to build and maintain a system while maximizing the potential for its evolution.&rdquo;
            </blockquote>

            <p>
              Modular design doesn&apos;t just apply to the back-end. It is a philosophy that must permeate every layer of the product&mdash;from the visual design system to the way we index and retrieve knowledge within our personal workspaces.
            </p>
          </div>
        </div>
      </section>

      {/* Right Pane: AI Insights */}
      <aside className="w-80 hidden xl:flex flex-col bg-zinc-950/50 border-l border-zinc-800 overflow-y-auto">
        <div className="p-6 space-y-8">
          {/* AI Summary */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">AI Research Summary</h4>
              <Brain className="h-4 w-4 text-blue-400" />
            </div>
            <div className="bg-zinc-900/50 p-4 rounded-xl border border-zinc-800">
              <p className="text-sm text-zinc-300 mb-3 leading-snug">
                This draft aligns with <strong className="text-white">84%</strong> of your previous technical essays on <strong className="text-white">Modularity</strong> and <strong className="text-white">Efficiency</strong>.
              </p>
              <div className="flex flex-wrap gap-2">
                {aiTags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-zinc-900 rounded text-[10px] font-mono text-zinc-400 border border-zinc-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Knowledge Context */}
          <div className="space-y-4">
            <h4 className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">Knowledge Context</h4>
            <div className="space-y-3">
              {knowledgeContext.map((item) => (
                <div
                  key={item.title}
                  className="p-3 rounded-xl border border-zinc-800 hover:bg-zinc-800/30 transition-colors cursor-pointer"
                >
                  <p className="text-sm text-zinc-200 font-medium mb-1 truncate">{item.title}</p>
                  <p className="text-[11px] text-zinc-600 leading-tight">{item.source}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Why this topic */}
          <div className="space-y-4">
            <h4 className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">Why this topic?</h4>
            <div className="p-4 rounded-xl bg-zinc-900/30 border border-zinc-800">
              <p className="text-sm text-zinc-400 italic">
                &ldquo;Engagement trends indicate a rising demand for content that bridges the gap between high-level management and low-level engineering implementation.&rdquo;
              </p>
              <div className="mt-3 flex items-center gap-2">
                <div className="h-1 flex-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-400/70 w-[70%] rounded-full"></div>
                </div>
                <span className="text-[10px] font-mono text-zinc-500">70% Relevance</span>
              </div>
            </div>
          </div>

          {/* Toolbelt */}
          <div className="pt-6 border-t border-zinc-800">
            <div className="grid grid-cols-2 gap-3">
              <button className="flex flex-col items-center justify-center p-4 border border-zinc-800 rounded-xl hover:bg-zinc-800/30 transition-colors">
                <GitBranch className="h-5 w-5 mb-2 text-zinc-400" />
                <span className="text-[10px] font-mono text-zinc-500">MAP</span>
              </button>
              <button className="flex flex-col items-center justify-center p-4 border border-zinc-800 rounded-xl hover:bg-zinc-800/30 transition-colors">
                <BookOpen className="h-5 w-5 mb-2 text-zinc-400" />
                <span className="text-[10px] font-mono text-zinc-500">KNOWLEDGE</span>
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile FAB */}
      <button className="fixed bottom-8 right-8 w-14 h-14 bg-white text-black rounded-full shadow-2xl flex items-center justify-center hover:scale-105 active:scale-95 transition-all z-[60] lg:hidden">
        <FileText className="h-6 w-6" />
      </button>
    </div>
  );
}
