"use client";

import { useState } from "react";
import { cn } from "@/lib/format";

export interface BarDatum {
  label: string;
  value: number;
  /** Text shown at the row's right edge — the formatted value. */
  display: string;
  color?: string;
  /** Extra context revealed on hover. */
  detail?: string;
}

/**
 * Horizontal bars with direct labels.
 *
 * Chosen over a vertical bar chart because every row is a named category with a
 * long label — rotating labels to fit a vertical axis is the classic failure.
 * Direct labels double as the secondary encoding, so rows that share a hue are
 * still distinguishable.
 */
export function BarList({
  data,
  className,
  barColor = "var(--color-series-1)",
  emptyLabel = "No data yet",
}: {
  data: BarDatum[];
  className?: string;
  barColor?: string;
  emptyLabel?: string;
}) {
  const [active, setActive] = useState<number | null>(null);

  if (!data.length) {
    return <div className={cn("py-6 text-[13px] text-ink-faint", className)}>{emptyLabel}</div>;
  }

  const max = Math.max(...data.map((d) => Math.abs(d.value)), 0.0001);

  return (
    <div className={cn("flex flex-col gap-2.5", className)}>
      {data.map((d, i) => {
        const width = (Math.abs(d.value) / max) * 100;
        const isActive = active === i;
        return (
          <div
            key={`${d.label}-${i}`}
            className="group"
            onMouseEnter={() => setActive(i)}
            onMouseLeave={() => setActive(null)}
          >
            <div className="flex items-baseline justify-between gap-3">
              <span className="truncate text-[12.5px] text-ink-secondary">{d.label}</span>
              <span className="tabular shrink-0 text-[12.5px] font-medium text-ink">
                {d.display}
              </span>
            </div>
            {/* Track sits at 4px so a full row of bars reads as a texture, not a stack of blocks. */}
            <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-3">
              <div
                className="h-full rounded-full transition-[width,opacity] duration-300"
                style={{
                  width: `${Math.max(width, 1.5)}%`,
                  background: d.color ?? barColor,
                  opacity: active === null || isActive ? 1 : 0.45,
                }}
              />
            </div>
            {d.detail && isActive ? (
              <div className="mt-1 text-[11px] leading-relaxed text-ink-faint">{d.detail}</div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
