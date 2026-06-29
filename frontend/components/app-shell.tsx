"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAppStore } from "@/lib/stores";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div
        className={cn(
          "flex flex-1 flex-col transition-all duration-200",
          sidebarCollapsed ? "lg:ml-0" : "lg:ml-0",
        )}
      >
        <div className="h-24" /> {/* Spacer for floating header (24px top + 56px header + 16px) */}
        <Header />
        <main className="flex-1 px-4 pb-8 lg:px-6 xl:px-8 pt-6">
          <div className="mx-auto" style={{ maxWidth: "var(--content-max-width)" }}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
