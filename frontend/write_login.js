const fs = require('fs');

const content = `"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/features/ui/Button";
import { Input } from "@/features/ui/Input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/features/ui/Card";
import { Separator } from "@/features/ui/Separator";
import { Label } from "@/features/ui/Label";
import { Github, Mail, Lock, AlertCircle, Loader2 } from "lucide-react";
import { LoginRequestSchema } from "@/lib/validators/auth";
import { apiPostValidated, TokenResponseSchema, setTokens } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth";
import { useUIStore } from "@/stores/ui";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/app";
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState("");
  const [cardRotation, setCardRotation] = useState({ x: 0, y: 0 });
  const { setUser } = useAuthStore();
  const { setCommandPaletteOpen, setNotificationPanelOpen } = useUIStore();

  useEffect(() => {
    const handleMouseMove = (e) => {
      const xAxis = (window.innerWidth / 2 - e.pageX) / 100;
      const yAxis = (window.innerHeight / 2 - e.pageY) / 100;
      setCardRotation({ x: yAxis, y: xAxis });
    };

    const handleMouseEnter = () => {
      document.body.style.transition = "none";
    };

    const handleMouseLeave = () => {
      document.body.style.transition = "all 0.5s ease";
      setCardRotation({ x: 0, y: 0 });
    };

    document.body.addEventListener("mousemove", handleMouseMove);
    document.body.addEventListener("mouseenter", handleMouseEnter);
    document.body.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      document.body.removeEventListener("mousemove", handleMouseMove);
      document.body.removeEventListener("mouseenter", handleMouseEnter);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const result = LoginRequestSchema.safeParse({ email, password });
    if (!result.success) {
      toast.error("Invalid email or password");
      setIsLoading(false);
      return;
    }

    try {
      const data = await apiPostValidated("/auth/login", TokenResponseSchema, { email, password });
      setTokens(data.access_token, data.refresh_token);
      toast.success("Welcome back!");
      router.push(redirect);
      router.refresh();
    } catch (error) {
      if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Login failed");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-[#09090b] px-4 py-12 selection:bg-[#CF4500]/30 selection:text-white">
      {/* Background Layer */}
      <div className="fixed inset-0 technical-grid pointer-events-none" style={{
        backgroundSize: "40px 40px",
        backgroundImage: `
          linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
        `
      }} aria-hidden="true" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_center,_transparent_0%,_#09090b_100%)] pointer-events-none opacity-80" aria-hidden="true" />

      {/* Identity Anchor (Top) */}
      <header className="absolute top-12 flex flex-col items-center gap-2">
        <span className="font-bold text-white text-xl tracking-tight">BrandOS</span>
        <p className="text-xs font-mono uppercase tracking-wider text-gray-400 opacity-60">System Authentication v2.4</p>
      </header>

      {/* Login Container */}
      <main className="z-10 w-full max-w-[420px] px-6" style={{ transform: `rotateY(${cardRotation.y}deg) rotateX(${cardRotation.x}deg)` }}>
        <Card className="bg-zinc-950/50 border border-zinc-800 p-8 md:p-10 flex flex-col gap-8 relative overflow-hidden shadow-2xl">
          {/* Subtle internal glow for editorial depth */}
          <div className="absolute inset-0 border border-white/5 pointer-events-none" aria-hidden="true" />
          {/* Header */}
          <div className="space-y-2 text-center">
            <h1 className="text-2xl md:text-3xl font-semibold text-white">Initialize Session</h1>
            <p className="text-gray-400">Turn today's work into tomorrow's reputation.</p>
          </div>

          {/* Primary Action: GitHub OAuth */}
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

            {/* Divider */}
            <div className="flex items-center gap-4 py-2">
              <div className="h-[1px] flex-1 bg-zinc-800 opacity-30" />
              <span className="text-xs font-mono uppercase tracking-widest text-gray-400">OR EMAIL</span>
              <div className="h-[1px] flex-1 bg-zinc-800 opacity-30" />
            </div>

            {/* Form */}
            <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs font-mono uppercase tracking-wider text-gray-400 block">Identifier</Label>
                <div className="relative">
                  <input
                    className="w-full h-12 bg-zinc-950 border border-zinc-800 px-4 text-white placeholder:text-gray-500 focus:outline-none focus:border-white transition-all font-sans"
                    id="email"
                    placeholder="dev@brandos.tech"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-xs font-mono uppercase tracking-wider text-gray-400 block">Secret</Label>
                <div className="relative">
                  <input
                    className="w-full h-12 bg-zinc-950 border border-zinc-800 px-4 pr-10 text-white placeholder:text-gray-500 focus:outline-none focus:border-white transition-all font-sans"
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 hover:bg-zinc-800/80 transition-colors rounded-full p-1"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    <span className="text-gray-500 text-sm">{showPassword ? "HIDE" : "SHOW"}</span>
                  </button>
                </div>
              </div>
              <button
                type="submit"
                className="w-full h-12 border border-zinc-800 bg-transparent text-white font-medium hover:bg-zinc-800/50 transition-colors duration-200 rounded-lg"
              >
                Request Magic Link
              </button>
            </form>
          </div>

          {/* Security Meta */}
          <div className="pt-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-primary text-[16px]" aria-hidden="true">LOCK</span>
              <span className="text-xs font-mono text-gray-400 opacity-60">SSL: SECURED</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-gray-400 opacity-60">INSTANCE: US-EAST-1</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Secondary Navigation */}
      <footer className="absolute bottom-12 w-full max-w-[420px] px-6 flex justify-between">
        <Link href="#" className="text-xs font-mono uppercase tracking-widest text-gray-400 hover:text-white transition-colors duration-200">Privacy Protocol</Link>
        <Link href="#" className="text-xs font-mono uppercase tracking-widest text-gray-400 hover:text-white transition-colors duration-200">Terminal Access</Link>
      </footer>
    </main>

    <style jsx>{`
      .technical-grid {
        background-size: 40px 40px;
        background-image:
          linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
      }
      .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
        font-size: 20px;
      }
      .glass-stroke {
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
      }
    `}</style>
  );
}
`;

fs.writeFileSync('app/(auth)/login/page.tsx', content, 'utf8');
console.log('Login page written successfully');