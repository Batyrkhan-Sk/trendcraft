"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Wand2 } from "lucide-react";
import { RecordingGuidePanel } from "@/components/scenarios/recording-guide";
import { ScenarioDetail } from "@/components/scenarios/scenario-card";
import { Button, Card, SectionLabel } from "@/components/ui/primitives";
import { apiBase } from "@/lib/api";
import { cn, titleCase } from "@/lib/format";
import { CONTENT_TYPES, GOALS, LANGUAGES, NICHES, platformLabel } from "@/lib/meta";
import type { Scenario, TrendSummary } from "@/lib/types";

const PLATFORMS = ["tiktok", "instagram", "youtube"];
const AGES = ["13-17", "18-24", "25-34", "35-44", "45+"];
const CAPACITY = [
  { value: "low", label: "Phone only" },
  { value: "medium", label: "Phone + basic edit" },
  { value: "high", label: "Full setup" },
];

export function ScenarioGenerator({
  trends,
  defaultTrendId,
  defaults,
}: {
  trends: TrendSummary[];
  defaultTrendId?: string;
  defaults?: Partial<Record<string, string>>;
}) {
  const router = useRouter();
  const [form, setForm] = useState({
    trend_id: defaultTrendId ?? "",
    niche: defaults?.niche ?? "",
    audience: defaults?.audience ?? "",
    audience_age: defaults?.audience_age ?? "25-34",
    platform: defaults?.platform ?? "tiktok",
    goal: defaults?.goal ?? "audience_growth",
    preferred_style: defaults?.preferred_style ?? "",
    topic: "",
    languages: [defaults?.language ?? "en"],
    production_capacity: defaults?.production_capacity ?? "low",
    count: 3,
    include_recording_guide: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Scenario[] | null>(null);
  const [openIndex, setOpenIndex] = useState(0);

  const set = (key: string, value: unknown) => setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/scenarios/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": "demo@trendcraft.app",
        },
        body: JSON.stringify({ ...form, trend_id: form.trend_id || null }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResults(data.items);
      setOpenIndex(0);
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? "Generation failed. The API may be unreachable, or no trends exist yet."
          : "Generation failed.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <Card className="p-5">
        <form onSubmit={submit}>
          <SectionLabel>Adapt a trending format to you</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            The structure comes from the trend. Everything else comes from these answers.
          </p>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Field label="Trend">
              <Select
                value={form.trend_id}
                onChange={(v) => set("trend_id", v)}
                options={[
                  { value: "", label: "Best fit for my profile" },
                  ...trends.map((t) => ({ value: t.id, label: t.name })),
                ]}
              />
            </Field>

            <Field label="Niche">
              <Select
                value={form.niche}
                onChange={(v) => set("niche", v)}
                options={[
                  { value: "", label: "Use my profile" },
                  ...NICHES.map((n) => ({ value: n, label: titleCase(n) })),
                ]}
              />
            </Field>

            <Field label="Platform">
              <Select
                value={form.platform}
                onChange={(v) => set("platform", v)}
                options={PLATFORMS.map((p) => ({ value: p, label: platformLabel(p) }))}
              />
            </Field>

            <Field label="Goal">
              <Select
                value={form.goal}
                onChange={(v) => set("goal", v)}
                options={GOALS.map((g) => ({ value: g.value, label: g.label }))}
              />
            </Field>

            <Field label="Audience age">
              <Select
                value={form.audience_age}
                onChange={(v) => set("audience_age", v)}
                options={AGES.map((a) => ({ value: a, label: a }))}
              />
            </Field>

            <Field label="Production capacity">
              <Select
                value={form.production_capacity}
                onChange={(v) => set("production_capacity", v)}
                options={CAPACITY}
              />
            </Field>

            <Field label="Audience" className="sm:col-span-2">
              <Input
                value={form.audience}
                onChange={(v) => set("audience", v)}
                placeholder="e.g. solo founders shipping their first product"
              />
            </Field>

            <Field label="Language">
              <Select
                value={form.languages[0]}
                onChange={(v) => set("languages", [v])}
                options={LANGUAGES}
              />
            </Field>

            <Field label="Topic to cover" className="sm:col-span-2">
              <Input
                value={form.topic}
                onChange={(v) => set("topic", v)}
                placeholder="Leave blank and the AI picks angles for your niche"
              />
            </Field>

            <Field label="Preferred style">
              <Input
                value={form.preferred_style}
                onChange={(v) => set("preferred_style", v)}
                placeholder="e.g. dry, no-fluff, screen-heavy"
              />
            </Field>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button type="submit" variant="primary" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Generating…
                </>
              ) : (
                <>
                  <Wand2 className="size-4" /> Generate {form.count} scenarios
                </>
              )}
            </Button>

            <div className="flex items-center gap-1">
              {[1, 3, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => set("count", n)}
                  className={cn(
                    "h-8 w-8 rounded-lg border text-[12.5px] font-medium transition-colors",
                    form.count === n
                      ? "border-brand-line bg-brand-soft text-[#c3b5ff]"
                      : "border-line text-ink-muted hover:border-line-strong hover:text-ink",
                  )}
                >
                  {n}
                </button>
              ))}
            </div>

            <label className="flex cursor-pointer items-center gap-2 text-[12.5px] text-ink-secondary">
              <input
                type="checkbox"
                checked={form.include_recording_guide}
                onChange={(e) => set("include_recording_guide", e.target.checked)}
                className="size-3.5 accent-[#7c5cff]"
              />
              Include recording guide
            </label>
          </div>

          {error ? (
            <p className="mt-3 text-[12.5px]" style={{ color: "var(--color-state-critical)" }}>
              {error}
            </p>
          ) : null}
        </form>
      </Card>

      {results?.length ? (
        <section>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <SectionLabel>
              {results.length} scenario{results.length === 1 ? "" : "s"} generated
            </SectionLabel>
            <span className="text-[11px] text-ink-faint">
              Saved to your library · generated by {results[0].generator_model}
            </span>
          </div>

          {/* Tabs rather than a stack: the scenarios are alternatives, and putting
              them side by side is what makes them comparable. */}
          <div className="rail mt-3 flex gap-2 overflow-x-auto pb-1">
            {results.map((s, i) => (
              <button
                key={s.id ?? i}
                onClick={() => setOpenIndex(i)}
                className={cn(
                  "shrink-0 rounded-lg border px-3 py-2 text-left text-[12.5px] transition-colors",
                  openIndex === i
                    ? "border-brand-line bg-brand-soft text-ink"
                    : "border-line bg-surface text-ink-muted hover:border-line-strong hover:text-ink-secondary",
                )}
              >
                <span className="tabular mr-1.5 text-ink-faint">{i + 1}</span>
                <span className="line-clamp-1 inline max-w-[240px] align-middle font-medium">
                  {s.title}
                </span>
              </button>
            ))}
          </div>

          <div className="mt-4">
            <ScenarioDetail scenario={results[openIndex]} />
            {results[openIndex].recording_guide ? (
              <div className="mt-8">
                <div className="mb-4 rounded-lg border border-line bg-surface-2 px-4 py-3">
                  <h2 className="text-[15px] font-semibold tracking-tight text-ink">
                    How to record this video
                  </h2>
                  <p className="mt-0.5 text-[12.5px] text-ink-secondary">
                    Shot list, framing, editing blueprint and a storyboard to plan against.
                  </p>
                </div>
                <RecordingGuidePanel guide={results[openIndex].recording_guide!} />
              </div>
            ) : null}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <label className="mb-1.5 block text-[11px] uppercase tracking-[0.08em] text-ink-muted">
        {label}
      </label>
      {children}
    </div>
  );
}

function Input({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="h-9 w-full rounded-lg border border-line bg-surface px-3 text-[13px] text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
    />
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 w-full cursor-pointer appearance-none rounded-lg border border-line bg-surface px-3 text-[13px] text-ink focus:border-line-strong focus:outline-none"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value} className="bg-surface-2">
          {o.label}
        </option>
      ))}
    </select>
  );
}

export { CONTENT_TYPES };
