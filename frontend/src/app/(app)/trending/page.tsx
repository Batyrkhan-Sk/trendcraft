import { Flame } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { TrendCard } from "@/components/trends/trend-card";
import { EmptyState } from "@/components/ui/primitives";
import { getTrends } from "@/lib/api";

export const metadata = { title: "Trending" };
export const dynamic = "force-dynamic";

export default async function TrendingPage() {
  // Peak formats: already viral or growing, ranked by the composite trend score
  // rather than by opportunity — this page answers "what is big", not "what should I make".
  const data = await getTrends("?status=viral,growing&sort=trend_score&limit=48");

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Trending"
        title="Formats at peak reach"
        description="Widely adopted formats ranked by trend score. High reach usually means high competition — check the opportunity score before committing."
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
            icon={Flame}
            title="Nothing at peak yet"
            description="No format has reached the reach and adoption thresholds for viral or growing status."
          />
        </div>
      )}
    </PageShell>
  );
}
