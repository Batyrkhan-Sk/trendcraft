import { Card } from "@/components/ui/primitives";
import { timecode } from "@/lib/format";
import type { FormatSegment } from "@/lib/types";

const SEGMENT_TINTS = [
  "linear-gradient(180deg,#7c5cff33,#7c5cff14)",
  "linear-gradient(180deg,#22d3ee2e,#22d3ee12)",
  "linear-gradient(180deg,#3987e52e,#3987e512)",
  "linear-gradient(180deg,#199e702e,#199e7012)",
  "linear-gradient(180deg,#d959262e,#d9592612)",
  "linear-gradient(180deg,#fab2192e,#fab21912)",
];

/**
 * The format's shape over time.
 *
 * A proportional bar rather than a list, because the point being made is how much
 * of the runtime each beat consumes — a hook that owns 10% of a 30-second video
 * is a different instruction from one that owns 30%.
 */
export function FormatTimeline({ segments }: { segments: FormatSegment[] }) {
  if (!segments.length) {
    return (
      <Card className="p-5 text-[13px] text-ink-faint">
        No structure has been derived for this format yet.
      </Card>
    );
  }

  const total = Math.max(...segments.map((s) => s.end), 1);

  return (
    <div>
      <div className="flex h-11 w-full overflow-hidden rounded-lg border border-line">
        {segments.map((s, i) => {
          const width = ((s.end - s.start) / total) * 100;
          return (
            <div
              key={`${s.label}-${i}`}
              className="relative flex min-w-0 items-center justify-center border-r border-line last:border-r-0"
              style={{ width: `${width}%`, background: SEGMENT_TINTS[i % SEGMENT_TINTS.length] }}
              title={`${timecode(s.start)}–${timecode(s.end)} ${s.label}`}
            >
              <span className="truncate px-2 text-[11.5px] font-medium text-ink">{s.label}</span>
            </div>
          );
        })}
      </div>

      <div className="mt-1.5 flex w-full">
        {segments.map((s, i) => (
          <div
            key={`tick-${i}`}
            className="tabular min-w-0 shrink-0 text-[10.5px] text-ink-faint"
            style={{ width: `${((s.end - s.start) / total) * 100}%` }}
          >
            {timecode(s.start)}
          </div>
        ))}
      </div>

      <ol className="mt-4 flex flex-col gap-2.5">
        {segments.map((s, i) => (
          <li key={`detail-${i}`} className="flex gap-3">
            <span
              className="mt-1.5 h-2 w-2 shrink-0 rounded-full"
              style={{ background: SEGMENT_TINTS[i % SEGMENT_TINTS.length] }}
              aria-hidden
            />
            <div className="min-w-0">
              <div className="flex items-baseline gap-2">
                <span className="text-[13px] font-medium text-ink">{s.label}</span>
                <span className="tabular text-[11px] text-ink-faint">
                  {timecode(s.start)}–{timecode(s.end)}
                </span>
              </div>
              {s.detail ? (
                <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-secondary">{s.detail}</p>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
