import { cn } from "@/lib/format";

/**
 * Hero figure for the opportunity score.
 *
 * A single number is the job here, so the ring is a magnitude cue around the
 * figure rather than a chart in its own right — no ticks, no legend, no tooltip.
 * The arc uses one hue at varying step; the score's *meaning* is carried by the
 * number and the caption beneath it.
 */
export function ScoreRing({
  value,
  size = 108,
  stroke = 7,
  label = "Opportunity",
  caption,
  className,
}: {
  value: number;
  size?: number;
  stroke?: number;
  label?: string;
  caption?: string;
  className?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const dash = (clamped / 100) * circumference;
  const gradientId = `ring-${size}-${Math.round(clamped)}`;

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={`${label} score ${Math.round(clamped)} out of 100`}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stopColor="#7c5cff" />
              <stop offset="100%" stopColor="#22d3ee" />
            </linearGradient>
          </defs>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--color-line)"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference - dash}`}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="tabular font-semibold leading-none text-ink"
            style={{ fontSize: size * 0.3 }}
          >
            {Math.round(clamped)}
          </span>
          <span className="mt-1 text-[10px] uppercase tracking-[0.12em] text-ink-faint">
            / 100
          </span>
        </div>
      </div>
      <div className="mt-2 text-center">
        <div className="text-[12px] font-medium text-ink-secondary">{label}</div>
        {caption ? <div className="mt-0.5 text-[11px] text-ink-faint">{caption}</div> : null}
      </div>
    </div>
  );
}
