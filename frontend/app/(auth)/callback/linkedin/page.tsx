"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { apiPostValidated, TokenResponseSchema, setTokens } from "@/lib/api/client";

function LinkedInCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const redirect = searchParams.get("state") || "/app";

  useEffect(() => {
    async function handleCallback() {
      if (error) {
        toast.error(`LinkedIn OAuth failed: ${error}`);
        router.push("/login");
        return;
      }

      if (!code) {
        toast.error("No authorization code received");
        router.push("/login");
        return;
      }

      try {
        const data = await apiPostValidated("/auth/linkedin/callback", TokenResponseSchema, { code });
        setTokens(data.access_token, data.refresh_token);
        toast.success("Connected to LinkedIn!");
        router.push(redirect);
        router.refresh();
      } catch (err) {
        toast.error("Failed to connect LinkedIn");
        router.push("/login");
      }
    }

    handleCallback();
  }, [code, error, redirect, router]);

  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
        <p className="text-muted-foreground">Connecting to LinkedIn...</p>
      </div>
    </main>
  );
}

export default function LinkedInCallbackPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary mb-4" />
          <p className="text-muted-foreground">Connecting...</p>
        </div>
      </main>
    }>
      <LinkedInCallbackContent />
    </Suspense>
  );
}