"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  LogOut,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/features/ui/Button";
import { Avatar, AvatarFallback } from "@/features/ui/Avatar";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/features/ui/DropdownMenu";
import { ScrollArea } from "@/features/ui/ScrollArea";
import { Separator } from "@/features/ui/Separator";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useAppStore } from "@/lib/stores";

const primaryNav = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Content Briefs", href: "/app/briefs", icon: Sparkles },
  { label: "Content", href: "/app/content", icon: FileText },
  { label: "Knowledge", href: "/app/knowledge", icon: BookOpen },
  { label: "Analytics", href: "/app/analytics", icon: BarChart3 },
  { label: "Trends", href: "/app/trends", icon: TrendingUp },
  { label: "Style", href: "/app/style", icon: Palette },
] as const;

const secondaryNav = [
  { label: "Connections", href: "/app/connections", icon: Link2 },
  { label: "Settings", href: "/app/settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { user, clearAuth } = useAuthStore();
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);

  const isActive = (href: string) =>
    href === "/app" ? pathname === "/app" : pathname.startsWith(href);

  return (
    <aside
      className={cn(
        "hidden lg:flex lg:flex-col bg-sidebar transition-all duration-200",
        sidebarCollapsed ? "w-16" : "w-64",
      )}
    >
      <div className={cn("flex items-center h-16 border-b border-sidebar-border px-5", sidebarCollapsed && "justify-center px-0")}>
        <Link href="/app" className={cn("font-bold tracking-mc-heading text-sidebar-foreground", sidebarCollapsed ? "text-lg" : "text-xl")}>
          {sidebarCollapsed ? "B" : "BrandOS"}
        </Link>
      </div>

      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="space-y-1">
          {primaryNav.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-[20px] px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  sidebarCollapsed && "justify-center px-2",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {!sidebarCollapsed && (
          <>
            <Separator className="my-3 bg-sidebar-border" />
            <nav className="space-y-1">
              {secondaryNav.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-[20px] px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      active
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </>
        )}
      </ScrollArea>

      <div className={cn("border-t border-sidebar-border p-4", sidebarCollapsed && "flex justify-center")}>
        {sidebarCollapsed ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-xs">
                    {user?.display_name?.[0]?.toUpperCase() ?? "U"}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent side="right" className="w-56">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col">
                  <span>{user?.display_name ?? "User"}</span>
                  <span className="text-xs text-muted-foreground">{user?.email ?? ""}</span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={clearAuth} className="text-destructive focus:text-destructive">
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start gap-3 h-auto py-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-xs">
                    {user?.display_name?.[0]?.toUpperCase() ?? "U"}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-medium truncate text-sidebar-foreground">
                    {user?.display_name ?? "User"}
                  </p>
                  <p className="text-xs text-sidebar-foreground/50 truncate">
                    {user?.email ?? "Free Plan"}
                  </p>
                </div>
                <ChevronRight className="h-4 w-4 text-sidebar-foreground/30" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col">
                  <span>{user?.display_name ?? "User"}</span>
                  <span className="text-xs text-muted-foreground">{user?.email ?? ""}</span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/app/settings" className="flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  clearAuth();
                  window.location.href = "/login";
                }}
                className="text-destructive focus:text-destructive"
              >
                <LogOut className="h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </aside>
  );
}
