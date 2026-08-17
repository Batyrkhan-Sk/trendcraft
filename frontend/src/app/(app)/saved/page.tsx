import Link from "next/link";
import { Bookmark } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { ScenarioMiniCard } from "@/components/scenarios/scenario-card";
import { TrendCard } from "@/components/trends/trend-card";
import { Button, EmptyState, SectionLabel } from "@/components/ui/primitives";
import { getSaved } from "@/lib/api";

export const metadata = { title: "Saved" };
export const dynamic = "force-dynamic";

export default async function SavedPage() {
  const items = await getSaved();
  const trends = items.filter((i) => i.trend).map((i) => i.trend!);
  const scenarios = items.filter((i) => i.scenario).map((i) => i.scenario!);

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Saved"
        title="Your library"
        description="Formats and scenarios you have bookmarked."
        actions={
          <span className="tabular text-[12.5px] text-ink-muted">{items.length} items</span>
        }
      />

      {!items.length ? (
        <div className="mt-6">
          <EmptyState
            icon={Bookmark}
            title="Nothing saved yet"
            description="Bookmark a format from Discover, or save a scenario after generating one. Saved items show up here and on your dashboard."
            action={
              <Link href="/discover">
                <Button variant="primary">Browse formats</Button>
              </Link>
            }
          />
        </div>
      ) : (
        <div className="mt-6 flex flex-col gap-10">
          {trends.length ? (
            <section>
              <SectionLabel>Formats</SectionLabel>
              <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {trends.map((t) => (
                  <TrendCard key={t.id} trend={t} />
                ))}
              </div>
            </section>
          ) : null}

          {scenarios.length ? (
            <section>
              <SectionLabel>Scenarios</SectionLabel>
              <div className="mt-3 grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                {scenarios.map((s) => (
                  <ScenarioMiniCard key={s.id} scenario={s} />
                ))}
              </div>
            </section>
          ) : null}
        </div>
      )}
    </PageShell>
  );
}
