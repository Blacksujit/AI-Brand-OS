"use client";

import { MobileNav } from "./MobileNav";

export function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 lg:px-6">
      <MobileNav />
      <div className="flex-1" />
    </header>
  );
}