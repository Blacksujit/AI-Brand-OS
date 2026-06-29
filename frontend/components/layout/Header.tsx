"use client";

import { Bell, Search } from "lucide-react";
import { MobileNav } from "./MobileNav";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { Button } from "@/features/ui/Button";
import { Avatar, AvatarFallback } from "@/features/ui/Avatar";
import { useAuthStore } from "@/lib/stores/auth-store";
import { useUIStore } from "@/lib/stores";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/features/ui/Tooltip";

export function Header() {
  const { user } = useAuthStore();
  const { setCommandPaletteOpen, setNotificationPanelOpen } = useUIStore();

  return (
    <header className="fixed top-6 left-1/2 -translate-x-1/2 z-30 flex h-14 items-center gap-2 bg-[hsl(var(--card))] px-6 lg:px-8 shadow-mc-1 rounded-[999px] w-[calc(100%-2rem)] lg:w-[calc(100%-4rem)] max-w-7xl">
      <MobileNav />

      <div className="flex-1" />

      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon" onClick={() => setCommandPaletteOpen(true)} aria-label="Search" className="rounded-full hover:bg-accent/80 transition-colors">
            <Search className="h-[1.2rem] w-[1.2rem]" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Search (⌘K)</p>
        </TooltipContent>
      </Tooltip>

      <ThemeToggle />

      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon" onClick={() => setNotificationPanelOpen(true)} aria-label="Notifications" className="rounded-full hover:bg-accent/80 transition-colors">
            <Bell className="h-[1.2rem] w-[1.2rem]" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Notifications</p>
        </TooltipContent>
      </Tooltip>

      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="ghost" size="icon" className="rounded-full hover:bg-accent/80 transition-colors" asChild>
            <a href="/app/settings">
              <Avatar className="h-7 w-7 ring-2 ring-border hover:ring-primary/50 transition-all">
                <AvatarFallback className="text-xs font-medium">
                  {user?.display_name?.[0]?.toUpperCase() ?? "U"}
                </AvatarFallback>
              </Avatar>
            </a>
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>Settings</p>
        </TooltipContent>
      </Tooltip>
    </header>
  );
}
