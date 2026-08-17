import Link from "next/link";
import { ArrowUpRight, Clapperboard, Clock, Hash, Quote, Sparkles } from "lucide-react";
import { Badge, Card, Divider, SectionLabel } from "@/components/ui/primitives";
import { LEVEL_META, platformLabel } from "@/lib/meta";
import { duration, timecode, titleCase } from "@/lib/format";
import type { Scenario } from "@/lib/types";

/** Compact entry for lists and rails. */
export function ScenarioMiniCard({ scenario }: { scenario: Scenario }) {
  return (
    <Link href={`/scenarios/${scenario.id}`}>
      <Card hover className="group p-3.5">
        <div className="flex items-start justify-between gap-2">
          <h3 className="line-clamp-2 text-[13px] font-semibold leading-snug text-ink">
            {scenario.title}
          </h3>
          <ArrowUpRight className="mt-0.5 size-3.5 shrink-0 text-ink-faint transition-transform group-hover:translate-x-0.5 group-hover:text-ink-secondary" />
        </div>
        <p className="mt-1.5 line-clamp-2 text-[12px] leading-relaxed text-ink-secondary">
          {scenario.concept}
        </p>
        <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-faint">
          <span className="tabular inline-flex items-center gap-1">
            <Clock className="size-3" /> {duration(scenario.suggested_duration_sec)}
          </span>
          <span
            className="inline-flex items-center gap-1"
            style={{ color: LEVEL_META[scenario.difficulty].color }}
          >
            {LEVEL_META[scenario.difficulty].label} effort
          </span>
          {scenario.recording_guide?.shots?.length ? (
            <span className="inline-flex items-center gap-1">
              <Clapperboard className="size-3" /> {scenario.recording_guide.shots.length} shots
            </span>
          ) : null}
        </div>
      </Card>
    </Link>
  );
}

/** Full scenario body: hook, concept, timed script, caption and rationale. */
export function ScenarioDetail({ scenario }: { scenario: Scenario }) {
  return (
    <div className="flex flex-col gap-6">
      <Card className="overflow-hidden">
        <div className="border-b border-line bg-gradient-to-br from-[#7c5cff14] to-transparent p-5">
          <div className="flex items-center gap-1.5 text-[10.5px] uppercase tracking-[0.1em] text-[#a99bff]">
            <Quote className="size-3" /> The hook
          </div>
          <p className="mt-2 text-[19px] font-semibold leading-snug tracking-tight text-ink">
            “{scenario.hook}”
          </p>
          <p className="mt-1.5 text-[11.5px] text-ink-faint">
            Speak this in under three seconds. No greeting before it.
          </p>
        </div>

        <div className="p-5">
          <SectionLabel>Concept</SectionLabel>
          <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-secondary">
            {scenario.concept}
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px]">
            <Meta label="Duration" value={duration(scenario.suggested_duration_sec)} />
            <Meta label="Effort" value={`${LEVEL_META[scenario.difficulty].label}`} />
            {scenario.platform ? (
              <Meta label="Platform" value={platformLabel(scenario.platform)} />
            ) : null}
            {scenario.niche ? <Meta label="Niche" value={titleCase(scenario.niche)} /> : null}
          </div>
        </div>
      </Card>

      {scenario.script_structure?.length ? (
        <section>
          <SectionLabel>Script</SectionLabel>
          <p className="mt-1 text-[12.5px] text-ink-faint">
            Words to say, and what to show while saying them.
          </p>
          <div className="mt-3 flex flex-col gap-2">
            {scenario.script_structure.map((beat, i) => (
              <Card key={i} className="flex flex-col gap-0 p-0 sm:flex-row">
                <div className="flex shrink-0 items-center gap-2 border-b border-line bg-surface-2 px-4 py-2.5 sm:w-[124px] sm:flex-col sm:items-start sm:justify-center sm:border-b-0 sm:border-r">
                  <span className="tabular text-[12px] font-medium text-ink">
                    {timecode(beat.start)}–{timecode(beat.end)}
                  </span>
                  <span className="text-[11px] text-ink-muted">{beat.label}</span>
                </div>
                <div className="min-w-0 flex-1 p-4">
                  {/* Only add quotes when the beat is verbatim speech. Guidance
                      text carries its own example quotes, and wrapping those
                      again produces doubled marks. */}
                  <p className="text-[13.5px] leading-relaxed text-ink">
                    {/[“"]/.test(beat.script) ? beat.script : `“${beat.script}”`}
                  </p>
                  {beat.direction ? (
                    <p className="mt-1.5 text-[12px] leading-relaxed text-ink-muted">
                      <span className="text-ink-faint">Show: </span>
                      {beat.direction}
                    </p>
                  ) : null}
                </div>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      <div className="grid gap-3 lg:grid-cols-2">
        <Card className="p-4">
          <SectionLabel>Publish kit</SectionLabel>
          <div className="mt-3 flex flex-col gap-3">
            {scenario.caption ? (
              <div>
                <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
                  Caption
                </div>
                <p className="mt-1 text-[12.5px] leading-relaxed text-ink-secondary">
                  {scenario.caption}
                </p>
              </div>
            ) : null}
            <div>
              <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
                Call to action
              </div>
              <p className="mt-1 text-[12.5px] leading-relaxed text-ink-secondary">
                {scenario.call_to_action}
              </p>
            </div>
            {scenario.suggested_audio ? (
              <div>
                <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">Audio</div>
                <p className="mt-1 text-[12.5px] leading-relaxed text-ink-secondary">
                  {scenario.suggested_audio}
                </p>
              </div>
            ) : null}
          </div>
          {scenario.hashtags?.length ? (
            <>
              <Divider className="my-3.5" />
              <div className="flex flex-wrap items-center gap-1.5">
                <Hash className="size-3 text-ink-muted" />
                {scenario.hashtags.map((h) => (
                  <Badge key={h} tone="outline">
                    {h.replace(/^#/, "")}
                  </Badge>
                ))}
              </div>
            </>
          ) : null}
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2">
            <Sparkles className="size-3.5 text-ink-muted" />
            <SectionLabel>Why this could work</SectionLabel>
          </div>
          <ul className="mt-3 flex flex-col gap-2">
            {scenario.why_it_could_work.map((reason) => (
              <li key={reason} className="flex gap-2.5 text-[12.5px] leading-relaxed text-ink-secondary">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-[#7c5cff]" aria-hidden />
                {reason}
              </li>
            ))}
          </ul>
          {scenario.derived_from ? (
            <>
              <Divider className="my-3.5" />
              <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
                Derived from
              </div>
              <p className="mt-1 font-mono text-[12px] text-[#a99bff]">{scenario.derived_from}</p>
              {scenario.trend_id ? (
                <Link
                  href={`/trends/${scenario.trend_id}`}
                  className="mt-2 inline-flex items-center gap-1 text-[11.5px] text-ink-muted hover:text-ink"
                >
                  View the source trend <ArrowUpRight className="size-3" />
                </Link>
              ) : null}
            </>
          ) : null}
        </Card>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-baseline gap-1.5">
      <span className="text-[11px] uppercase tracking-[0.06em] text-ink-muted">{label}</span>
      <span className="font-medium text-ink">{value}</span>
    </span>
  );
}
