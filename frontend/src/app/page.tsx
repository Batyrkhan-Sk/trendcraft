import Link from "next/link";
import {
  ArrowRight,
  Clapperboard,
  Gauge,
  Layers,
  Play,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { HeroVideo } from "@/components/landing/hero-video";
import { getAnalytics } from "@/lib/api";
import { compact } from "@/lib/format";

export const metadata = {
  title: "TrendCraft — Trend intelligence for short-form video",
  description:
    "Find the content formats that are actually emerging, understand why they work, and turn them into a shot-by-shot recording plan for your niche.",
};

export const dynamic = "force-dynamic";

export default async function LandingPage() {
  // Real corpus numbers rather than invented marketing figures — if the pipeline
  // is empty the strip simply doesn't render.
  const analytics = await getAnalytics();
  const t = analytics.totals ?? {};
  const hasStats = Boolean(t.trends);

  return (
    <div className="relative z-10">
      {/* ---------------------------------------------------------------- hero */}
      <section className="relative isolate overflow-hidden">
        <HeroVideo />

        <header className="relative mx-auto flex max-w-6xl items-center justify-between px-5 py-5 sm:px-8">
          <div className="flex items-center gap-2.5">
            <span className="grid size-7 place-items-center rounded-lg bg-gradient-to-br from-brand to-accent">
              <Sparkles className="size-4 text-canvas" strokeWidth={2.5} />
            </span>
            <span className="text-[15px] font-semibold tracking-tight">TrendCraft</span>
          </div>
          <Link
            href="/dashboard"
            className="rounded-lg border border-line bg-surface/70 px-3.5 py-2 text-[13px] font-medium text-ink backdrop-blur transition-colors hover:border-line-strong"
          >
            Open app
          </Link>
        </header>

        <div className="relative mx-auto max-w-4xl px-5 pb-28 pt-16 text-center sm:px-8 sm:pb-36 sm:pt-24">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-line bg-brand-soft px-3 py-1 text-[11.5px] font-medium text-[#c3b5ff] backdrop-blur">
            <TrendingUp className="size-3.5" />
            Format intelligence, not a hashtag list
          </span>

          <h1 className="mt-6 text-[40px] font-semibold leading-[1.05] tracking-[-0.03em] text-ink sm:text-[62px]">
            Find the format
            <br />
            <span className="gradient-text">before it peaks</span>
          </h1>

          <p className="mx-auto mt-5 max-w-xl text-[15px] leading-relaxed text-ink-secondary sm:text-[16px]">
            TrendCraft watches short-form video across platforms, works out which
            <em className="not-italic text-ink"> content formats </em>
            are genuinely emerging, explains the mechanics that make them work, and
            turns the winners into a shot-by-shot plan for your niche.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-5 text-[14px] font-medium text-white shadow-[0_1px_0_0_#ffffff2e_inset] transition-colors hover:bg-[#8f74ff]"
            >
              Explore trends <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/onboarding"
              className="inline-flex h-11 items-center gap-2 rounded-xl border border-line bg-surface/70 px-5 text-[14px] font-medium text-ink backdrop-blur transition-colors hover:border-line-strong"
            >
              Set up my niche
            </Link>
          </div>

          <p className="mt-4 text-[12px] text-ink-faint">
            No signup. The demo runs on a live corpus.
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------- live corpus */}
      {hasStats ? (
        <section className="relative border-y border-line bg-surface/40">
          <div className="mx-auto grid max-w-6xl grid-cols-2 gap-px px-5 sm:px-8 lg:grid-cols-4">
            <Metric label="Formats tracked" value={compact(t.trends)} />
            <Metric label="Videos analysed" value={compact(t.analyzed_videos ?? t.videos)} />
            <Metric label="Creators tracked" value={compact(t.creators)} />
            <Metric label="Combined reach" value={compact(t.total_reach)} />
          </div>
        </section>
      ) : null}

      {/* ---------------------------------------------------------- how it works */}
      <section className="mx-auto max-w-6xl px-5 py-20 sm:px-8">
        <div className="max-w-2xl">
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-muted">
            How it works
          </div>
          <h2 className="mt-2 text-[28px] font-semibold leading-tight tracking-tight text-ink">
            Views tell you who has an audience.
            <br />
            They don&apos;t tell you what to make.
          </h2>
          <p className="mt-3 text-[14px] leading-relaxed text-ink-secondary">
            Every signal is normalised — by time, by the creator&apos;s own baseline, or
            against the previous window. A 40k-view video from someone who averages 5k
            is stronger evidence than a 2M-view video from someone who always gets 2M.
          </p>
        </div>

        <div className="mt-10 grid gap-3 md:grid-cols-3">
          <Step
            icon={Layers}
            step="01"
            title="Cluster into formats"
            body="Videos are grouped by structure — hook, beats, editing rhythm — not by topic or hashtag. The unit of analysis is the reusable format."
          />
          <Step
            icon={Gauge}
            step="02"
            title="Score what's emerging"
            body="Nine weighted signals separate adoption growth from raw reach, and every score is shown with the components that produced it."
          />
          <Step
            icon={Clapperboard}
            step="03"
            title="Turn it into a shoot"
            body="Pick a format and get a script, shot list, editing blueprint and storyboard — rewritten for your niche, not copied from anyone."
          />
        </div>
      </section>

      {/* ------------------------------------------------------------- closing */}
      <section className="mx-auto max-w-6xl px-5 pb-24 sm:px-8">
        <div className="relative overflow-hidden rounded-2xl border border-brand-line bg-gradient-to-br from-[#7c5cff1a] via-transparent to-[#22d3ee12] p-8 sm:p-12">
          <div className="relative max-w-xl">
            <h2 className="text-[24px] font-semibold leading-tight tracking-tight text-ink sm:text-[30px]">
              Stop guessing what to post
            </h2>
            <p className="mt-3 text-[14px] leading-relaxed text-ink-secondary">
              Tell TrendCraft your niche and it reorders everything around what you
              actually make — then hands you the plan for the next video.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/onboarding"
                className="inline-flex h-11 items-center gap-2 rounded-xl bg-brand px-5 text-[14px] font-medium text-white transition-colors hover:bg-[#8f74ff]"
              >
                Get started <ArrowRight className="size-4" />
              </Link>
              <Link
                href="/discover"
                className="inline-flex h-11 items-center gap-2 rounded-xl border border-line bg-surface px-5 text-[14px] font-medium text-ink transition-colors hover:border-line-strong"
              >
                <Play className="size-3.5" /> Browse formats
              </Link>
            </div>
          </div>
        </div>

        <footer className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-6 text-[12px] text-ink-faint">
          <span>TrendCraft — trend intelligence for short-form video</span>
          <Link href="/dashboard" className="hover:text-ink-secondary">
            Open the app →
          </Link>
        </footer>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-line px-2 py-7 text-center lg:border-l lg:first:border-l-0">
      <div className="tabular text-[26px] font-semibold leading-none tracking-tight text-ink">
        {value}
      </div>
      <div className="mt-2 text-[11px] uppercase tracking-[0.1em] text-ink-muted">{label}</div>
    </div>
  );
}

function Step({
  icon: Icon,
  step,
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string }>;
  step: string;
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-[var(--radius-card)] border border-line bg-surface p-5 transition-colors hover:border-line-strong">
      <div className="flex items-center justify-between">
        <span className="grid size-8 place-items-center rounded-lg bg-brand-soft text-[#c3b5ff]">
          <Icon className="size-4" />
        </span>
        <span className="tabular text-[11px] text-ink-faint">{step}</span>
      </div>
      <h3 className="mt-3.5 text-[15px] font-semibold tracking-tight text-ink">{title}</h3>
      <p className="mt-1.5 text-[13px] leading-relaxed text-ink-secondary">{body}</p>
    </div>
  );
}
