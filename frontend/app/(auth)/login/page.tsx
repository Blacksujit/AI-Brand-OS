"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/app";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 1000));
      router.push(redirect);
    } catch {
      // error handled
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-[#09090b] px-4 py-12">
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: "radial-gradient(circle at 25% 25%, rgba(207,69,0,0.08) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(207,69,0,0.05) 0%, transparent 50%)"
      }} aria-hidden="true" />

      <header className="absolute top-12 flex flex-col items-center gap-2">
        <span className="font-bold text-white text-xl tracking-tight">BrandOS</span>
        <p className="text-xs font-mono uppercase tracking-wider text-gray-500/60">System Authentication</p>
      </header>

      <main className="z-10 w-full max-w-[420px] px-6">
        <div className="bg-zinc-950/50 border border-zinc-800 p-8 md:p-10 flex flex-col gap-8 relative overflow-hidden shadow-2xl rounded-2xl">
          <div className="absolute inset-0 border border-white/[0.03] pointer-events-none rounded-2xl" aria-hidden="true" />
          <div className="space-y-2 text-center">
            <h1 className="text-2xl md:text-3xl font-semibold text-white">Initialize Session</h1>
            <p className="text-gray-400">Turn today&apos;s work into tomorrow&apos;s reputation.</p>
          </div>

          <div className="flex flex-col gap-4">
            <button
              type="button"
              className="w-full h-12 bg-white text-black font-medium flex items-center justify-center gap-3 active:scale-[0.98] transition-all hover:bg-gray-100 duration-200 rounded-lg"
            >
              <svg className="inline-block" fill="currentColor" height="20" viewBox="0 0 24 24" width="20">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.041-1.61-4.041-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"></path>
              </svg>
              <span className="font-medium">Continue with GitHub</span>
            </button>

            <div className="flex items-center gap-4 py-2">
              <div className="h-[1px] flex-1 bg-zinc-800/50" />
              <span className="text-xs font-mono uppercase tracking-widest text-gray-500">OR EMAIL</span>
              <div className="h-[1px] flex-1 bg-zinc-800/50" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="email" className="text-xs font-mono uppercase tracking-wider text-gray-500 block">Identifier</label>
                <input
                  className="w-full h-12 bg-zinc-950 border border-zinc-800 px-4 text-white placeholder:text-gray-600 focus:outline-none focus:border-white/50 transition-all font-sans rounded-lg"
                  id="email"
                  placeholder="dev@brandos.tech"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label htmlFor="password" className="text-xs font-mono uppercase tracking-wider text-gray-500 block">Secret</label>
                <input
                  className="w-full h-12 bg-zinc-950 border border-zinc-800 px-4 text-white placeholder:text-gray-600 focus:outline-none focus:border-white/50 transition-all font-sans rounded-lg"
                  id="password"
                  type="password"
                  placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full h-12 border border-zinc-800 bg-transparent text-white font-medium hover:bg-zinc-800/50 transition-colors duration-200 rounded-lg disabled:opacity-50"
              >
                {isLoading ? "Connecting..." : "Continue with Email"}
              </button>
            </form>
          </div>

          <div className="pt-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-gray-500 text-xs font-mono">SSL: SECURED</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-gray-500/60">INSTANCE: US-EAST-1</span>
            </div>
          </div>
        </div>
      </main>

      <footer className="absolute bottom-12 w-full max-w-[420px] px-6 flex justify-between">
        <Link href="#" className="text-xs font-mono uppercase tracking-widest text-gray-500 hover:text-white transition-colors duration-200">Privacy Protocol</Link>
        <Link href="#" className="text-xs font-mono uppercase tracking-widest text-gray-500 hover:text-white transition-colors duration-200">Terminal Access</Link>
      </footer>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="relative min-h-screen flex items-center justify-center bg-[#09090b]">
        <div className="text-gray-500 font-mono text-sm">Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
