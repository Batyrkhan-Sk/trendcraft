import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Clapperboard,
  Clock,
  Gauge,
  Info,
  Layers,
  Users,
  Video as VideoIcon,
} from "lucide-react";
import { AreaChart } from "@/components/charts/area-chart";
import { ScoreRing } from "@/components/charts/score-ring";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { FormatTimeline } from "@/components/trends/format-timeline";
import { SaveButton } from "@/components/trends/save-button";
import { ScoreBreakdownPanel, ScoreInputs } from "@/components/trends/score-breakdown";
import { GrowthDelta, LevelMeter, StatusPill } from "@/components/trends/status-pill";
import { VideoCard } from "@/components/trends/video-card";
import { Badge, Button, Card, Divider, SectionLabel, Stat } from "@/components/ui/primitives";
import { ApiError, getTrend } from "@/lib/api";
import { compact, duration, percent, relativeTime } from "@/lib/format";
import { STATUS_META, platformLabel } from "@/lib/meta";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const trend = await getTrend(slug);
    return { title: trend.name };
  } catch {
    return { title: "Trend" };
  }
}

export default async function TrendPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let trend;
  try {
    trend = await getTrend(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const meta = STATUS_META[trend.status];
  const snapshots = trend.snapshots.slice(-14);

  return (
    <PageShell wide>
      <Link
        href="/discover"
        className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted transition-colors hover:text-ink"
      >
        <ArrowLeft className="size-3.5" /> Discover
      </Link>

      <div className="mt-4">
        <PageHeader
          eyebrow={trend.niches.slice(0, 3).join(" · ") || "Format"}
          title={trend.name}
          description={trend.summary}
          actions={
            <>
              <SaveButton entityType="trend" entityId={trend.id} />
              <Link href={`/trends/${trend.slug}/recreate`}>
                <Button variant="primary">
                  <Clapperboard className="size-4" /> Recreate
                </Button>
              </Link>
            </>
          }
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <StatusPill status={trend.status} />
        {trend.platforms.map((p) => (
          <Badge key={p} tone="outline">
            {platformLabel(p)}
          </Badge>
        ))}
        {trend.format_pattern ? (
          <span className="rounded-md border border-brand-line bg-brand-soft px-2 py-1 font-mono text-[11.5px] text-[#c3b5ff]">
            {trend.format_pattern}
          </span>
        ) : null}
        <span className="ml-auto text-[11px] text-ink-faint">
          Recomputed {relativeTime(trend.last_computed_at)}
        </span>
      </div>

      {/* --- headline metrics + opportunity --- */}
      <div className="mt-5 grid gap-3 lg:grid-cols-[1fr_300px]">
        <Card className="p-4">
          <div className="grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-3 lg:grid-cols-6">
            <Stat label="Videos" value={compact(trend.video_count)} sub="in cluster" />
            <Stat label="Creators" value={compact(trend.creator_count)} sub="distinct" />
            <Stat label="Avg views" value={compact(trend.avg_views)} sub={`${compact(trend.median_views)} median`} />
            <Stat label="Engagement" value={percent(trend.avg_engagement_rate, 1)} sub="likes+comments+shares" />
            <Stat
              label="Creator lift"
              value={`${trend.creator_normalized_lift.toFixed(2)}×`}
              sub="vs creator's own average"
            />
            <Stat label="Median length" value={duration(trend.median_duration_sec)} sub="per video" />
          </div>

          <Divider className="my-4" />

          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.08em] text-ink-muted">
                Adoption growth (7d)
              </div>
              <GrowthDelta value={trend.growth_7d} className="mt-1 text-[16px]" />
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-[0.08em] text-ink-muted">
                View momentum (24h)
              </div>
              <GrowthDelta value={trend.growth_24h} className="mt-1 text-[16px]" />
            </div>
            <div className="min-w-[180px] flex-1">
              <LevelMeter level={trend.competition_level} label="Competition" inverse />
              <LevelMeter level={trend.production_difficulty} label="Production effort" inverse className="mt-1.5" />
              <LevelMeter level={trend.adaptability} label="Adaptability" className="mt-1.5" />
            </div>
          </div>
        </Card>

        <Card className="flex flex-col items-center justify-center p-4">
          <ScoreRing
            value={trend.opportunity_score}
            caption={`Trend score ${trend.trend_score.toFixed(0)}`}
          />
          <div
            className="mt-3 w-full rounded-lg border px-2.5 py-2 text-[11.5px] leading-relaxed"
            style={{ borderColor: meta.ring, background: meta.tint, color: "var(--color-ink-secondary)" }}
          >
            {meta.blurb}
          </div>
        </Card>
      </div>

      {/* --- why the score is what it is --- */}
      {trend.opportunity_explanation.length ? (
        <Card className="mt-3 p-4">
          <div className="flex items-center gap-2">
            <Info className="size-3.5 text-ink-muted" />
            <SectionLabel>Why this score</SectionLabel>
          </div>
          <ul className="mt-2.5 flex flex-col gap-1.5">
            {trend.opportunity_explanation.map((reason) => (
              <li key={reason} className="flex gap-2 text-[13px] leading-relaxed text-ink-secondary">
                <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-ink-faint" />
                {reason}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {/* --- why it works --- */}
      <section className="mt-8">
        <SectionLabel>Why it works</SectionLabel>
        <p className="mt-1 text-[12.5px] text-ink-faint">
          The mechanisms that make this structure perform, not a description of the topic.
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {trend.why_it_works.map((item, i) => (
            <Card key={item.principle} className="p-4">
              <div className="flex items-start gap-2.5">
                <span className="tabular mt-0.5 grid size-6 shrink-0 place-items-center rounded-md bg-brand-soft text-[11px] font-semibold text-[#c3b5ff]">
                  {i + 1}
                </span>
                <div className="min-w-0">
                  <h3 className="text-[13.5px] font-semibold leading-snug text-ink">{item.title}</h3>
                  <p className="mt-1 text-[12.5px] leading-relaxed text-ink-secondary">
                    {item.detail}
                  </p>
                  <div className="mt-2 font-mono text-[10.5px] text-ink-faint">{item.principle}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* --- structure + shared elements --- */}
      <section className="mt-8 grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <div>
          <SectionLabel>Format structure</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Typical beat timing across the {trend.video_count} videos in this cluster.
          </p>
          <div className="mt-3">
            <FormatTimeline segments={trend.format_structure} />
          </div>
        </div>

        <div>
          <SectionLabel>Shared elements</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            What every video in the cluster has in common.
          </p>
          <Card className="mt-3 p-4">
            <ul className="flex flex-col gap-2.5">
              {trend.common_elements.map((element) => (
                <li key={element} className="flex gap-2.5 text-[12.5px] leading-relaxed text-ink-secondary">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-line-strong" aria-hidden />
                  {element}
                </li>
              ))}
            </ul>
            <Divider className="my-3.5" />
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Niches" value={trend.niches.length} sub={trend.niches.slice(0, 3).join(", ")} />
              <Stat
                label="Languages"
                value={trend.languages.length}
                sub={trend.languages.join(", ").toUpperCase()}
              />
            </div>
          </Card>
        </div>
      </section>

      {/* --- adoption history --- */}
      {snapshots.length > 1 ? (
        <section className="mt-8">
          <SectionLabel>Adoption over time</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Videos and distinct creators using the format, by day.
          </p>
          <Card className="mt-3 p-4">
            <AreaChart
              labels={snapshots.map((s) =>
                new Date(s.captured_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                }),
              )}
              series={[
                {
                  key: "videos",
                  label: "Videos",
                  color: "var(--color-series-1)",
                  values: snapshots.map((s) => s.video_count),
                },
                {
                  key: "creators",
                  label: "Creators",
                  color: "var(--color-series-2)",
                  values: snapshots.map((s) => s.creator_count),
                },
              ]}
              format="integer"
            />
          </Card>
        </section>
      ) : null}

      {/* --- score transparency --- */}
      <section className="mt-8">
        <SectionLabel>How the score was calculated</SectionLabel>
        <p className="mt-1 text-[12.5px] text-ink-faint">
          Every signal, its weight, and the points it contributed.
        </p>
        <div className="mt-3">
          <ScoreBreakdownPanel breakdown={trend.score_breakdown} />
        </div>
        {trend.score_breakdown.inputs ? (
          <Card className="mt-3 p-4">
            <div className="flex items-center gap-2">
              <Gauge className="size-3.5 text-ink-muted" />
              <SectionLabel>Measured inputs</SectionLabel>
            </div>
            <div className="mt-3">
              <ScoreInputs inputs={trend.score_breakdown.inputs} />
            </div>
          </Card>
        ) : null}
      </section>

      {/* --- examples --- */}
      <section className="mt-8">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <SectionLabel>Examples</SectionLabel>
            <p className="mt-1 text-[12.5px] text-ink-faint">
              Ordered by how prototypical they are for the cluster.
            </p>
          </div>
          <span className="tabular text-[11.5px] text-ink-muted">
            {trend.videos.length} of {trend.video_count} shown
          </span>
        </div>
        <div className="mt-3 grid gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
          {trend.videos.slice(0, 10).map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      </section>

      {/* --- deep dive on the single most prototypical video --- */}
      {trend.videos[0]?.analysis ? (
        <section className="mt-8">
          <SectionLabel>Anatomy of the closest example</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            What the AI extracted from @{trend.videos[0].creator?.handle}.
          </p>
          <Card className="mt-3 p-4">
            <AnalysisGrid video={trend.videos[0]} />
          </Card>
        </section>
      ) : null}

      <div className="mt-10 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-card)] border border-brand-line bg-brand-soft p-5">
        <div>
          <h3 className="text-[15px] font-semibold text-ink">Make this format yours</h3>
          <p className="mt-1 max-w-xl text-[12.5px] leading-relaxed text-ink-secondary">
            Generate a script, a shot list and a frame-by-frame recording plan adapted to your niche
            — keeping the structure, replacing every specific.
          </p>
        </div>
        <Link href={`/trends/${trend.slug}/recreate`}>
          <Button variant="primary">
            <Clapperboard className="size-4" /> Recreate this
          </Button>
        </Link>
      </div>
    </PageShell>
  );
}

function AnalysisGrid({ video }: { video: NonNullable<Awaited<ReturnType<typeof getTrend>>["videos"][number]> }) {
  const a = video.analysis!;
  const fields: [string, React.ReactNode][] = [
    ["Hook", <span key="h" className="text-ink">“{a.hook}”</span>],
    ["Opening 3–5s", a.opening_frames],
    ["Content format", a.content_format],
    ["Structure", a.narrative_structure.join(" → ")],
    ["Speaking style", a.speaking_style],
    ["Visual style", a.visual_style],
    ["Editing", a.editing_patterns.join(", ")],
    ["Captions", a.caption_style],
    ["Emotional tone", a.emotional_tone],
    ["Audio", a.audio_style],
    ["Target audience", a.target_audience],
    ["Call to action", a.call_to_action || "—"],
  ];

  return (
    <div>
      <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
        {fields.map(([label, value]) => (
          <div key={label} className="min-w-0">
            <dt className="text-[11px] uppercase tracking-[0.06em] text-ink-muted">{label}</dt>
            <dd className="mt-0.5 text-[12.5px] leading-relaxed text-ink-secondary">
              {value || "—"}
            </dd>
          </div>
        ))}
      </dl>

      {a.key_moments.length ? (
        <>
          <Divider className="my-4" />
          <div className="flex items-center gap-2">
            <Clock className="size-3.5 text-ink-muted" />
            <SectionLabel>Key moments</SectionLabel>
          </div>
          <ol className="mt-2.5 flex flex-col gap-2">
            {a.key_moments.map((m, i) => (
              <li key={i} className="flex gap-3">
                <span className="tabular mt-0.5 w-10 shrink-0 text-[11.5px] font-medium text-[#a99bff]">
                  {m.t.toFixed(1)}s
                </span>
                <div className="min-w-0">
                  <div className="text-[12.5px] font-medium text-ink">{m.label}</div>
                  <div className="text-[12px] leading-relaxed text-ink-secondary">{m.why}</div>
                </div>
              </li>
            ))}
          </ol>
        </>
      ) : null}

      <Divider className="my-4" />
      <div className="flex flex-wrap items-center gap-3 text-[11px] text-ink-faint">
        <span className="inline-flex items-center gap-1.5">
          <VideoIcon className="size-3" /> {compact(video.views)} views
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Users className="size-3" /> {compact(video.creator?.followers ?? 0)} followers
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Layers className="size-3" /> similarity {((video.similarity ?? 0) * 100).toFixed(0)}%
        </span>
        <span className="ml-auto font-mono">
          extracted by {a.extraction_model ?? "unknown"}
          {a.is_fallback ? " (metadata-only fallback)" : ""}
        </span>
      </div>
    </div>
  );
}
