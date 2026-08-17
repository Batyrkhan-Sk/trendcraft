import { ExternalLink, Heart, MessageCircle, Share2 } from "lucide-react";
import { VideoEmbed } from "@/components/trends/video-embed";
import { Badge, Card } from "@/components/ui/primitives";
import { compact, duration, percent, relativeTime } from "@/lib/format";
import { platformLabel } from "@/lib/meta";
import type { Video } from "@/lib/types";

/**
 * One analysed video, playable in place.
 *
 * The player is a facade — see :file:`video-embed.tsx`. Nothing is proxied or
 * rehosted; playback runs through the platform's own embed so the creator keeps
 * the view.
 */
export function VideoCard({ video, showAnalysis }: { video: Video; showAnalysis?: boolean }) {
  const a = video.analysis;

  return (
    <Card hover className="flex flex-col overflow-hidden">
      <div className="relative">
        <VideoEmbed video={video} />
        <div className="pointer-events-none absolute left-2 top-2 flex items-center gap-1.5">
          <Badge tone="outline" className="bg-canvas/70 backdrop-blur">
            {platformLabel(video.platform)}
          </Badge>
          <span className="tabular rounded-md bg-canvas/70 px-1.5 py-0.5 text-[10.5px] text-ink-secondary backdrop-blur">
            {duration(video.duration_sec)}
          </span>
        </div>
      </div>

      <div className="flex min-w-0 flex-1 flex-col p-3">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-[12px] font-medium text-ink">
            @{video.creator?.handle ?? "unknown"}
          </span>
          <a
            href={video.url}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-ink-muted transition-colors hover:text-ink"
            aria-label="Open on platform"
          >
            <ExternalLink className="size-3.5" />
          </a>
        </div>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-ink-faint">
          <span>{compact(video.creator?.followers ?? 0)} followers</span>
          <span>·</span>
          <span>{relativeTime(video.published_at)}</span>
        </div>

        {a?.hook ? (
          <p className="mt-2 line-clamp-2 text-[12.5px] leading-snug text-ink-secondary">
            {a.hook}
          </p>
        ) : null}

        <div className="mt-2.5 flex items-center gap-3 border-t border-line-soft pt-2.5 text-[11px] text-ink-muted">
          <span className="tabular inline-flex items-center gap-1">
            <Heart className="size-3" /> {compact(video.likes)}
          </span>
          <span className="tabular inline-flex items-center gap-1">
            <MessageCircle className="size-3" /> {compact(video.comments)}
          </span>
          <span className="tabular inline-flex items-center gap-1">
            <Share2 className="size-3" /> {compact(video.shares)}
          </span>
          <span className="tabular ml-auto font-medium text-ink-secondary">
            {percent(video.engagement_rate, 1)}
          </span>
        </div>

        {showAnalysis && a ? (
          <div className="mt-2.5 flex flex-wrap gap-1">
            {a.emotional_tone ? <Badge>{a.emotional_tone}</Badge> : null}
            {a.narrative_structure.slice(0, 3).map((b) => (
              <Badge key={b} tone="outline">
                {b}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
    </Card>
  );
}
