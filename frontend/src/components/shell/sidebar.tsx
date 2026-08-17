"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bookmark,
  Compass,
  Flame,
  Settings,
  Sparkles,
  TrendingUp,
  Wand2,
} from "lucide-react";
import { cn } from "@/lib/format";

const NAV = [
  { href: "/discover", label: "Discover", icon: Compass },
  { href: "/trending", label: "Trending", icon: Flame },
  { href: "/rising", label: "Rising", icon: TrendingUp },
  { href: "/scenarios", label: "Scenarios", icon: Wand2 },
  { href: "/saved", label: "Saved", icon: Bookmark },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 z-30 hidden h-dvh w-[216px] shrink-0 flex-col border-r border-line bg-canvas/80 backdrop-blur lg:flex">
      <Link href="/" className="flex items-center gap-2.5 px-5 py-5">
        <span className="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-brand to-accent">
          <Sparkles className="size-4 text-canvas" strokeWidth={2.5} />
        </span>
        <span className="text-[15px] font-semibold tracking-tight">TrendCraft</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors",
                active
                  ? "bg-surface-2 text-ink"
                  : "text-ink-muted hover:bg-surface/70 hover:text-ink-secondary",
              )}
            >
              {active ? (
                <span className="absolute inset-y-1.5 -left-3 w-0.5 rounded-full bg-gradient-to-b from-brand to-accent" />
              ) : null}
              <Icon className="size-4" strokeWidth={2} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3">
        <div className="rounded-xl border border-line bg-surface p-3">
          <div className="text-[12px] font-medium text-ink">Pipeline</div>
          <p className="mt-1 text-[11px] leading-relaxed text-ink-muted">
            Collection runs every 3h, analysis continuously, re-clustering nightly.
          </p>
          <Link
            href="/settings"
            className="mt-2 inline-flex text-[11px] font-medium text-[#a99bff] hover:underline"
          >
            View status
          </Link>
        </div>
      </div>
    </aside>
  );
}

/** Compact nav for viewports below the sidebar breakpoint. */
export function MobileNav() {
  const pathname = usePathname();
  return (
    <div className="sticky top-0 z-30 flex items-center gap-1 overflow-x-auto border-b border-line bg-canvas/90 px-3 py-2 backdrop-blur lg:hidden rail">
      <Link href="/" className="mr-2 flex shrink-0 items-center gap-2">
        <span className="grid size-6 place-items-center rounded-md bg-gradient-to-br from-brand to-accent">
          <Sparkles className="size-3.5 text-canvas" strokeWidth={2.5} />
        </span>
        <span className="text-[13px] font-semibold tracking-tight">TrendCraft</span>
      </Link>
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[12px] font-medium",
              active ? "bg-surface-2 text-ink" : "text-ink-muted",
            )}
          >
            <Icon className="size-3.5" />
            {label}
          </Link>
        );
      })}
    </div>
  );
}
