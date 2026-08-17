import Link from "next/link";
import { Wand2 } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { ScenarioGenerator } from "@/components/scenarios/scenario-generator";
import { ScenarioMiniCard } from "@/components/scenarios/scenario-card";
import { Card, SectionLabel } from "@/components/ui/primitives";
import { getProfile, getScenarios, getTrends } from "@/lib/api";

export const metadata = { title: "Scenarios" };
export const dynamic = "force-dynamic";

export default async function ScenariosPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const trendId = typeof params.trend === "string" ? params.trend : undefined;

  const [trends, existing, profile] = await Promise.all([
    getTrends("?limit=60&sort=opportunity"),
    getScenarios("?limit=24"),
    getProfile(),
  ]);

  return (
    <PageShell>
      <PageHeader
        eyebrow="Scenarios"
        title="AI scenario generator"
        description="Take a format that is currently working and rewrite it for your niche — hook, script, shot list and a recording plan."
      />

      <div className="mt-6">
        <ScenarioGenerator
          trends={trends.items}
          defaultTrendId={trendId}
          defaults={{
            niche: profile?.niche ?? "",
            audience: profile?.audience ?? "",
            audience_age: profile?.audience_age ?? "25-34",
            platform: profile?.platforms?.[0] ?? "tiktok",
            goal: profile?.goal ?? "audience_growth",
            preferred_style: profile?.preferred_style ?? "",
            production_capacity: profile?.production_capacity ?? "low",
            language: profile?.languages?.[0] ?? "en",
          }}
        />
      </div>

      {existing.items.length ? (
        <section className="mt-10">
          <div className="flex items-baseline justify-between">
            <SectionLabel>Your library</SectionLabel>
            <span className="tabular text-[11.5px] text-ink-muted">{existing.total} saved</span>
          </div>
          <div className="mt-3 grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {existing.items.map((s) => (
              <ScenarioMiniCard key={s.id} scenario={s} />
            ))}
          </div>
        </section>
      ) : (
        <Card className="mt-10 flex items-center gap-3 p-4">
          <Wand2 className="size-4 shrink-0 text-ink-muted" />
          <p className="text-[13px] text-ink-secondary">
            Generated scenarios are saved automatically and will appear here. You can also start
            from a trend&apos;s{" "}
            <Link href="/discover" className="text-[#a99bff] hover:underline">
              Recreate
            </Link>{" "}
            button.
          </p>
        </Card>
      )}
    </PageShell>
  );
}
