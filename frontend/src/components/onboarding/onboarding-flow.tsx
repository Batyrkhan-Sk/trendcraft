"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Check, Loader2, Sparkles } from "lucide-react";
import { Button, Card } from "@/components/ui/primitives";
import { apiBase } from "@/lib/api";
import { cn, titleCase } from "@/lib/format";
import { CONTENT_TYPES, GOALS, LANGUAGES, NICHES, platformLabel } from "@/lib/meta";
import type { Profile } from "@/lib/types";

const PLATFORMS = ["tiktok", "instagram", "youtube"];
const AGES = ["13-17", "18-24", "25-34", "35-44", "45+"];
const CAPACITY = [
  { value: "low", label: "Phone only", hint: "Front camera and a screen recorder" },
  { value: "medium", label: "Phone + editing", hint: "Comfortable with cuts, overlays, subtitles" },
  { value: "high", label: "Full setup", hint: "Lighting, mics, multi-shot edits" },
];

const STEPS = [
  { key: "niche", title: "What do you make?", hint: "Pick the niche your content lives in." },
  { key: "audience", title: "Who is it for?", hint: "The clearer this is, the sharper the hooks." },
  { key: "platforms", title: "Where do you publish?", hint: "Formats behave differently per platform." },
  { key: "format", title: "What do you make and why?", hint: "Content types, goal and how much you can produce." },
] as const;

export function OnboardingFlow({ initial }: { initial: Profile | null }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    niche: initial?.niche ?? "",
    sub_niches: initial?.sub_niches ?? [],
    audience: initial?.audience ?? "",
    audience_age: initial?.audience_age ?? "25-34",
    platforms: initial?.platforms ?? [],
    content_types: initial?.content_types ?? [],
    goal: initial?.goal ?? "",
    languages: initial?.languages ?? ["en"],
    country: initial?.country ?? "",
    preferred_style: initial?.preferred_style ?? "",
    production_capacity: initial?.production_capacity ?? "low",
  });

  const set = (k: string, v: unknown) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (k: "platforms" | "content_types" | "languages", value: string) =>
    setForm((f) => {
      const list = f[k] as string[];
      return { ...f, [k]: list.includes(value) ? list.filter((v) => v !== value) : [...list, value] };
    });

  const canAdvance = [
    !!form.niche,
    !!form.audience || !!form.audience_age,
    form.platforms.length > 0,
    !!form.goal,
  ][step];

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase()}/me/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": "demo@trendcraft.app",
        },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error();
      router.push("/");
      router.refresh();
    } catch {
      setError("Could not save. Check the API is running.");
      setSaving(false);
    }
  };

  const current = STEPS[step];

  return (
    <div className="relative z-10 mx-auto flex min-h-dvh w-full max-w-3xl flex-col px-5 py-10">
      <Link href="/" className="flex items-center gap-2.5">
        <span className="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-brand to-accent">
          <Sparkles className="size-4 text-canvas" strokeWidth={2.5} />
        </span>
        <span className="text-[15px] font-semibold tracking-tight">TrendCraft</span>
      </Link>

      <div className="mt-10">
        <div className="flex items-center gap-1.5">
          {STEPS.map((s, i) => (
            <div
              key={s.key}
              className={cn(
                "h-0.5 flex-1 rounded-full transition-colors",
                i <= step ? "bg-gradient-to-r from-brand to-accent" : "bg-line",
              )}
            />
          ))}
        </div>
        <div className="mt-3 text-[11px] uppercase tracking-[0.14em] text-ink-muted">
          Step {step + 1} of {STEPS.length}
        </div>
        <h1 className="mt-2 text-[26px] font-semibold leading-tight tracking-tight text-ink">
          {current.title}
        </h1>
        <p className="mt-1.5 text-[13.5px] text-ink-secondary">{current.hint}</p>
      </div>

      <Card className="mt-6 flex-1 p-5">
        {step === 0 ? (
          <div>
            <FieldLabel>Your niche</FieldLabel>
            <ChipGrid
              options={NICHES.map((n) => ({ value: n, label: titleCase(n) }))}
              selected={form.niche ? [form.niche] : []}
              onSelect={(v) => set("niche", v)}
            />

            <div className="mt-6">
              <FieldLabel>Sub-topics you cover</FieldLabel>
              <input
                value={form.sub_niches.join(", ")}
                onChange={(e) =>
                  set(
                    "sub_niches",
                    e.target.value
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean),
                  )
                }
                placeholder="e.g. automation, developer tools, no-code"
                className="h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-[13.5px] text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
              />
              <p className="mt-1.5 text-[11.5px] text-ink-faint">
                Comma separated. Used to sharpen scenario topics.
              </p>
            </div>
          </div>
        ) : null}

        {step === 1 ? (
          <div>
            <FieldLabel>Describe your audience</FieldLabel>
            <textarea
              value={form.audience}
              onChange={(e) => set("audience", e.target.value)}
              rows={3}
              placeholder="e.g. solo founders and operators trying to automate parts of their business"
              className="w-full resize-none rounded-lg border border-line bg-surface-2 px-3 py-2.5 text-[13.5px] leading-relaxed text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
            />

            <div className="mt-6">
              <FieldLabel>Age range</FieldLabel>
              <ChipGrid
                options={AGES.map((a) => ({ value: a, label: a }))}
                selected={[form.audience_age]}
                onSelect={(v) => set("audience_age", v)}
              />
            </div>

            <div className="mt-6">
              <FieldLabel>Languages you publish in</FieldLabel>
              <ChipGrid
                options={LANGUAGES}
                selected={form.languages}
                onSelect={(v) => toggle("languages", v)}
                multi
              />
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div>
            <FieldLabel>Platforms</FieldLabel>
            <div className="grid gap-2.5 sm:grid-cols-3">
              {PLATFORMS.map((p) => {
                const active = form.platforms.includes(p);
                return (
                  <button
                    key={p}
                    onClick={() => toggle("platforms", p)}
                    className={cn(
                      "rounded-xl border p-4 text-left transition-colors",
                      active
                        ? "border-brand-line bg-brand-soft"
                        : "border-line bg-surface-2 hover:border-line-strong",
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[14px] font-semibold text-ink">
                        {platformLabel(p)}
                      </span>
                      {active ? <Check className="size-4 text-[#c3b5ff]" /> : null}
                    </div>
                    <p className="mt-1 text-[11.5px] text-ink-muted">
                      {p === "tiktok"
                        ? "Fastest format turnover"
                        : p === "instagram"
                          ? "Reels, strong on visual formats"
                          : "Shorts, longer watch tolerance"}
                    </p>
                  </button>
                );
              })}
            </div>

            <div className="mt-6">
              <FieldLabel>Country (optional)</FieldLabel>
              <input
                value={form.country}
                onChange={(e) => set("country", e.target.value.toUpperCase().slice(0, 2))}
                placeholder="US"
                className="h-10 w-24 rounded-lg border border-line bg-surface-2 px-3 text-[13.5px] uppercase text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
              />
            </div>
          </div>
        ) : null}

        {step === 3 ? (
          <div>
            <FieldLabel>Content types you make</FieldLabel>
            <ChipGrid
              options={CONTENT_TYPES.map((c) => ({ value: c, label: titleCase(c) }))}
              selected={form.content_types}
              onSelect={(v) => toggle("content_types", v)}
              multi
            />

            <div className="mt-6">
              <FieldLabel>Your main goal</FieldLabel>
              <ChipGrid
                options={GOALS}
                selected={form.goal ? [form.goal] : []}
                onSelect={(v) => set("goal", v)}
              />
            </div>

            <div className="mt-6">
              <FieldLabel>How much can you produce?</FieldLabel>
              <div className="grid gap-2.5 sm:grid-cols-3">
                {CAPACITY.map((c) => {
                  const active = form.production_capacity === c.value;
                  return (
                    <button
                      key={c.value}
                      onClick={() => set("production_capacity", c.value)}
                      className={cn(
                        "rounded-xl border p-3.5 text-left transition-colors",
                        active
                          ? "border-brand-line bg-brand-soft"
                          : "border-line bg-surface-2 hover:border-line-strong",
                      )}
                    >
                      <div className="text-[13px] font-semibold text-ink">{c.label}</div>
                      <p className="mt-0.5 text-[11.5px] leading-relaxed text-ink-muted">
                        {c.hint}
                      </p>
                    </button>
                  );
                })}
              </div>
              <p className="mt-2 text-[11.5px] text-ink-faint">
                Formats needing more than this get ranked down rather than hidden.
              </p>
            </div>

            <div className="mt-6">
              <FieldLabel>Preferred style (optional)</FieldLabel>
              <input
                value={form.preferred_style}
                onChange={(e) => set("preferred_style", e.target.value)}
                placeholder="e.g. dry and direct, no hype, screen-recording heavy"
                className="h-10 w-full rounded-lg border border-line bg-surface-2 px-3 text-[13.5px] text-ink placeholder:text-ink-faint focus:border-line-strong focus:outline-none"
              />
            </div>
          </div>
        ) : null}
      </Card>

      {error ? (
        <p className="mt-3 text-[12.5px]" style={{ color: "var(--color-state-critical)" }}>
          {error}
        </p>
      ) : null}

      <div className="mt-5 flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
        >
          <ArrowLeft className="size-4" /> Back
        </Button>

        <div className="flex items-center gap-2">
          <Link href="/" className="text-[12.5px] text-ink-muted hover:text-ink">
            Skip for now
          </Link>
          {step < STEPS.length - 1 ? (
            <Button variant="primary" onClick={() => setStep((s) => s + 1)} disabled={!canAdvance}>
              Continue <ArrowRight className="size-4" />
            </Button>
          ) : (
            <Button variant="primary" onClick={submit} disabled={!canAdvance || saving}>
              {saving ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Saving…
                </>
              ) : (
                <>
                  Finish <Check className="size-4" />
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-2.5 text-[11px] uppercase tracking-[0.1em] text-ink-muted">{children}</div>
  );
}

function ChipGrid({
  options,
  selected,
  onSelect,
  multi,
}: {
  options: { value: string; label: string }[];
  selected: string[];
  onSelect: (value: string) => void;
  multi?: boolean;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((o) => {
        const active = selected.includes(o.value);
        return (
          <button
            key={o.value}
            onClick={() => onSelect(o.value)}
            aria-pressed={active}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[12.5px] font-medium transition-colors",
              active
                ? "border-brand-line bg-brand-soft text-ink"
                : "border-line bg-surface-2 text-ink-secondary hover:border-line-strong hover:text-ink",
            )}
          >
            {multi && active ? <Check className="size-3" /> : null}
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
