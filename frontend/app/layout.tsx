import type { Metadata } from "next";
import { Sofia_Sans } from "next/font/google";
import { Providers } from "@/components/providers";
import { ErrorBoundary } from "@/components/error-boundary";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
import { ThemeScript } from "@/components/theme/ThemeScript";
import "./globals.css";

const sofiaSans = Sofia_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sofia-sans",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://brandos.dev"),
  title: {
    default: "BrandOS — Knowledge-First AI Content Engine for Technical Professionals",
    template: "%s | BrandOS",
  },
  description:
    "BrandOS writes from your actual work — GitHub, notes, and projects. No hallucinated credentials. Human-reviewed, always.",
  openGraph: {
    title: "BrandOS — Knowledge-First AI Content Engine",
    description:
      "BrandOS writes from your actual work — GitHub, notes, and projects. No hallucinated credentials. Human-reviewed, always.",
    url: "https://brandos.dev",
    siteName: "BrandOS",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BrandOS — Knowledge-First AI Content Engine",
    description:
      "BrandOS writes from your actual work — GitHub, notes, and projects. No hallucinated credentials. Human-reviewed, always.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className={sofiaSans.className}>
        <ThemeProvider>
          <Providers>
            <ErrorBoundary>{children}</ErrorBoundary>
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}