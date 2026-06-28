"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/stores/auth-store";
import { Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { accessToken } = useAuthStore();

  useEffect(() => {
    if (accessToken) {
      router.push("/app");
    } else {
      router.push("/login");
    }
  }, [accessToken, router]);

  return (
    <main className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </main>
  );
}