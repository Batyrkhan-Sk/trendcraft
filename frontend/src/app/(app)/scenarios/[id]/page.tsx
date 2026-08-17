import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Clapperboard } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { RecordingGuidePanel } from "@/components/scenarios/recording-guide";
import { ScenarioDetail } from "@/components/scenarios/scenario-card";
import { SaveButton } from "@/components/trends/save-button";
import { Badge, Card } from "@/components/ui/primitives";
import { ApiError, getScenario } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  try {
    const s = await getScenario(id);
    return { title: s.title };
  } catch {
    return { title: "Scenario" };
  }
}

export default async function ScenarioPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let scenario;
  try {
    scenario = await getScenario(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  return (
    <PageShell>
      <Link
        href="/scenarios"
        className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted transition-colors hover:text-ink"
      >
        <ArrowLeft className="size-3.5" /> Scenarios
      </Link>

      <div className="mt-4">
        <PageHeader
          eyebrow={scenario.kind === "recreation" ? "Recreation" : "Scenario"}
          title={scenario.title}
          actions={scenario.id ? <SaveButton entityType="scenario" entityId={scenario.id} /> : null}
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {scenario.trend_name ? (
          <Badge tone="brand">Adapted from: {scenario.trend_name}</Badge>
        ) : null}
        {scenario.platform ? <Badge tone="outline">{scenario.platform}</Badge> : null}
        {scenario.niche ? <Badge tone="outline">{scenario.niche}</Badge> : null}
        <span className="ml-auto font-mono text-[11px] text-ink-faint">
          {scenario.generator_model}
        </span>
      </div>

      <div className="mt-6">
        <ScenarioDetail scenario={scenario} />
      </div>

      {scenario.recording_guide?.shots?.length ? (
        <section className="mt-10">
          <Card className="mb-4 flex items-center gap-3 border-brand-line bg-brand-soft p-4">
            <Clapperboard className="size-5 shrink-0 text-[#c3b5ff]" />
            <div>
              <h2 className="text-[15px] font-semibold tracking-tight text-ink">
                How to record this video
              </h2>
              <p className="mt-0.5 text-[12.5px] text-ink-secondary">
                Shot list, camera and framing, editing blueprint, and a storyboard to plan against
                before you film.
              </p>
            </div>
          </Card>
          <RecordingGuidePanel guide={scenario.recording_guide} />
        </section>
      ) : null}
    </PageShell>
  );
}
