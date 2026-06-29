"use client";

import { Moon, Sun } from "lucide-react";
import { useUIStore } from "@/lib/stores";
import { Button } from "@/features/ui/Button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/features/ui/Tooltip";

export function ThemeToggle() {
  const { theme, toggleTheme } = useUIStore();

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "dark" ? <Sun className="h-[1.2rem] w-[1.2rem]" /> : <Moon className="h-[1.2rem] w-[1.2rem]" />}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        <p>{theme === "dark" ? "Light mode" : "Dark mode"}</p>
      </TooltipContent>
    </Tooltip>
  );
}
