"use client";

import { useState } from "react";
import { Clapperboard, Loader2, RefreshCw } from "lucide-react";
import { RecordingGuidePanel } from "@/components/scenarios/recording-guide";
import { ScenarioDetail } from "@/components/scenarios/scenario-card";
import { Button, Card, SectionLabel } from "@/components/ui/primitives";
import { apiBase } from "@/lib/api";
import { titleCase } from "@/lib/format";
import { GOALS, NICHES, platformLabel } from "@/lib/meta";
import type { Scenario } from "@/lib/types";

const PLATFORMS = ["tiktok", "instagram", "youtube"];

/**
 * The "Recreate" flow.
 *
 * One click with sensible defaults produces the complete package; the inputs are
 * exposed underneath for anyone who wants to steer it. Generation happens on
 * demand rather than at page load because it is a real model call and should be
 * something the user chose to spend.
 */
export function RecreatePanel({
  trendSlug,
  trendName,
  defaults,
}: {
  trendSlug: string;
  trendName: string;
  defaults: { niche: string; platform: string; goal: string; production_capacity: string };
}) {
  const [form, setForm] = useState({ ...defaults, topic: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/scenarios/recreate/${trendSlug}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": "demo@trendcraft.app",
        },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error(await res.text());
      setScenario(await res.json());
    } catch {
      setError("Could not generate. Check that the API is reachable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <Card className="p-5">
        <SectionLabel>Make it yours</SectionLabel>
        <p className="mt-1 text-[12.5px] text-ink-faint">
          Keeps the structure of <span className="text-ink-secondary">{trendName}</span> and replaces
          every specific — so the result is your video, not a copy of someone else&apos;s.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Your niche">
            <select
              value={form.niche}
              onChange={(e) => set("niche", e.target.value)}
              className="h-9 w-full cursor-pointer rounded-lg border border-line bg-surface px-3 text-[13px] text-ink focus:border-line-strong focus:outline-none"
            >
              <option value="">Use my profile</option>
              {NICHES.map((n) => (
                <option key={n} value={n} className="bg-surface-2">
                  {titleCase(n)}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Platform">
            <select
              value={form.platform}
              onChange={(e) => set("platform", e.target.value)}
              className="h-9 w-full cursor-pointer rounded-lg border border-line bg-surface px-3 text-[13px] text-ink focus:border-line-strong focus:outline-none"
            >
              {PLATFORMS.map((p) => (
                <option key={p} value={p} className="bg-surface-2">
                  {platformLabel(p)}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Goal">
            <select
              value={form.goal}
              onChange={(e) => set("goal", e.target.value)}
              className="h-9 w-full cursor-pointer rounded-lg border border-line bg-surface px-3 text-[13px] text-ink focus:border-line-strong focus:outline-none"
            >
              {GOALS.map((g) => (
                <option key={g.value} value={g.value} className="bg-surface-2">
                  {g.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Topic (optional)">
            <input
              value={form.topic}
              onChange={(e) => set("topic", e.target.value)}
              placeholder="What it's about"
              className="h-9 w-full rounded-lg border border-line bg-surface px-3 text-[13px] text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
            />
          </Field>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Button variant="primary" onClick={run} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Building your version…
              </>
            ) : scenario ? (
              <>
                <RefreshCw className="size-4" /> Regenerate
              </>
            ) : (
              <>
                <Clapperboard className="size-4" /> Generate my version
              </>
            )}
          </Button>
          {!scenario && !loading ? (
            <span className="text-[12px] text-ink-faint">
              Produces a script, shot list, editing blueprint and storyboard.
            </span>
          ) : null}
        </div>

        {error ? (
          <p className="mt-3 text-[12.5px]" style={{ color: "var(--color-state-critical)" }}>
            {error}
          </p>
        ) : null}
      </Card>

      {loading && !scenario ? <GeneratingSkeleton /> : null}

      {scenario ? (
        <>
          <ScenarioDetail scenario={scenario} />
          {scenario.recording_guide ? (
            <section className="mt-4">
              <Card className="mb-4 flex items-center gap-3 border-brand-line bg-brand-soft p-4">
                <Clapperboard className="size-5 shrink-0 text-[#c3b5ff]" />
                <div>
                  <h2 className="text-[15px] font-semibold tracking-tight text-ink">
                    How to record this video
                  </h2>
                  <p className="mt-0.5 text-[12.5px] text-ink-secondary">
                    Every shot, the framing, what to say, and how to cut it.
                  </p>
                </div>
              </Card>
              <RecordingGuidePanel guide={scenario.recording_guide} />
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1.5 block text-[11px] uppercase tracking-[0.08em] text-ink-muted">
        {label}
      </label>
      {children}
    </div>
  );
}

function GeneratingSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <div className="skeleton h-32 rounded-[var(--radius-card)]" />
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="skeleton h-24 rounded-[var(--radius-card)]" />
        <div className="skeleton h-24 rounded-[var(--radius-card)]" />
      </div>
      <div className="skeleton h-40 rounded-[var(--radius-card)]" />
    </div>
  );
}
