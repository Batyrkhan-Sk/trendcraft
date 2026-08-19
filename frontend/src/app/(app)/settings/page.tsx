import Link from "next/link";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { Button, Card, SectionLabel } from "@/components/ui/primitives";
import { getProfile } from "@/lib/api";
import { titleCase } from "@/lib/format";
import { platformLabel } from "@/lib/meta";

export const metadata = { title: "Settings" };
export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const profile = await getProfile();

  return (
    <PageShell>
      <PageHeader
        eyebrow="Settings"
        title="Your profile"
        description="Your creator profile drives the personalised feed — what you make, where you post it, and who it is for."
        actions={
          <Link href="/onboarding">
            <Button variant="primary">Edit profile</Button>
          </Link>
        }
      />

      <section className="mt-6">
        <SectionLabel>Creator profile</SectionLabel>
        <Card className="mt-3 p-5">
          {profile?.niche ? (
            <dl className="grid gap-x-8 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">
              <Row label="Niche" value={titleCase(profile.niche)} />
              <Row label="Sub-topics" value={profile.sub_niches?.join(", ") || "—"} />
              <Row label="Audience" value={profile.audience || "—"} />
              <Row label="Audience age" value={profile.audience_age || "—"} />
              <Row
                label="Platforms"
                value={profile.platforms?.map(platformLabel).join(", ") || "—"}
              />
              <Row label="Content types" value={profile.content_types?.join(", ") || "—"} />
              <Row label="Goal" value={titleCase(profile.goal ?? "—")} />
              <Row label="Languages" value={profile.languages?.join(", ").toUpperCase() || "—"} />
              <Row
                label="Production capacity"
                value={titleCase(profile.production_capacity ?? "—")}
              />
              <Row label="Preferred style" value={profile.preferred_style || "—"} />
            </dl>
          ) : (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-[13px] text-ink-secondary">
                No profile yet. Until you set one, the feed ranks purely on opportunity.
              </p>
              <Link href="/onboarding">
                <Button variant="primary" size="sm">
                  Start onboarding
                </Button>
              </Link>
            </div>
          )}
        </Card>
      </section>
    </PageShell>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] uppercase tracking-[0.06em] text-ink-muted">{label}</dt>
      <dd className="mt-0.5 truncate text-[13px] text-ink-secondary">{value}</dd>
    </div>
  );
}
