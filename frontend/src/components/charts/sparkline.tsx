import { cn } from "@/lib/format";

/**
 * Adoption micro-chart for trend cards.
 *
 * Deliberately axis-free and label-free: it answers "which way and how steeply",
 * and the precise number always sits next to it as text. Values arrive
 * pre-normalised to 0–1 from the API.
 */
export function Sparkline({
  values,
  color = "var(--color-series-1)",
  className,
  width = 96,
  height = 28,
  label,
}: {
  values: number[];
  color?: string;
  className?: string;
  width?: number;
  height?: number;
  label?: string;
}) {
  if (!values || values.length < 2) {
    return <div className={cn("h-7 w-24", className)} aria-hidden />;
  }

  const pad = 2;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const max = Math.max(...values, 0.0001);
  const min = Math.min(...values);
  const span = Math.max(max - min, 0.0001);

  const points = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * w;
    const y = pad + h - ((v - min) / span) * h;
    return [x, y] as const;
  });

  const line = points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} L${points[points.length - 1][0].toFixed(1)},${height} L${points[0][0].toFixed(1)},${height} Z`;
  const gradientId = `spark-${Math.round(points[0][1] * 1000)}-${values.length}`;
  const [lastX, lastY] = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={cn("overflow-visible", className)}
      role="img"
      aria-label={label ?? "Adoption trend over the last 14 days"}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.28" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Terminal marker carries a 2px surface ring so it stays legible over the fill. */}
      <circle cx={lastX} cy={lastY} r="2.75" fill={color} stroke="var(--color-surface)" strokeWidth="2" />
    </svg>
  );
}
