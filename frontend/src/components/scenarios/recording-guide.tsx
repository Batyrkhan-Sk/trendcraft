import {
  AlertTriangle,
  Camera,
  Clapperboard,
  Film,
  Lightbulb,
  Mic,
  Package,
  Scissors,
  Sparkles,
  Type,
} from "lucide-react";
import { Badge, Card, Divider, SectionLabel } from "@/components/ui/primitives";
import { timecode } from "@/lib/format";
import type { RecordingGuide } from "@/lib/types";

/**
 * "How to Record This Video".
 *
 * Structured as a shot list first, then the setup and edit blueprints, then the
 * storyboard — the order a creator actually needs them in when they sit down to
 * film, rather than the order the model generates them.
 */
export function RecordingGuidePanel({ guide }: { guide: RecordingGuide }) {
  return (
    <div className="flex flex-col gap-8">
      <ShotList guide={guide} />
      <Storyboard guide={guide} />

      <div className="grid gap-3 lg:grid-cols-2">
        <CameraSetup guide={guide} />
        <EditingBlueprint guide={guide} />
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {guide.gear?.length ? (
          <Card className="p-4">
            <div className="flex items-center gap-2">
              <Package className="size-3.5 text-ink-muted" />
              <SectionLabel>Gear</SectionLabel>
            </div>
            <ul className="mt-3 flex flex-wrap gap-1.5">
              {guide.gear.map((g) => (
                <li key={g}>
                  <Badge tone="outline">{g}</Badge>
                </li>
              ))}
            </ul>
            {(guide.estimated_shoot_minutes || guide.estimated_edit_minutes) && (
              <>
                <Divider className="my-3.5" />
                <div className="flex gap-6">
                  {guide.estimated_shoot_minutes ? (
                    <div>
                      <div className="text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                        Shoot
                      </div>
                      <div className="tabular mt-0.5 text-[14px] font-semibold text-ink">
                        ~{guide.estimated_shoot_minutes} min
                      </div>
                    </div>
                  ) : null}
                  {guide.estimated_edit_minutes ? (
                    <div>
                      <div className="text-[11px] uppercase tracking-[0.06em] text-ink-muted">
                        Edit
                      </div>
                      <div className="tabular mt-0.5 text-[14px] font-semibold text-ink">
                        ~{guide.estimated_edit_minutes} min
                      </div>
                    </div>
                  ) : null}
                </div>
              </>
            )}
          </Card>
        ) : null}

        {guide.common_mistakes?.length ? (
          <Card className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-3.5" style={{ color: "var(--color-state-warning)" }} />
              <SectionLabel>What kills this format</SectionLabel>
            </div>
            <ul className="mt-3 flex flex-col gap-2">
              {guide.common_mistakes.map((m) => (
                <li key={m} className="flex gap-2.5 text-[12.5px] leading-relaxed text-ink-secondary">
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-[#fab219]" aria-hidden />
                  {m}
                </li>
              ))}
            </ul>
          </Card>
        ) : null}
      </div>
    </div>
  );
}

function ShotList({ guide }: { guide: RecordingGuide }) {
  if (!guide.shots?.length) return null;
  return (
    <section>
      <div className="flex items-center gap-2">
        <Clapperboard className="size-3.5 text-ink-muted" />
        <SectionLabel>Shot-by-shot plan</SectionLabel>
      </div>
      <p className="mt-1 text-[12.5px] text-ink-faint">
        {guide.shots.length} shots. Film them in any order — the timings are for the edit.
      </p>

      <ol className="mt-3 flex flex-col gap-2.5">
        {guide.shots.map((shot) => (
          <li key={shot.index}>
            <Card className="overflow-hidden">
              <div className="flex flex-col gap-0 sm:flex-row">
                {/* Timing rail: the shot's position in the finished video. */}
                <div className="flex shrink-0 items-center gap-3 border-b border-line bg-surface-2 px-4 py-3 sm:w-[132px] sm:flex-col sm:items-start sm:justify-center sm:border-b-0 sm:border-r">
                  <span className="grid size-7 place-items-center rounded-lg bg-brand-soft text-[12px] font-semibold text-[#c3b5ff]">
                    {shot.index}
                  </span>
                  <div>
                    <div className="tabular text-[12px] font-medium text-ink">
                      {timecode(shot.start)}–{timecode(shot.end)}
                    </div>
                    <div className="text-[10.5px] text-ink-faint">
                      {(shot.end - shot.start).toFixed(0)}s
                    </div>
                  </div>
                </div>

                <div className="min-w-0 flex-1 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-[13.5px] font-semibold text-ink">{shot.label}</h4>
                    <Badge>{shot.shot_type}</Badge>
                  </div>

                  <div className="mt-2.5 grid gap-2.5 sm:grid-cols-2">
                    <Detail icon={Camera} label="Camera" value={shot.camera} />
                    <Detail icon={Film} label="Action" value={shot.action} />
                    {shot.lighting ? (
                      <Detail icon={Lightbulb} label="Lighting" value={shot.lighting} />
                    ) : null}
                    <Detail icon={Scissors} label="Editing" value={shot.editing} />
                  </div>

                  {shot.spoken ? (
                    <div className="mt-3 rounded-lg border border-line bg-surface-2 px-3 py-2.5">
                      <div className="flex items-center gap-1.5 text-[10.5px] uppercase tracking-[0.08em] text-ink-muted">
                        <Mic className="size-3" /> Say this
                      </div>
                      <p className="mt-1 text-[13px] leading-relaxed text-ink">“{shot.spoken}”</p>
                    </div>
                  ) : null}

                  {shot.on_screen_text ? (
                    <div className="mt-2 flex items-start gap-1.5 text-[11.5px] text-ink-secondary">
                      <Type className="mt-0.5 size-3 shrink-0 text-ink-muted" />
                      <span>
                        <span className="text-ink-muted">On screen: </span>
                        {shot.on_screen_text}
                      </span>
                    </div>
                  ) : null}
                </div>
              </div>
            </Card>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Detail({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-0">
      <div className="flex items-center gap-1.5 text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
        <Icon className="size-3" />
        {label}
      </div>
      <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-secondary">{value}</p>
    </div>
  );
}

/**
 * Frame-by-frame planning view.
 *
 * Each frame is drawn as a composed placeholder rather than a generated image:
 * the useful information is the composition — where the subject sits, what fills
 * the frame, what text is burned in — and that reads more clearly as a diagram
 * than as an AI-rendered picture that would only approximate it.
 */
function Storyboard({ guide }: { guide: RecordingGuide }) {
  if (!guide.storyboard?.length) return null;

  return (
    <section>
      <div className="flex items-center gap-2">
        <Sparkles className="size-3.5 text-ink-muted" />
        <SectionLabel>Storyboard</SectionLabel>
      </div>
      <p className="mt-1 text-[12.5px] text-ink-faint">
        Plan the composition before you film. One frame per shot.
      </p>

      <div className="rail mt-3 -mx-1 flex gap-3 overflow-x-auto px-1 pb-2">
        {guide.storyboard.map((frame) => (
          <Card key={frame.frame} className="w-[210px] shrink-0 overflow-hidden">
            <div className="relative aspect-[9/16] w-full bg-gradient-to-b from-surface-3 to-surface-2">
              <FrameSketch shotType={frame.shot_type} onScreenText={frame.on_screen_text} />
              <div className="absolute left-2 top-2 rounded bg-canvas/80 px-1.5 py-0.5 text-[10px] font-medium tabular text-ink">
                {frame.timecode}
              </div>
              <div className="absolute right-2 top-2 rounded bg-canvas/80 px-1.5 py-0.5 text-[10px] font-medium text-ink-secondary">
                #{frame.frame}
              </div>
            </div>
            <div className="p-2.5">
              <div className="truncate text-[12px] font-medium text-ink">{frame.label}</div>
              <p className="mt-1 line-clamp-4 text-[11.5px] leading-relaxed text-ink-secondary">
                {frame.description}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

/** Schematic of one frame's composition, keyed off the shot type. */
function FrameSketch({ shotType, onScreenText }: { shotType: string; onScreenText: string }) {
  const t = (shotType || "").toLowerCase();
  // Order matters: "split screen" contains "screen", so the split case has to be
  // tested before the screen-recording case or every split renders as a capture.
  const isSplit = t.includes("split");
  const isScreen = !isSplit && t.includes("screen");
  const isWide = t.includes("wide") || t.includes("b-roll") || t.includes("top-down");
  const isClose = t.includes("close");

  return (
    <svg viewBox="0 0 90 160" className="absolute inset-0 size-full" aria-hidden>
      <rect x="0" y="0" width="90" height="160" fill="none" />

      {isScreen ? (
        <>
          <rect x="8" y="34" width="74" height="52" rx="3" fill="#ffffff0e" stroke="#ffffff22" />
          <rect x="12" y="39" width="30" height="3" rx="1.5" fill="#ffffff2e" />
          <rect x="12" y="46" width="52" height="3" rx="1.5" fill="#ffffff1c" />
          <rect x="12" y="53" width="44" height="3" rx="1.5" fill="#ffffff1c" />
          <circle cx="66" cy="70" r="2.5" fill="#7c5cff" />
          <circle cx="70" cy="112" r="12" fill="#ffffff12" stroke="#ffffff26" />
          <circle cx="70" cy="108" r="4" fill="#ffffff2e" />
        </>
      ) : isSplit ? (
        <>
          <rect x="6" y="30" width="37" height="70" rx="3" fill="#ffffff0c" stroke="#ffffff22" />
          <rect x="47" y="30" width="37" height="70" rx="3" fill="#7c5cff1f" stroke="#7c5cff45" />
          <rect x="12" y="104" width="25" height="4" rx="2" fill="#ffffff26" />
          <rect x="53" y="104" width="25" height="4" rx="2" fill="#7c5cff66" />
        </>
      ) : isWide ? (
        <>
          <rect x="6" y="46" width="78" height="52" rx="3" fill="#ffffff0c" stroke="#ffffff22" />
          <circle cx="30" cy="72" r="9" fill="#ffffff1f" />
          <rect x="46" y="64" width="30" height="16" rx="2" fill="#ffffff14" />
        </>
      ) : (
        // Talking head — head-and-shoulders, sized by how close the framing is.
        <>
          <circle cx="45" cy={isClose ? 62 : 70} r={isClose ? 22 : 16} fill="#ffffff14" stroke="#ffffff26" />
          <circle cx={isClose ? 38 : 40} cy={isClose ? 58 : 67} r="2" fill="#ffffff3d" />
          <circle cx={isClose ? 52 : 50} cy={isClose ? 58 : 67} r="2" fill="#ffffff3d" />
          <path
            d={isClose ? "M20 108 Q45 84 70 108 L70 130 L20 130 Z" : "M26 104 Q45 88 64 104 L64 126 L26 126 Z"}
            fill="#ffffff0f"
            stroke="#ffffff1c"
          />
        </>
      )}

      {onScreenText ? (
        <>
          <rect x="10" y="132" width="70" height="7" rx="3.5" fill="#ffffff2e" />
          <rect x="20" y="143" width="50" height="5" rx="2.5" fill="#ffffff1c" />
        </>
      ) : null}
    </svg>
  );
}

function CameraSetup({ guide }: { guide: RecordingGuide }) {
  const s = guide.camera_setup ?? {};
  const rows: [React.ComponentType<{ className?: string }>, string, string | undefined][] = [
    [Camera, "Talking head", s.talking_head],
    [Film, "Screen recording", s.screen_recording],
    [Lightbulb, "Lighting", s.lighting],
    [Mic, "Audio", s.audio],
  ];

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2">
        <Camera className="size-3.5 text-ink-muted" />
        <SectionLabel>Camera & framing</SectionLabel>
      </div>
      <div className="mt-3 flex flex-col gap-3">
        {rows
          .filter(([, , value]) => value)
          .map(([Icon, label, value]) => (
            <div key={label}>
              <div className="flex items-center gap-1.5 text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">
                <Icon className="size-3" />
                {label}
              </div>
              <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-secondary">{value}</p>
            </div>
          ))}
      </div>

      {s.b_roll?.length ? (
        <>
          <Divider className="my-3.5" />
          <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">B-roll to grab</div>
          <ul className="mt-1.5 flex flex-col gap-1.5">
            {s.b_roll.map((b) => (
              <li key={b} className="flex gap-2 text-[12.5px] leading-relaxed text-ink-secondary">
                <span className="mt-1.5 size-1 shrink-0 rounded-full bg-line-strong" aria-hidden />
                {b}
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {s.angles?.length ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {s.angles.map((a) => (
            <Badge key={a} tone="outline">
              {a}
            </Badge>
          ))}
        </div>
      ) : null}
    </Card>
  );
}

function EditingBlueprint({ guide }: { guide: RecordingGuide }) {
  const e = guide.editing_blueprint ?? {};
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2">
        <Scissors className="size-3.5 text-ink-muted" />
        <SectionLabel>Editing blueprint</SectionLabel>
      </div>

      <div className="mt-3 flex flex-col gap-3">
        {e.cuts ? <Line label="Cuts" value={e.cuts} /> : null}
        {e.subtitles ? <Line label="Subtitles" value={e.subtitles} /> : null}
        {e.sound_design ? <Line label="Sound design" value={e.sound_design} /> : null}
      </div>

      {[
        ["Zooms", e.zooms],
        ["Text overlays", e.text_overlays],
        ["Speed changes", e.speed_changes],
        ["Transitions", e.transitions],
      ]
        .filter(([, items]) => Array.isArray(items) && items.length)
        .map(([label, items]) => (
          <div key={label as string} className="mt-3">
            <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">{label}</div>
            <ul className="mt-1.5 flex flex-col gap-1.5">
              {(items as string[]).map((item) => (
                <li key={item} className="flex gap-2 text-[12.5px] leading-relaxed text-ink-secondary">
                  <span className="mt-1.5 size-1 shrink-0 rounded-full bg-line-strong" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
    </Card>
  );
}

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10.5px] uppercase tracking-[0.06em] text-ink-muted">{label}</div>
      <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-secondary">{value}</p>
    </div>
  );
}
