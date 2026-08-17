import Link from "next/link";
import { Layers, Users } from "lucide-react";
import { Sparkline } from "@/components/charts/sparkline";
import { Badge, Card } from "@/components/ui/primitives";
import { GrowthDelta, StatusPill } from "@/components/trends/status-pill";
import { VideoEmbed } from "@/components/trends/video-embed";
import { compact, duration, percent } from "@/lib/format";
import { STATUS_META, platformLabel } from "@/lib/meta";
import type { TrendSummary } from "@/lib/types";

export function TrendCard({ trend, showRelevance }: { trend: TrendSummary; showRelevance?: boolean }) {
  const meta = STATUS_META[trend.status];

  return (
    <Card hover className="group relative flex h-full flex-col overflow-hidden">
      {/* The link covers the informational body only. The examples strip sits
          outside it so its play buttons are not swallowed by navigation. */}
      <Link href={`/trends/${trend.slug}`} className="flex flex-1 flex-col p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <StatusPill status={trend.status} size="sm" />
            {trend.platforms.slice(0, 3).map((p) => (
              <Badge key={p} tone="outline">
                {platformLabel(p)}
              </Badge>
            ))}
          </div>
          <div className="shrink-0 text-right">
            <div className="tabular text-[19px] font-semibold leading-none text-ink">
              {Math.round(trend.opportunity_score)}
            </div>
            <div className="mt-1 text-[10px] uppercase tracking-[0.1em] text-ink-faint">
              Opportunity
            </div>
          </div>
        </div>

        <h3 className="mt-3 text-[15px] font-semibold leading-snug tracking-tight text-ink">
          {trend.name}
        </h3>
        {trend.format_pattern ? (
          <p className="mt-1 truncate font-mono text-[11.5px] text-[#a99bff]">
            {trend.format_pattern}
          </p>
        ) : null}
        <p className="mt-2 line-clamp-2 text-[12.5px] leading-relaxed text-ink-secondary">
          {trend.summary}
        </p>

        {/* Growth is the headline; the sparkline shows shape, the number shows size. */}
        <div className="mt-3 flex items-center justify-between gap-3">
          <div className="flex flex-col gap-0.5">
            <GrowthDelta value={trend.growth_7d} suffix="7d" />
            <span className="tabular text-[11px] text-ink-faint">
              {trend.growth_24h >= 0 ? "+" : ""}
              {(trend.growth_24h * 100).toFixed(0)}% in 24h
            </span>
          </div>
          <Sparkline
            values={trend.sparkline}
            color={meta.color}
            label={`Adoption for ${trend.name}`}
          />
        </div>

        <div className="mt-3 grid grid-cols-4 gap-2 border-t border-line-soft pt-3">
          <Metric label="Videos" value={compact(trend.video_count)} icon={<Layers className="size-3" />} />
          <Metric label="Creators" value={compact(trend.creator_count)} icon={<Users className="size-3" />} />
          <Metric label="Avg views" value={compact(trend.avg_views)} />
          <Metric label="Engage" value={percent(trend.avg_engagement_rate, 1)} />
        </div>

        <div className="mt-3 flex items-center justify-between gap-2 text-[11px] text-ink-faint">
          <span className="truncate">
            {trend.niches.slice(0, 3).join(" · ") || "—"}
          </span>
          <span className="shrink-0 tabular">{duration(trend.median_duration_sec)} median</span>
        </div>

        {showRelevance && trend.relevance_reasons?.length ? (
          <div className="mt-3 rounded-lg border border-brand-line bg-brand-soft px-2.5 py-2">
            <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#a99bff]">
              Why you
            </div>
            <p className="mt-0.5 text-[11.5px] leading-relaxed text-ink-secondary">
              {trend.relevance_reasons.join(" · ")}
            </p>
          </div>
        ) : null}
      </Link>

      {/* Real examples, playable in place. Outside the <Link> so the play
          buttons are not swallowed by the card's navigation. */}
      {trend.exemplars.length ? (
        <div className="border-t border-line-soft px-4 pb-4 pt-3">
          <div className="mb-2 flex items-baseline justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-ink-muted">
              Examples
            </span>
            <span className="text-[10.5px] text-ink-faint">tap to play</span>
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            {trend.exemplars.slice(0, 3).map((video) => (
              <VideoEmbed
                key={video.id}
                video={video}
                showStats={false}
                className="rounded-md border border-line"
              />
            ))}
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function Metric({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="min-w-0">
      <div className="flex items-center gap-1 text-[10px] uppercase tracking-[0.06em] text-ink-faint">
        {icon}
        <span className="truncate">{label}</span>
      </div>
      <div className="tabular mt-0.5 truncate text-[13px] font-semibold text-ink">{value}</div>
    </div>
  );
}

/** Dense single-line variant used inside rails and the saved list. */
export function TrendRow({ trend, rank }: { trend: TrendSummary; rank?: number }) {
  return (
    <Link
      href={`/trends/${trend.slug}`}
      className="flex items-center gap-3 rounded-lg px-2.5 py-2.5 transition-colors hover:bg-surface-2"
    >
      {rank !== undefined ? (
        <span className="tabular w-5 shrink-0 text-[12px] text-ink-faint">{rank}</span>
      ) : null}
      <div className="min-w-0 flex-1">
        <div className="truncate text-[13px] font-medium text-ink">{trend.name}</div>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-ink-faint">
          <StatusPill status={trend.status} size="sm" />
          <span className="truncate">{trend.niches.slice(0, 2).join(" · ")}</span>
        </div>
      </div>
      <GrowthDelta value={trend.growth_7d} className="shrink-0" />
      <span className="tabular w-8 shrink-0 text-right text-[13px] font-semibold text-ink">
        {Math.round(trend.opportunity_score)}
      </span>
    </Link>
  );
}
