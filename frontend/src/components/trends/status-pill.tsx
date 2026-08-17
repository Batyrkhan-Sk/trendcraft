import { cn } from "@/lib/format";
import { LEVEL_META, STATUS_META } from "@/lib/meta";
import type { Level, TrendStatus } from "@/lib/types";

/**
 * Lifecycle badge.
 *
 * Icon and text always ship together: two of the four status hues (growing green,
 * declining red) are indistinguishable under deuteranopia, so colour is a
 * reinforcement here and never the signal.
 */
export function StatusPill({
  status,
  size = "md",
  className,
}: {
  status: TrendStatus;
  size?: "sm" | "md";
  className?: string;
}) {
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border font-medium",
        size === "sm" ? "px-1.5 py-0.5 text-[10.5px]" : "px-2 py-1 text-[11.5px]",
        className,
      )}
      style={{ color: meta.color, background: meta.tint, borderColor: meta.ring }}
    >
      <Icon className={size === "sm" ? "size-3" : "size-3.5"} strokeWidth={2.4} />
      {meta.label}
    </span>
  );
}

/**
 * Ordinal level indicator (competition, difficulty, adaptability).
 *
 * Three filled dots out of three, plus the word. The dot count is the primary
 * encoding so this stays readable in grayscale and at 11px.
 */
export function LevelMeter({
  level,
  label,
  inverse,
  className,
}: {
  level: Level;
  label: string;
  /** When true, "low" is the good direction (competition, difficulty). */
  inverse?: boolean;
  className?: string;
}) {
  const meta = LEVEL_META[level];
  const good = inverse ? level === "low" : level === "high";
  const color = good ? "var(--color-state-good)" : level === "medium" ? "var(--color-state-warning)" : "var(--color-state-critical)";

  return (
    <div className={cn("flex items-center justify-between gap-3", className)}>
      <span className="text-[11.5px] text-ink-muted">{label}</span>
      <span className="flex items-center gap-1.5">
        <span className="flex gap-0.5" aria-hidden>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="h-2.5 w-1 rounded-[1px]"
              style={{ background: i < meta.dots ? color : "var(--color-line-strong)" }}
            />
          ))}
        </span>
        <span className="text-[11.5px] font-medium text-ink-secondary">{meta.label}</span>
      </span>
    </div>
  );
}

export function GrowthDelta({
  value,
  suffix,
  className,
}: {
  value: number;
  suffix?: string;
  className?: string;
}) {
  const up = value > 0;
  const flat = Math.abs(value) < 0.005;
  const color = flat
    ? "var(--color-ink-muted)"
    : up
      ? "var(--color-state-good)"
      : "var(--color-state-critical)";
  const pct = value * 100;
  return (
    <span
      className={cn("tabular inline-flex items-baseline gap-1 text-[12.5px] font-semibold", className)}
      style={{ color }}
    >
      <span aria-hidden>{flat ? "→" : up ? "↑" : "↓"}</span>
      {`${up && !flat ? "+" : ""}${pct.toFixed(Math.abs(pct) < 10 ? 1 : 0)}%`}
      {suffix ? <span className="text-[11px] font-normal text-ink-faint">{suffix}</span> : null}
    </span>
  );
}
