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
  title: "BrandOS — AI Content Engine",
  description: "BrandOS automates your content research, strategy, writing, and analytics pipeline.",
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