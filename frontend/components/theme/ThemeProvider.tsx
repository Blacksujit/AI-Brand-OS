"use client";

import { useEffect } from "react";
import { useUIStore } from "@/lib/stores";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("brandos-theme", theme);
    } catch {}
  }, [theme]);

  return <>{children}</>;
}
