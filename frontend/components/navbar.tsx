"use client";

import { LogOut, User, ChevronDown } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/hooks/use-auth";

export function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((part) => part[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "?";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-background/80 backdrop-blur-md px-4 md:px-6">
      {/* Logo */}
      <div className="flex items-center gap-2.5">
        <div className="logo-gradient flex h-7 w-7 items-center justify-center rounded-lg text-white font-bold text-xs shadow-sm">
          R
        </div>
        <span className="brand-text font-semibold text-sm tracking-tight">ResearchGPT</span>
      </div>

      {/* User menu */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          className="flex items-center gap-2 rounded-full border border-border bg-card px-2.5 py-1.5 text-sm font-medium shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
        >
          <span className="logo-gradient flex h-6 w-6 items-center justify-center rounded-full text-white text-[10px] font-semibold">
            {initials}
          </span>
          <span className="hidden max-w-[8rem] truncate text-sm md:inline text-foreground">
            {user?.full_name ?? "Account"}
          </span>
          <ChevronDown className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ${menuOpen ? "rotate-180" : ""}`} />
        </button>

        {menuOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setMenuOpen(false)}
              aria-hidden="true"
            />
            <div
              role="menu"
              className="animate-scale-in absolute right-0 z-20 mt-2 w-60 rounded-xl border border-border bg-card p-1.5 card-shadow-md"
            >
              <div className="flex items-center gap-3 rounded-lg px-3 py-2.5 mb-1">
                <span className="logo-gradient flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white text-sm font-semibold">
                  {initials}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{user?.full_name}</p>
                  <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
                </div>
              </div>
              <div className="my-1 h-px bg-border mx-1" />
              <button
                type="button"
                role="menuitem"
                onClick={handleLogout}
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-destructive hover:bg-destructive/10 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  );
}
