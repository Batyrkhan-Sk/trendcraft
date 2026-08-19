import Link from "next/link";
import { ArrowRight, Bookmark, Compass, Wand2 } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { TrendCard, TrendRow } from "@/components/trends/trend-card";
import { Button, Card, EmptyState, SectionLabel } from "@/components/ui/primitives";
import { ScenarioMiniCard } from "@/components/scenarios/scenario-card";
import { getDashboard } from "@/lib/api";
import { compact } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const data = await getDashboard();
  const { stats } = data;
  const hasData = data.best_opportunities.length > 0;

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Overview"
        title={<span className="gradient-text">Your Content Intelligence</span>}
        description="What is emerging right now, which formats are worth your time, and what to shoot next."
        actions={
          <>
            <Link href="/discover">
              <Button variant="secondary">
                <Compass className="size-4" /> Discover
              </Button>
            </Link>
            <Link href="/scenarios">
              <Button variant="primary">
                <Wand2 className="size-4" /> Generate scenarios
              </Button>
            </Link>
          </>
        }
      />

      {!hasData ? (
        <div className="mt-8">
          <EmptyState
            icon={Compass}
            title="No trends computed yet"
            description="Run the pipeline to collect videos, analyse them and cluster them into formats. Until then there is nothing to rank."
            action={
              <Link href="/onboarding">
                <Button variant="primary">Set up your profile</Button>
              </Link>
            }
          />
        </div>
      ) : (
        <>
          {/* One strip rather than four cards: these four numbers are read
              together, and three extra borders only chop that reading up. */}
          <Card className="mt-6 grid grid-cols-2 gap-px overflow-hidden bg-line-soft lg:grid-cols-4">
            <StatTile
              label="Tracked formats"
              value={compact(stats.tracked_trends)}
              sub={`${stats.rising_count} still rising`}
            />
            <StatTile
              label="Videos analysed"
              value={compact(stats.videos_analyzed)}
              sub="across all platforms"
            />
            <StatTile
              label="Creators tracked"
              value={compact(stats.creators_tracked)}
              sub="distinct accounts"
            />
            <StatTile
              label="Avg opportunity"
              value={`${stats.avg_opportunity}`}
              sub="across tracked formats"
            />
          </Card>

          {!stats.profile_complete ? (
            <Card className="mt-4 flex flex-wrap items-center justify-between gap-3 border-brand-line bg-brand-soft p-4">
              <div>
                <div className="text-[13px] font-semibold text-ink">Finish onboarding</div>
                <p className="mt-0.5 text-[12.5px] text-ink-secondary">
                  Tell us your niche and platforms and the feed reorders around what you actually make.
                </p>
              </div>
              <Link href="/onboarding">
                <Button variant="primary" size="sm">
                  Set up profile <ArrowRight className="size-3.5" />
                </Button>
              </Link>
            </Card>
          ) : null}

          <Rail
            title="Rising fast"
            hint="Highest 7-day adoption growth"
            href="/rising"
            trends={data.rising_fast}
          />
          <Rail
            title="Best opportunities"
            hint="Growth and low competition, weighted against production effort"
            href="/discover?sort=opportunity"
            trends={data.best_opportunities}
          />
          <Rail
            title="Trending in your niche"
            hint="Ranked for your profile"
            href="/discover"
            trends={data.in_your_niche}
            showRelevance
          />

          <div className="mt-8 grid gap-5 lg:grid-cols-[1.35fr_1fr]">
            <section>
              <div className="mb-3 flex items-baseline justify-between">
                <SectionLabel>Cross-platform formats</SectionLabel>
                <span className="text-[11px] text-ink-faint">
                  Working on two or more platforms at once
                </span>
              </div>
              <Card className="p-1.5">
                {data.cross_platform.length ? (
                  data.cross_platform.map((t, i) => <TrendRow key={t.id} trend={t} rank={i + 1} />)
                ) : (
                  <p className="px-3 py-6 text-[13px] text-ink-faint">
                    No format has crossed platforms yet.
                  </p>
                )}
              </Card>
            </section>

            <section>
              <div className="mb-3 flex items-baseline justify-between">
                <SectionLabel>Recommended scenarios</SectionLabel>
                <Link href="/scenarios" className="text-[11px] text-[#a99bff] hover:underline">
                  All scenarios
                </Link>
              </div>
              {data.recommended_scenarios.length ? (
                <div className="flex flex-col gap-2">
                  {data.recommended_scenarios.map((s) => (
                    <ScenarioMiniCard key={s.id} scenario={s} />
                  ))}
                </div>
              ) : (
                <Card className="p-5">
                  <p className="text-[13px] leading-relaxed text-ink-secondary">
                    You have not generated any scenarios yet. Pick a trend and hit Recreate, or
                    generate a batch for your niche.
                  </p>
                  <Link href="/scenarios" className="mt-3 inline-block">
                    <Button variant="primary" size="sm">
                      <Wand2 className="size-3.5" /> Generate
                    </Button>
                  </Link>
                </Card>
              )}
            </section>
          </div>

          <section className="mt-8">
            <div className="mb-3 flex items-baseline justify-between">
              <SectionLabel>Recently saved</SectionLabel>
              <Link href="/saved" className="text-[11px] text-[#a99bff] hover:underline">
                Open saved
              </Link>
            </div>
            {data.recently_saved.length ? (
              <Card className="p-1.5">
                {data.recently_saved.map((item) =>
                  item.trend ? (
                    <TrendRow key={item.id} trend={item.trend} />
                  ) : item.scenario ? (
                    <Link
                      key={item.id}
                      href={`/scenarios/${item.scenario.id}`}
                      className="flex items-center gap-3 rounded-lg px-2.5 py-2.5 hover:bg-surface-2"
                    >
                      <Wand2 className="size-4 shrink-0 text-ink-muted" />
                      <span className="truncate text-[13px] text-ink">{item.scenario.title}</span>
                    </Link>
                  ) : null,
                )}
              </Card>
            ) : (
              <Card className="flex items-center gap-3 p-4">
                <Bookmark className="size-4 text-ink-muted" />
                <p className="text-[13px] text-ink-secondary">
                  Nothing saved yet. Bookmark a trend and it lands here.
                </p>
              </Card>
            )}
          </section>
        </>
      )}
    </PageShell>
  );
}

function StatTile({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="bg-surface p-4">
      <div className="text-[11px] uppercase tracking-[0.08em] text-ink-muted">{label}</div>
      <div className="tabular mt-2 text-[24px] font-semibold leading-none tracking-tight text-ink">
        {value}
      </div>
      <div className="mt-1.5 text-[11.5px] text-ink-faint">{sub}</div>
    </div>
  );
}

function Rail({
  title,
  hint,
  href,
  trends,
  showRelevance,
}: {
  title: string;
  hint: string;
  href: string;
  trends: Awaited<ReturnType<typeof getDashboard>>["rising_fast"];
  showRelevance?: boolean;
}) {
  if (!trends.length) return null;
  return (
    <section className="mt-8">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-3">
          <SectionLabel>{title}</SectionLabel>
          <span className="text-[11px] text-ink-faint">{hint}</span>
        </div>
        <Link href={href} className="text-[11px] text-[#a99bff] hover:underline">
          View all
        </Link>
      </div>
      {/* Horizontal rail on narrow viewports, grid once there is room. */}
      <div className="rail -mx-1 flex gap-3 overflow-x-auto px-1 pb-1 xl:grid xl:grid-cols-3 xl:overflow-visible">
        {trends.slice(0, 3).map((t) => (
          <div key={t.id} className="w-[320px] shrink-0 xl:w-auto">
            <TrendCard trend={t} showRelevance={showRelevance} />
          </div>
        ))}
      </div>
    </section>
  );
}
