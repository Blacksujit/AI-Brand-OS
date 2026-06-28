"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, PenSquare, Clock, Brain, Settings, Github, Linkedin, User, LogOut, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/features/ui";
import { Avatar, AvatarFallback } from "@/features/ui/Avatar";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel } from "@/features/ui/DropdownMenu";
import { ScrollArea } from "@/features/ui/ScrollArea";
import { Separator } from "@/features/ui/Separator";
import { useAuthStore } from "@/lib/stores/auth-store";

const navItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Content", href: "/app/content", icon: PenSquare },
  { label: "History", href: "/app/history", icon: Clock },
  { label: "Knowledge", href: "/app/knowledge", icon: Brain },
  { label: "Trends", href: "/app/trends", icon: Github },
  { label: "Style", href: "/app/style", icon: Linkedin },
  { label: "Settings", href: "/app/settings", icon: Settings },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const { user, clearAuth } = useAuthStore();

  return (
    <aside className="hidden lg:flex lg:flex-col w-64 border-r border-sidebar-border bg-sidebar">
      <div className="p-4">
        <Link href="/app" className="text-lg font-bold">
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
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
      <Separator />
      <div className="p-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="w-full justify-start gap-3 h-auto py-2" asChild>
              <Link href="/app/settings">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{user?.display_name?.[0]?.toUpperCase() ?? "U"}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-medium truncate">{user?.display_name ?? "User"}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email ?? "Free Plan"}</p>
                </div>
                <ChevronRight className="h-4 w-4 opacity-50" />
              </Link>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/app/settings" className="flex items-center gap-2">
                <User className="h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/app/settings#connected" className="flex items-center gap-2">
                <Github className="h-4 w-4" />
                GitHub
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/app/settings#connected" className="flex items-center gap-2">
                <Linkedin className="h-4 w-4" />
                LinkedIn
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
      </div>
    </aside>
  );
}