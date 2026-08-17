import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { RecreatePanel } from "@/components/scenarios/recreate-panel";
import { FormatTimeline } from "@/components/trends/format-timeline";
import { StatusPill } from "@/components/trends/status-pill";
import { Card, SectionLabel } from "@/components/ui/primitives";
import { ApiError, getProfile, getTrend } from "@/lib/api";
import { duration } from "@/lib/format";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const trend = await getTrend(slug);
    return { title: `Recreate · ${trend.name}` };
  } catch {
    return { title: "Recreate" };
  }
}

export default async function RecreatePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let trend;
  try {
    trend = await getTrend(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }
  const profile = await getProfile();

  return (
    <PageShell>
      <Link
        href={`/trends/${trend.slug}`}
        className="inline-flex items-center gap-1.5 text-[12.5px] text-ink-muted transition-colors hover:text-ink"
      >
        <ArrowLeft className="size-3.5" /> {trend.name}
      </Link>

      <div className="mt-4">
        <PageHeader
          eyebrow="Recreate"
          title={`Your version of "${trend.name}"`}
          description="The format's skeleton, rebuilt around your niche — with a shooting plan you can follow on the day."
          actions={<StatusPill status={trend.status} />}
        />
      </div>

      {/* The format being adapted, kept visible so the user can see what is being
          preserved and what is being replaced. */}
      <Card className="mt-5 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <SectionLabel>The structure you&apos;re keeping</SectionLabel>
          <span className="tabular text-[11.5px] text-ink-muted">
            {duration(trend.median_duration_sec)} median · {trend.video_count} videos analysed
          </span>
        </div>
        {trend.format_pattern ? (
          <p className="mt-2 font-mono text-[12.5px] text-[#a99bff]">{trend.format_pattern}</p>
        ) : null}
        <div className="mt-3">
          <FormatTimeline segments={trend.format_structure} />
        </div>
      </Card>

      <div className="mt-6">
        <RecreatePanel
          trendSlug={trend.slug}
          trendName={trend.name}
          defaults={{
            niche: profile?.niche ?? "",
            platform: profile?.platforms?.[0] ?? trend.platforms[0] ?? "tiktok",
            goal: profile?.goal ?? "audience_growth",
            production_capacity: profile?.production_capacity ?? "low",
          }}
        />
      </div>
    </PageShell>
  );
}
