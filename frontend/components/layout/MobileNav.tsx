"use client";

import { Menu } from "lucide-react";
import { Button } from "@/features/ui";
import { Sheet, SheetContent, SheetTrigger } from "@/features/ui/Sheet";
import Link from "next/link";
import { Separator } from "@/features/ui/Separator";
import { ScrollArea } from "@/features/ui/ScrollArea";
import { LayoutDashboard, PenSquare, Clock, Brain, Settings, Github, Linkedin } from "lucide-react";
import { cn } from "@/lib/utils";
import { usePathname } from "next/navigation";

const navItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Content", href: "/app/content", icon: PenSquare },
  { label: "History", href: "/app/history", icon: Clock },
  { label: "Knowledge", href: "/app/knowledge", icon: Brain },
  { label: "Trends", href: "/app/trends", icon: Github },
  { label: "Style", href: "/app/style", icon: Linkedin },
  { label: "Settings", href: "/app/settings", icon: Settings },
] as const;

export function MobileNav() {
  const pathname = usePathname();

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle navigation</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64 p-0">
        <div className="p-4">
          <Link
            href="/app"
            className="text-lg font-bold"
            onClick={() => document.querySelector('[role="dialog"]')?.querySelector('button')?.click()}
          >
            BrandOS
          </Link>
        </div>
        <Separator />
        <ScrollArea className="flex-1 px-3 py-2">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => document.querySelector('[role="dialog"]')?.querySelector('button')?.click()}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent hover:text-accent-foreground"
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