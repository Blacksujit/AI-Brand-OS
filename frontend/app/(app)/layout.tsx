"use client";

import { useAuthStore } from "@/lib/stores/auth-store";
import { AppShell } from "@/components/app-shell";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useAuthStore(); // Ensures auth store is initialized

  return <AppShell>{children}</AppShell>;
}