"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/features/ui/Button";
import { cn } from "@/lib/utils";

const archetypes = [
  {
    id: "architect",
    title: "The Architect",
    description: "Deep, structural, and authoritative. This voice focuses on systems thinking, long-term scalability, and first-principles reasoning.",
    preview: `"The fundamental constraint of this architecture isn't the throughput—it's the state management. To build a truly resilient system, we must decouple the persistence layer from the execution context, ensuring that every transition is idempotent..."`
  },
  {
    id: "builder",
    title: "The Builder",
    description: "Pragmatic and tutorial-focused. A high-velocity voice that prioritizes shipping, clear implementations, and real-world results.",
    preview: `"Let's get this running. First, swap out the standard hook for a custom debounce. This cuts re-renders by 40% immediately. Here's the exact snippet you need to handle the edge case where the component unmounts mid-request..."`
  },
  {
    id: "researcher",
    title: "The Researcher",
    description: "Insightful and trend-aware. Connects the dots between emerging technologies and market shifts. Intellectual and curious.",
    preview: `"The shift toward edge computing isn't just a technical pivot; it's a sociological one. As we analyze the latest data from the Vercel ecosystem, a clear pattern emerges: the latency gap is becoming the primary differentiator in user retention..."`
  }
];

export default function PersonaSelectionPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleSubmit = () => {
    if (selectedId) {
      console.log("Persona selected:", selectedId);
      alert(`Persona "${archetypes.find(a => a.id === selectedId)?.title}" finalized. Welcome to BrandOS.`);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#09090b] text-white font-sans antialiased">
      {/* Subtle Background Effect */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0" />

      {/* Navigation Shell */}
      <header className="relative z-10 w-full h-20 flex items-center justify-between px-10 max-w-[1200px] mx-auto">
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg tracking-tight">BrandOS</span>
          <span className="px-2 py-0.5 rounded border border-gray-700 text-xs font-mono uppercase tracking-[0.05em] text-gray-400">
            ONBOARDING / STEP 02
          </span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          <span className="text-xs font-mono uppercase tracking-[0.05em] text-gray-400">KNOWLEDGE IMPORTED</span>
          <div className="w-12 h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="w-2/3 h-full bg-white" />
          </div>
        </div>
      </header>

      <main className="relative z-10 flex-grow flex flex-col items-center justify-center px-4 py-10 max-w-[1200px] mx-auto w-full">
        {/* Headline Section */}
        <div className="text-center mb-16 max-w-2xl">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 leading-tight">
            Select your Technical Voice
          </h1>
          <p className="text-lg text-gray-400 leading-relaxed">
            Our AI has ingested your documentation and history. Now, choose the editorial archetype that best represents how you want to be heard by the world.
          </p>
        </div>

        {/* Archetype Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-16 max-w-6xl">
          {archetypes.map((archetype, index) => (
            <motion.div
              key={archetype.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08, duration: 0.4 }}
              onClick={() => setSelectedId(archetype.id)}
              className={cn(
                "voice-card group cursor-pointer relative bg-zinc-950 border p-8 flex flex-col h-[480px]",
                selectedId === archetype.id
                  ? "border-white bg-white/[0.03]"
                  : "border-zinc-800 hover:border-gray-700",
                "rounded-none"
              )}
            >
              <div className={cn(
                "selection-indicator absolute top-4 right-4 text-brand-orange",
                selectedId === archetype.id ? "opacity-100" : "opacity-0",
                "transition-opacity duration-200"
              )}>
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.042-1.416-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
              </div>
              <div className="mb-8">
                <span className="text-gray-400 text-xs font-mono uppercase tracking-[0.05em] mb-2 block">STYLE ARCHETYPE</span>
                <h3 className="text-2xl font-semibold text-white">{archetype.title}</h3>
              </div>
              <p className="text-gray-400 text-base mb-8 flex-grow leading-relaxed">
                {archetype.description}
              </p>
              <div className="bg-zinc-950 border border-gray-800 p-4 rounded-sm overflow-hidden flex flex-col h-40">
                <span className="text-gray-400 text-xs font-mono uppercase tracking-[0.05em] mb-3 block">AI PREVIEW</span>
                <div className="text-gray-400 text-sm font-mono leading-relaxed overflow-y-auto">
                  {archetype.preview}
                </div>
              </div>
            </motion.div>
          ))}

        </div>

        {/* Action Section */}
        <div className="flex flex-col items-center gap-6">
          <Button
            className="px-12 py-4 rounded-sm disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:scale-[1.02] active:scale-[0.98]"
            disabled={!selectedId}
            onClick={handleSubmit}
            size="lg"
          >
            Finalize My AI Persona
          </Button>
          <p className="text-xs font-mono uppercase tracking-[0.05em] text-gray-400">
            YOU CAN RE-CALIBRATE THIS AT ANY TIME IN SETTINGS
          </p>
        </div>
      </main>

      {/* Footer Identity */}
      <footer className="relative z-10 w-full py-12 px-10 mt-auto">
        <div className="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between items-center border-t border-gray-800 pt-8 gap-6">
          <p className="text-base text-gray-400">© 2024 BrandOS. Engineered for clarity.</p>
          <div className="flex gap-8">
            <a className="text-xs font-mono uppercase tracking-[0.05em] text-gray-400 hover:text-white transition-colors" href="#">Privacy Policy</a>
            <a className="text-xs font-mono uppercase tracking-[0.05em] text-gray-400 hover:text-white transition-colors" href="#">System Status</a>
          </div>
        </div>
      </footer>
    </div>
  );
}