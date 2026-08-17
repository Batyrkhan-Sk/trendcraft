import { TrendingUp } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { TrendCard } from "@/components/trends/trend-card";
import { EmptyState } from "@/components/ui/primitives";
import { getTrends } from "@/lib/api";

export const metadata = { title: "Rising" };
export const dynamic = "force-dynamic";

export default async function RisingPage() {
  // The inverse of Trending: formats with real acceleration and a base small
  // enough that entering now still means arriving early.
  const data = await getTrends("?status=emerging,growing&min_growth=0&sort=growth_7d&limit=48");

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Rising"
        title="Accelerating right now"
        description="Formats gaining creators week over week, ordered by adoption growth. These are the ones where arriving early still counts for something."
      />

      {data.items.length ? (
        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {data.items.map((trend) => (
            <TrendCard key={trend.id} trend={trend} />
          ))}
        </div>
      ) : (
        <div className="mt-6">
          <EmptyState
            icon={TrendingUp}
            title="Nothing accelerating"
            description="No tracked format is currently gaining creators. That usually means the corpus needs a fresh collection run."
          />
        </div>
      )}
    </PageShell>
  );
}
