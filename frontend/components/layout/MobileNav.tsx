"use client";

import { Menu } from "lucide-react";
import { Button } from "@/features/ui/Button";
import { Sheet, SheetContent, SheetTrigger } from "@/features/ui/Sheet";
import Link from "next/link";
import { ScrollArea } from "@/features/ui/ScrollArea";
import {
  LayoutDashboard,
  Sparkles,
  FileText,
  BookOpen,
  BarChart3,
  TrendingUp,
  Palette,
  Link2,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Content Briefs", href: "/app/briefs", icon: Sparkles },
  { label: "Content", href: "/app/content", icon: FileText },
  { label: "Knowledge", href: "/app/knowledge", icon: BookOpen },
  { label: "Analytics", href: "/app/analytics", icon: BarChart3 },
  { label: "Trends", href: "/app/trends", icon: TrendingUp },
  { label: "Style", href: "/app/style", icon: Palette },
  { label: "Connections", href: "/app/connections", icon: Link2 },
  { label: "Settings", href: "/app/settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  const closeSheet = () => {
    document.querySelector('[role="dialog"]')?.querySelector("button")?.click();
  };

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle navigation</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64 p-0">
        <div className="flex items-center h-14 px-4 border-b">
          <Link href="/app" className="text-xl font-bold" onClick={closeSheet}>
            BrandOS
          </Link>
        </div>
        <ScrollArea className="flex-1 px-2 py-3">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.href === "/app"
                  ? pathname === "/app"
                  : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={closeSheet}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent hover:text-accent-foreground",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
