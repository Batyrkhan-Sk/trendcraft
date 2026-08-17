import Link from "next/link";
import { Check, Cpu, Database, X } from "lucide-react";
import { PageHeader, PageShell } from "@/components/shell/page-header";
import { Badge, Button, Card, Divider, SectionLabel } from "@/components/ui/primitives";
import { apiSafe, getProfile } from "@/lib/api";
import { titleCase } from "@/lib/format";
import { platformLabel } from "@/lib/meta";

export const metadata = { title: "Settings" };
export const dynamic = "force-dynamic";

interface PipelineStatus {
  connectors: Record<string, { healthy: boolean; platform: string }>;
  ai: {
    llm_configured: boolean;
    llm_model: string;
    vision_model: string;
    embedding_provider: string;
    embedding_dim: number;
  };
  engine: Record<string, number>;
}

export default async function SettingsPage() {
  const [profile, status] = await Promise.all([
    getProfile(),
    apiSafe<PipelineStatus | null>("/pipeline/status", null),
  ]);

  return (
    <PageShell>
      <PageHeader
        eyebrow="Settings"
        title="Profile & pipeline"
        description="Your creator profile drives the personalised feed. The pipeline section shows which data sources and models are live."
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

      <section className="mt-8">
        <SectionLabel>Data sources</SectionLabel>
        <p className="mt-1 text-[12.5px] text-ink-faint">
          A connector is healthy when its credentials are present. Unhealthy connectors are skipped
          rather than failing the run.
        </p>
        <Card className="mt-3 p-1.5">
          {status?.connectors ? (
            Object.entries(status.connectors).map(([name, c]) => (
              <div
                key={name}
                className="flex items-center justify-between gap-3 rounded-lg px-3 py-2.5"
              >
                <div className="flex items-center gap-2.5">
                  <Database className="size-4 text-ink-muted" />
                  <span className="text-[13px] font-medium text-ink">{platformLabel(name)}</span>
                </div>
                {c.healthy ? (
                  <span
                    className="inline-flex items-center gap-1.5 text-[12px] font-medium"
                    style={{ color: "var(--color-state-good)" }}
                  >
                    <Check className="size-3.5" /> Configured
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-[12px] text-ink-muted">
                    <X className="size-3.5" /> Needs credentials
                  </span>
                )}
              </div>
            ))
          ) : (
            <p className="px-3 py-4 text-[13px] text-ink-faint">API unreachable.</p>
          )}
        </Card>
      </section>

      {status?.ai ? (
        <section className="mt-8">
          <SectionLabel>AI configuration</SectionLabel>
          <Card className="mt-3 p-5">
            <div className="flex items-center gap-2.5">
              <Cpu className="size-4 text-ink-muted" />
              <span className="text-[13px] font-medium text-ink">Models</span>
              {status.ai.llm_configured ? (
                <Badge tone="brand">Live</Badge>
              ) : (
                <Badge tone="outline">Offline fallback</Badge>
              )}
            </div>

            {!status.ai.llm_configured ? (
              <p className="mt-3 text-[12.5px] leading-relaxed text-ink-secondary">
                No <span className="font-mono text-[#a99bff]">GOOGLE_API_KEY</span> is set, so
                extraction, trend naming and scenario writing run on deterministic local
                implementations. Clustering and scoring are unaffected — those never call a model.
              </p>
            ) : null}

            <Divider className="my-4" />

            <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
              <Row label="Generation model" value={status.ai.llm_model} mono />
              <Row label="Video understanding" value={status.ai.vision_model} mono />
              <Row label="Embeddings" value={status.ai.embedding_provider} mono />
              <Row label="Embedding dimensions" value={`${status.ai.embedding_dim}`} mono />
            </dl>
          </Card>
        </section>
      ) : null}

      {status?.engine ? (
        <section className="mt-8">
          <SectionLabel>Engine tuning</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Set via environment variables; a change takes effect on the next re-cluster.
          </p>
          <Card className="mt-3 p-5">
            <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-3">
              <Row
                label="Minimum cluster size"
                value={`${status.engine.min_cluster_size} videos`}
                mono
              />
              <Row
                label="Similarity threshold"
                value={`${status.engine.cluster_similarity_threshold}`}
                mono
              />
              <Row
                label="Recency half-life"
                value={`${status.engine.trend_half_life_hours}h`}
                mono
              />
            </dl>
          </Card>
        </section>
      ) : null}
    </PageShell>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] uppercase tracking-[0.06em] text-ink-muted">{label}</dt>
      <dd
        className={`mt-0.5 truncate text-[13px] text-ink-secondary ${mono ? "font-mono text-[12px]" : ""}`}
      >
        {value}
      </dd>
    </div>
  );
}
