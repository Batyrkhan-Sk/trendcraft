"use client";

import { useCallback, useMemo, useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ChevronDown, RotateCcw, Search, SlidersHorizontal } from "lucide-react";
import { cn, titleCase } from "@/lib/format";
import { platformLabel } from "@/lib/meta";

/** Filters that map 1:1 onto the API's query parameters. */
const SORTS = [
  { value: "opportunity", label: "Opportunity" },
  { value: "growth_7d", label: "Growth (7d)" },
  { value: "growth_24h", label: "Momentum (24h)" },
  { value: "trend_score", label: "Trend score" },
  { value: "engagement", label: "Engagement" },
  { value: "recency", label: "Newest" },
  { value: "videos", label: "Volume" },
];

const GROWTH_STEPS = [
  { value: "", label: "Any" },
  { value: "0", label: "Positive" },
  { value: "0.25", label: "> +25%" },
  { value: "0.75", label: "> +75%" },
  { value: "1.5", label: "> +150%" },
];

const ENGAGEMENT_STEPS = [
  { value: "", label: "Any" },
  { value: "0.05", label: "> 5%" },
  { value: "0.08", label: "> 8%" },
  { value: "0.11", label: "> 11%" },
];

const DURATION_STEPS = [
  { value: "", label: "Any length" },
  { value: "0:20", label: "Under 20s" },
  { value: "20:40", label: "20–40s" },
  { value: "40:", label: "Over 40s" },
];

const RECENCY_STEPS = [
  { value: "", label: "All time" },
  { value: "7", label: "First seen ≤ 7d" },
  { value: "14", label: "First seen ≤ 14d" },
  { value: "30", label: "First seen ≤ 30d" },
];

export function TrendFilters({ facets }: { facets: Record<string, string[]> }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [pending, startTransition] = useTransition();
  const [expanded, setExpanded] = useState(false);
  const [query, setQuery] = useState(params.get("q") ?? "");

  const setParam = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(params.toString());
      if (!value) next.delete(key);
      else next.set(key, value);
      startTransition(() => router.replace(`${pathname}?${next.toString()}`, { scroll: false }));
    },
    [params, pathname, router],
  );

  const setDuration = useCallback(
    (value: string) => {
      const next = new URLSearchParams(params.toString());
      next.delete("min_duration");
      next.delete("max_duration");
      if (value) {
        const [min, max] = value.split(":");
        if (min) next.set("min_duration", min);
        if (max) next.set("max_duration", max);
      }
      startTransition(() => router.replace(`${pathname}?${next.toString()}`, { scroll: false }));
    },
    [params, pathname, router],
  );

  const durationValue = useMemo(() => {
    const min = params.get("min_duration") ?? "";
    const max = params.get("max_duration") ?? "";
    return min || max ? `${min}:${max}` : "";
  }, [params]);

  const activeCount = useMemo(
    () =>
      [
        "platform",
        "niche",
        "country",
        "language",
        "content_type",
        "status",
        "competition",
        "difficulty",
        "min_growth",
        "min_engagement",
        "min_duration",
        "max_duration",
        "since_days",
        "q",
      ].filter((k) => params.get(k)).length,
    [params],
  );

  return (
    <div className={cn("transition-opacity", pending && "opacity-60")}>
      <div className="flex flex-wrap items-center gap-2">
        <label className="relative flex h-9 min-w-[220px] flex-1 items-center sm:max-w-xs">
          <Search className="pointer-events-none absolute left-3 size-3.5 text-ink-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") setParam("q", query || null);
            }}
            onBlur={() => setParam("q", query || null)}
            placeholder="Search formats…"
            className="h-full w-full rounded-lg border border-line bg-surface pl-8.5 pr-3 text-[13px] text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
          />
        </label>

        <Select
          value={params.get("sort") ?? "opportunity"}
          onChange={(v) => setParam("sort", v === "opportunity" ? null : v)}
          options={SORTS}
          prefix="Sort"
        />

        <Select
          value={params.get("platform") ?? ""}
          onChange={(v) => setParam("platform", v)}
          options={[
            { value: "", label: "All platforms" },
            ...(facets.platforms ?? []).map((p) => ({ value: p, label: platformLabel(p) })),
          ]}
        />

        <Select
          value={params.get("niche") ?? ""}
          onChange={(v) => setParam("niche", v)}
          options={[
            { value: "", label: "All niches" },
            ...(facets.niches ?? []).map((n) => ({ value: n, label: titleCase(n) })),
          ]}
        />

        <button
          onClick={() => setExpanded((v) => !v)}
          className={cn(
            "inline-flex h-9 items-center gap-1.5 rounded-lg border px-3 text-[13px] font-medium transition-colors",
            expanded || activeCount > 2
              ? "border-brand-line bg-brand-soft text-[#c3b5ff]"
              : "border-line bg-surface text-ink-secondary hover:border-line-strong",
          )}
        >
          <SlidersHorizontal className="size-3.5" />
          Filters
          {activeCount > 0 ? (
            <span className="tabular ml-0.5 rounded bg-surface-3 px-1 text-[11px] text-ink">
              {activeCount}
            </span>
          ) : null}
        </button>

        {activeCount > 0 ? (
          <button
            onClick={() => startTransition(() => router.replace(pathname, { scroll: false }))}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg px-2.5 text-[12.5px] text-ink-muted hover:text-ink"
          >
            <RotateCcw className="size-3.5" /> Reset
          </button>
        ) : null}
      </div>

      {expanded ? (
        <div className="mt-3 grid gap-3 rounded-xl border border-line bg-surface p-3.5 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Status">
            <Select
              value={params.get("status") ?? ""}
              onChange={(v) => setParam("status", v)}
              options={[
                { value: "", label: "Any status" },
                ...(facets.statuses ?? []).map((s) => ({ value: s, label: titleCase(s) })),
              ]}
              full
            />
          </Field>
          <Field label="Competition">
            <Select
              value={params.get("competition") ?? ""}
              onChange={(v) => setParam("competition", v)}
              options={[
                { value: "", label: "Any level" },
                ...(facets.competition_levels ?? []).map((s) => ({ value: s, label: titleCase(s) })),
              ]}
              full
            />
          </Field>
          <Field label="Production difficulty">
            <Select
              value={params.get("difficulty") ?? ""}
              onChange={(v) => setParam("difficulty", v)}
              options={[
                { value: "", label: "Any effort" },
                ...(facets.difficulties ?? []).map((s) => ({ value: s, label: titleCase(s) })),
              ]}
              full
            />
          </Field>
          <Field label="Content type">
            <Select
              value={params.get("content_type") ?? ""}
              onChange={(v) => setParam("content_type", v)}
              options={[
                { value: "", label: "Any type" },
                ...(facets.content_types ?? []).map((s) => ({ value: s, label: titleCase(s) })),
              ]}
              full
            />
          </Field>
          <Field label="Country">
            <Select
              value={params.get("country") ?? ""}
              onChange={(v) => setParam("country", v)}
              options={[
                { value: "", label: "Worldwide" },
                ...(facets.countries ?? []).map((s) => ({ value: s, label: s })),
              ]}
              full
            />
          </Field>
          <Field label="Language">
            <Select
              value={params.get("language") ?? ""}
              onChange={(v) => setParam("language", v)}
              options={[
                { value: "", label: "Any language" },
                ...(facets.languages ?? []).map((s) => ({ value: s, label: s.toUpperCase() })),
              ]}
              full
            />
          </Field>
          <Field label="Growth (7d)">
            <Select
              value={params.get("min_growth") ?? ""}
              onChange={(v) => setParam("min_growth", v)}
              options={GROWTH_STEPS}
              full
            />
          </Field>
          <Field label="Engagement">
            <Select
              value={params.get("min_engagement") ?? ""}
              onChange={(v) => setParam("min_engagement", v)}
              options={ENGAGEMENT_STEPS}
              full
            />
          </Field>
          <Field label="Video length">
            <Select value={durationValue} onChange={setDuration} options={DURATION_STEPS} full />
          </Field>
          <Field label="First seen">
            <Select
              value={params.get("since_days") ?? ""}
              onChange={(v) => setParam("since_days", v)}
              options={RECENCY_STEPS}
              full
            />
          </Field>
        </div>
      ) : null}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 text-[11px] uppercase tracking-[0.08em] text-ink-muted">{label}</div>
      {children}
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
  prefix,
  full,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  prefix?: string;
  full?: boolean;
}) {
  return (
    <div className={cn("relative", full ? "w-full" : "")}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-9 cursor-pointer appearance-none rounded-lg border border-line bg-surface pl-3 pr-8 text-[13px] text-ink transition-colors hover:border-line-strong focus:border-line-strong focus:outline-none",
          full && "w-full",
        )}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value} className="bg-surface-2">
            {prefix && o.value ? `${prefix}: ${o.label}` : o.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-3.5 -translate-y-1/2 text-ink-muted" />
    </div>
  );
}
