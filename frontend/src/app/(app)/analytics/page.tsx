import { BarChart3 } from "lucide-react";
import { AreaChart } from "@/components/charts/area-chart";
import { BarList } from "@/components/charts/bar-list";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { TrendRow } from "@/components/trends/trend-card";
import { Card, EmptyState, SectionLabel } from "@/components/ui/primitives";
import { getAnalytics } from "@/lib/api";
import { compact, titleCase } from "@/lib/format";
import { STATUS_META, platformLabel } from "@/lib/meta";
import type { TrendStatus } from "@/lib/types";

export const metadata = { title: "Analytics" };
export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const data = await getAnalytics();

  if (!data.totals.trends) {
    return (
      <PageShell>
        <PageHeader eyebrow="Analytics" title="Corpus analytics" />
        <div className="mt-6">
          <EmptyState
            icon={BarChart3}
            title="No data to analyse"
            description="The pipeline has not produced any trends yet, so there is nothing to chart."
          />
        </div>
      </PageShell>
    );
  }

  const timeline = data.adoption_timeline.slice(-30);

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Analytics"
        title="Corpus analytics"
        description="What the engine is tracking, where the coverage sits, and how opportunity is distributed."
      />

      <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label="Formats tracked" value={compact(data.totals.trends)} />
        <Tile label="Videos collected" value={compact(data.totals.videos)} />
        <Tile
          label="Videos analysed"
          value={compact(data.totals.analyzed_videos)}
          sub={`${Math.round(((data.totals.analyzed_videos ?? 0) / Math.max(1, data.totals.videos)) * 100)}% coverage`}
        />
        <Tile label="Creators tracked" value={compact(data.totals.creators)} />
      </div>

      {timeline.length > 1 ? (
        <section className="mt-8">
          <SectionLabel>Adoption across all formats</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Total videos and distinct creators per day, summed across every tracked format.
          </p>
          <Card className="mt-3 p-4">
            <AreaChart
              labels={timeline.map((d) =>
                new Date(d.date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
              )}
              series={[
                {
                  key: "videos",
                  label: "Videos",
                  color: "var(--color-series-1)",
                  values: timeline.map((d) => d.videos),
                },
                {
                  key: "creators",
                  label: "Creators",
                  color: "var(--color-series-2)",
                  values: timeline.map((d) => d.creators),
                },
              ]}
              height={240}
              format="compact"
            />
          </Card>
        </section>
      ) : null}

      <div className="mt-8 grid gap-3 lg:grid-cols-3">
        <Card className="p-4">
          <SectionLabel>Formats by platform</SectionLabel>
          <p className="mt-1 text-[11.5px] text-ink-faint">
            A format can appear on more than one platform.
          </p>
          <BarList
            className="mt-4"
            data={data.by_platform.map((p) => ({
              label: platformLabel(p.platform),
              value: p.trends,
              display: `${p.trends}`,
              detail: `${compact(p.videos)} videos collected`,
            }))}
          />
        </Card>

        <Card className="p-4">
          <SectionLabel>Lifecycle stage</SectionLabel>
          <p className="mt-1 text-[11.5px] text-ink-faint">
            Where tracked formats sit in their arc.
          </p>
          {/* Each row is direct-labelled, so the reserved status hues never carry
              the meaning on their own. */}
          <BarList
            className="mt-4"
            data={data.by_status.map((s) => ({
              label: STATUS_META[s.status as TrendStatus].label,
              value: s.count,
              display: `${s.count}`,
              color: STATUS_META[s.status as TrendStatus].color,
              detail: STATUS_META[s.status as TrendStatus].blurb,
            }))}
          />
        </Card>

        <Card className="p-4">
          <SectionLabel>Opportunity distribution</SectionLabel>
          <p className="mt-1 text-[11.5px] text-ink-faint">Formats per opportunity band.</p>
          <BarList
            className="mt-4"
            data={data.score_distribution.map((b) => ({
              label: b.bucket,
              value: b.count,
              display: `${b.count}`,
            }))}
            barColor="var(--color-series-3)"
          />
        </Card>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-[1fr_1fr]">
        <section>
          <SectionLabel>Coverage by niche</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Where the corpus is deep, and where it is thin.
          </p>
          <Card className="mt-3 p-4">
            <BarList
              data={data.by_niche.map((n) => ({
                label: titleCase(n.niche),
                value: n.trends,
                display: `${n.trends}`,
                detail: `${compact(n.videos)} videos · avg opportunity ${n.avg_opportunity}`,
              }))}
            />
          </Card>
        </section>

        <section>
          <SectionLabel>Biggest movers</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Largest 7-day change in creator adoption.
          </p>
          <Card className="mt-3 p-1.5">
            {data.top_movers.map((t, i) => (
              <TrendRow key={t.id} trend={t} rank={i + 1} />
            ))}
          </Card>
        </section>
      </div>
    </PageShell>
  );
}

function Tile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card className="p-4">
      <div className="text-[11px] uppercase tracking-[0.08em] text-ink-muted">{label}</div>
      <div className="tabular mt-2 text-[24px] font-semibold leading-none tracking-tight text-ink">
        {value}
      </div>
      {sub ? <div className="mt-1.5 text-[11.5px] text-ink-faint">{sub}</div> : null}
    </Card>
  );
}
