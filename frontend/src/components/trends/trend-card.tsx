import Link from "next/link";
import { Sparkline } from "@/components/charts/sparkline";
import { Card } from "@/components/ui/primitives";
import { GrowthDelta, StatusPill } from "@/components/trends/status-pill";
import { VideoEmbed } from "@/components/trends/video-embed";
import { compact, duration, percent } from "@/lib/format";
import { STATUS_META, platformLabel } from "@/lib/meta";
import type { TrendSummary } from "@/lib/types";

/**
 * Which of the card's own labels the surrounding page has already established.
 *
 * A filtered grid repeats its own filter on every card — twenty "YouTube" chips
 * under a YouTube filter carry no information and cost the eye a fixation each.
 * Pages that pin a facet declare it here and the card drops that label.
 */
export interface TrendCardContext {
  status?: boolean;
  platform?: boolean;
}

export function TrendCard({
  trend,
  showRelevance,
  implied,
}: {
  trend: TrendSummary;
  showRelevance?: boolean;
  implied?: TrendCardContext;
}) {
  const meta = STATUS_META[trend.status];
  const showStatus = !implied?.status;
  const platforms = implied?.platform ? [] : trend.platforms.slice(0, 3);
  const pattern = distinctPattern(trend.name, trend.format_pattern);
  const summary = trimLeadingName(trend.summary, trend.name);
  // A flat day is the common case; printing "+0% in 24h" under every card turns
  // the absence of news into a line of text.
  const hasDayMove = Math.abs(trend.growth_24h) >= 0.005;

  return (
    <Card hover className="group relative flex h-full flex-col overflow-hidden">
      {/* The link covers the informational body only. The examples strip sits
          outside it so its play buttons are not swallowed by navigation. */}
      <Link href={`/trends/${trend.slug}`} className="flex flex-1 flex-col p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2 text-[11px]">
            {showStatus ? <StatusPill status={trend.status} size="sm" variant="bare" /> : null}
            {showStatus && platforms.length ? <span className="text-ink-faint">·</span> : null}
            {platforms.length ? (
              <span className="truncate text-ink-muted">
                {platforms.map(platformLabel).join(" · ")}
              </span>
            ) : null}
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

        <h3 className="mt-2.5 text-[15px] font-semibold leading-snug tracking-tight text-ink">
          {trend.name}
        </h3>
        {pattern ? (
          <p className="mt-1 truncate font-mono text-[11.5px] text-[#a99bff]">{pattern}</p>
        ) : null}
        <p className="mt-1.5 line-clamp-2 text-[12.5px] leading-relaxed text-ink-secondary">
          {summary}
        </p>

        {/* Growth is the headline; the sparkline shows shape, the number shows size. */}
        <div className="mt-3 flex items-center justify-between gap-3">
          <div className="flex flex-col gap-0.5">
            <GrowthDelta value={trend.growth_7d} suffix="7d" />
            {hasDayMove ? (
              <span className="tabular text-[11px] text-ink-faint">
                {trend.growth_24h >= 0 ? "+" : ""}
                {(trend.growth_24h * 100).toFixed(0)}% in 24h
              </span>
            ) : null}
          </div>
          <Sparkline
            values={trend.sparkline}
            color={meta.color}
            label={`Adoption for ${trend.name}`}
          />
        </div>

        <div className="mt-3 grid grid-cols-4 gap-2 border-t border-line-soft pt-3">
          <Metric label="Videos" value={compact(trend.video_count)} />
          <Metric label="Creators" value={compact(trend.creator_count)} />
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
          buttons are not swallowed by the card's navigation. No caption: three
          vertical frames with play buttons do not need to be called examples. */}
      {trend.exemplars.length ? (
        <div className="grid grid-cols-3 gap-px border-t border-line-soft bg-line-soft">
          {trend.exemplars.slice(0, 3).map((video) => (
            <VideoEmbed
              key={video.id}
              video={video}
              showStats={false}
              size="sm"
              // Shallower than the 9:16 of the source clip: this is a teaser
              // rail, and full-height frames would outweigh the card's numbers.
              className="aspect-[4/5]"
            />
          ))}
        </div>
      ) : null}
    </Card>
  );
}

/**
 * The clustering step frequently names a format after its own pattern string.
 * When the two only differ in punctuation, the mono line is the title again in
 * a second typeface.
 */
function distinctPattern(name: string, pattern: string | null): string | null {
  if (!pattern) return null;
  const norm = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  return norm(pattern) === norm(name) ? null : pattern;
}

/** Generated summaries usually open by restating the name printed above them. */
function trimLeadingName(summary: string, name: string): string {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const trimmed = summary.replace(new RegExp(`^${escaped}[\\s,:—-]*`, "i"), "");
  if (!trimmed || trimmed === summary) return summary;
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <div className="truncate text-[10px] uppercase tracking-[0.06em] text-ink-faint">{label}</div>
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
          <StatusPill status={trend.status} size="sm" variant="bare" />
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
