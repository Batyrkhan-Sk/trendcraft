import { Suspense } from "react";
import { SearchX } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { TrendCard } from "@/components/trends/trend-card";
import { TrendFilters } from "@/components/trends/trend-filters";
import { EmptyState } from "@/components/ui/primitives";
import { getTrends } from "@/lib/api";

export const metadata = { title: "Discover" };
export const dynamic = "force-dynamic";

/** Query keys forwarded verbatim to the API. */
const PASSTHROUGH = [
  "platform",
  "niche",
  "country",
  "language",
  "content_type",
  "status",
  "competition",
  "difficulty",
  "min_growth",
  "min_engagement",
  "min_duration",
  "max_duration",
  "since_days",
  "q",
  "sort",
];

export function buildQuery(
  searchParams: Record<string, string | string[] | undefined>,
  defaults: Record<string, string> = {},
): string {
  const query = new URLSearchParams(defaults);
  for (const key of PASSTHROUGH) {
    const value = searchParams[key];
    if (typeof value === "string" && value !== "") query.set(key, value);
  }
  return `?${query.toString()}`;
}

export default async function DiscoverPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const data = await getTrends(buildQuery(params, { limit: "48" }));

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Discover"
        title="Emerging content formats"
        description="Every format the engine is tracking, ranked by opportunity rather than by raw view count."
        actions={
          <span className="tabular text-[12.5px] text-ink-muted">
            {data.total} {data.total === 1 ? "format" : "formats"}
          </span>
        }
      />

      <div className="mt-5">
        <Suspense fallback={<div className="h-9" />}>
          <TrendFilters facets={data.facets} />
        </Suspense>
      </div>

      {data.items.length ? (
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {data.items.map((trend) => (
            <TrendCard key={trend.id} trend={trend} />
          ))}
        </div>
      ) : (
        <div className="mt-6">
          <EmptyState
            icon={SearchX}
            title="No formats match those filters"
            description="Widen the growth or engagement threshold, or clear a filter or two. If the whole catalogue is empty, the pipeline has not produced trends yet."
          />
        </div>
      )}
    </PageShell>
  );
}
