"use client";

import { BarList, type BarDatum } from "@/components/charts/bar-list";
import { Card, SectionLabel } from "@/components/ui/primitives";
import type { ScoreBreakdown as Breakdown } from "@/lib/types";

/**
 * Renders the score as its parts.
 *
 * The product's credibility rests on the number being explicable, so every
 * component's normalised value, weight and resulting contribution is shown
 * rather than summarised. Bars are sized by contribution — the thing that
 * actually moved the total — with the raw signal value in the hover detail.
 */
export function ScoreBreakdownPanel({ breakdown }: { breakdown: Breakdown }) {
  const trend = breakdown.trend_score;
  const opportunity = breakdown.opportunity_score;
  if (!trend && !opportunity) return null;

  const toData = (components: NonNullable<typeof trend>["components"]): BarDatum[] =>
    components.map((c) => ({
      label: c.label,
      value: c.contribution,
      display: c.contribution.toFixed(1),
      detail: `Signal ${(c.value * 100).toFixed(0)}/100 × weight ${(c.weight * 100).toFixed(0)}% = ${c.contribution.toFixed(1)} points`,
    }));

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {trend ? (
        <Card className="p-4">
          <div className="flex items-baseline justify-between">
            <SectionLabel>Trend score</SectionLabel>
            <span className="tabular text-[15px] font-semibold text-ink">
              {trend.total.toFixed(1)}
            </span>
          </div>
          <p className="mt-1.5 text-[11.5px] leading-relaxed text-ink-faint">
            Points contributed by each signal. Hover a row for the raw value and weight.
          </p>
          <BarList className="mt-3.5" data={toData(trend.components)} />
        </Card>
      ) : null}

      {opportunity ? (
        <Card className="p-4">
          <div className="flex items-baseline justify-between">
            <SectionLabel>Opportunity score</SectionLabel>
            <span className="tabular text-[15px] font-semibold text-ink">
              {opportunity.total.toFixed(1)}
            </span>
          </div>
          <p className="mt-1.5 text-[11.5px] leading-relaxed text-ink-faint">
            Weighted toward growth and low competition, discounted by production effort.
          </p>
          <BarList
            className="mt-3.5"
            data={toData(opportunity.components)}
            barColor="var(--color-series-3)"
          />
        </Card>
      ) : null}
    </div>
  );
}

/** Raw measured inputs, shown as a definition grid beneath the bars. */
export function ScoreInputs({ inputs }: { inputs: Record<string, number> }) {
  const rows: [string, string][] = [
    ["Adoption growth (7d)", `${(inputs.growth_7d_pct ?? 0).toFixed(0)}%`],
    ["Velocity change (24h)", `${(inputs.growth_24h_pct ?? 0).toFixed(0)}%`],
    ["Median views/hour", `${Math.round(inputs.median_velocity_per_hour ?? 0).toLocaleString()}`],
    ["Creator-normalised lift", `${(inputs.median_creator_lift ?? 0).toFixed(2)}×`],
    ["Distinct creators", `${inputs.creator_count ?? 0}`],
    ["Videos in cluster", `${inputs.video_count ?? 0}`],
    [
      "Engagement vs baseline",
      `${((inputs.avg_engagement_rate ?? 0) * 100).toFixed(1)}% vs ${((inputs.engagement_baseline ?? 0) * 100).toFixed(1)}%`,
    ],
    ["Saturation", `${((inputs.saturation ?? 0) * 100).toFixed(0)}/100`],
    ["Median age", `${Math.round((inputs.median_age_hours ?? 0) / 24)}d`],
  ];

  return (
    <dl className="grid grid-cols-2 gap-x-6 gap-y-2.5 sm:grid-cols-3">
      {rows.map(([label, value]) => (
        <div key={label} className="min-w-0 border-b border-line-soft pb-2">
          <dt className="truncate text-[11px] uppercase tracking-[0.06em] text-ink-muted">
            {label}
          </dt>
          <dd className="tabular mt-0.5 truncate text-[13px] font-medium text-ink">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
