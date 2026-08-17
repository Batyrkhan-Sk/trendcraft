"use client";

import { useMemo, useRef, useState } from "react";
import { cn, compact } from "@/lib/format";

export interface Series {
  key: string;
  label: string;
  color: string;
  values: number[];
}

/**
 * Multi-series time chart with a crosshair and tooltip.
 *
 * One y-axis only. Where two measures of different magnitude need to appear
 * together (videos vs creators), they are plotted on a shared scale rather than
 * a second axis — a dual-axis chart lets the author manufacture any correlation
 * they like, which is exactly what an intelligence product must not do.
 */
/**
 * Axis formatting is chosen by name rather than by callback: this is a client
 * component, and React cannot serialise a function prop across the server
 * boundary. A token keeps every caller a server component.
 */
export type ValueFormat = "compact" | "integer" | "percent";

const FORMATTERS: Record<ValueFormat, (n: number) => string> = {
  compact,
  integer: (n) => `${Math.round(n)}`,
  percent: (n) => `${(n * 100).toFixed(0)}%`,
};

export function AreaChart({
  labels,
  series,
  height = 200,
  className,
  format = "compact",
  yLabel,
}: {
  labels: string[];
  series: Series[];
  height?: number;
  className?: string;
  format?: ValueFormat;
  yLabel?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<number | null>(null);
  const valueFormat = FORMATTERS[format];

  const { max, ticks } = useMemo(() => {
    const all = series.flatMap((s) => s.values);
    const rawMax = Math.max(...all, 1);
    // Round the ceiling up to a readable step so gridlines land on round numbers.
    const magnitude = 10 ** Math.floor(Math.log10(rawMax));
    const ceil = Math.ceil(rawMax / magnitude) * magnitude;
    return { max: ceil, ticks: [0, ceil / 2, ceil] };
  }, [series]);

  if (!labels.length || !series.length) {
    return (
      <div className={cn("grid place-items-center text-[13px] text-ink-faint", className)} style={{ height }}>
        Not enough history yet
      </div>
    );
  }

  const padL = 40;
  const padR = 8;
  const padT = 10;
  const padB = 22;
  const vw = 640;
  const plotW = vw - padL - padR;
  const plotH = height - padT - padB;

  const x = (i: number) => padL + (labels.length === 1 ? plotW / 2 : (i / (labels.length - 1)) * plotW);
  const y = (v: number) => padT + plotH - (v / max) * plotH;

  const onMove = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const rel = ((e.clientX - rect.left) / rect.width) * vw;
    const idx = Math.round(((rel - padL) / plotW) * (labels.length - 1));
    setHover(Math.max(0, Math.min(labels.length - 1, idx)));
  };

  // Show at most six x labels regardless of range length.
  const labelStep = Math.max(1, Math.ceil(labels.length / 6));

  return (
    <div className={className}>
      <div
        ref={ref}
        className="relative"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        <svg viewBox={`0 0 ${vw} ${height}`} className="w-full" style={{ height }} role="img"
             aria-label={`${series.map((s) => s.label).join(" and ")} over time`}>
          <defs>
            {series.map((s) => (
              <linearGradient key={s.key} id={`area-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity="0.22" />
                <stop offset="100%" stopColor={s.color} stopOpacity="0" />
              </linearGradient>
            ))}
          </defs>

          {ticks.map((t) => (
            <g key={t}>
              <line
                x1={padL}
                x2={vw - padR}
                y1={y(t)}
                y2={y(t)}
                stroke="var(--color-grid)"
                strokeWidth="1"
              />
              <text
                x={padL - 8}
                y={y(t) + 3.5}
                textAnchor="end"
                className="tabular"
                fontSize="10"
                fill="var(--color-ink-faint)"
              >
                {valueFormat(t)}
              </text>
            </g>
          ))}

          {series.map((s) => {
            const line = s.values
              .map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
              .join(" ");
            const area = `${line} L${x(s.values.length - 1).toFixed(1)},${y(0)} L${x(0).toFixed(1)},${y(0)} Z`;
            return (
              <g key={s.key}>
                <path d={area} fill={`url(#area-${s.key})`} />
                <path d={line} fill="none" stroke={s.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
              </g>
            );
          })}

          {labels.map((l, i) =>
            i % labelStep === 0 ? (
              <text
                key={l + i}
                x={x(i)}
                y={height - 6}
                textAnchor="middle"
                fontSize="10"
                fill="var(--color-ink-faint)"
              >
                {l}
              </text>
            ) : null,
          )}

          {hover !== null ? (
            <g>
              <line
                x1={x(hover)}
                x2={x(hover)}
                y1={padT}
                y2={padT + plotH}
                stroke="var(--color-line-strong)"
                strokeWidth="1"
              />
              {series.map((s) => (
                <circle
                  key={s.key}
                  cx={x(hover)}
                  cy={y(s.values[hover] ?? 0)}
                  r="4"
                  fill={s.color}
                  stroke="var(--color-surface)"
                  strokeWidth="2"
                />
              ))}
            </g>
          ) : null}
        </svg>

        {hover !== null ? (
          <div
            className="pointer-events-none absolute top-2 z-10 min-w-36 rounded-lg border border-line-strong bg-surface-2 px-2.5 py-2 shadow-xl"
            style={{
              left: `${(x(hover) / vw) * 100}%`,
              transform: `translateX(${hover > labels.length / 2 ? "-108%" : "8px"})`,
            }}
          >
            <div className="text-[11px] text-ink-muted">{labels[hover]}</div>
            {series.map((s) => (
              <div key={s.key} className="mt-1 flex items-center justify-between gap-4">
                <span className="flex items-center gap-1.5 text-[11.5px] text-ink-secondary">
                  <span className="size-2 rounded-full" style={{ background: s.color }} />
                  {s.label}
                </span>
                <span className="tabular text-[11.5px] font-medium text-ink">
                  {valueFormat(s.values[hover] ?? 0)}
                </span>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="mt-2 flex items-center gap-4">
        {/* Legend is always present for two or more series so identity is never colour-alone. */}
        {series.length > 1
          ? series.map((s) => (
              <span key={s.key} className="flex items-center gap-1.5 text-[11.5px] text-ink-muted">
                <span className="size-2 rounded-full" style={{ background: s.color }} />
                {s.label}
              </span>
            ))
          : null}
        {yLabel ? <span className="ml-auto text-[11px] text-ink-faint">{yLabel}</span> : null}
      </div>
    </div>
  );
}
