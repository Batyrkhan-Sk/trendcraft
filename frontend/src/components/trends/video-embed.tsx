"use client";

import { useState } from "react";
import { ExternalLink, Play } from "lucide-react";
import { cn, compact } from "@/lib/format";
import type { Video } from "@/lib/types";

/**
 * Inline playback for a collected video.
 *
 * Facade pattern, deliberately: the thumbnail is a plain image and the real
 * player iframe is only mounted once the viewer presses play. A grid of ten
 * eagerly-loaded YouTube iframes costs several megabytes, janks scrolling, and
 * sets tracking cookies for videos nobody watched.
 *
 * Playback always goes through the platform's official embed rather than a
 * proxied media file — the creator keeps their view count and their terms of
 * service stay intact.
 */
export function embedUrl(video: Video): string | null {
  const id = video.external_id;
  if (!id) return null;

  switch (video.platform) {
    case "youtube":
      // nocookie host: no tracking cookie until playback actually starts.
      return `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&modestbranding=1&playsinline=1`;
    case "tiktok":
      return `https://www.tiktok.com/embed/v2/${id}`;
    case "instagram":
      return `https://www.instagram.com/reel/${id}/embed`;
    default:
      return null;
  }
}

export function VideoEmbed({
  video,
  className,
  showStats = true,
}: {
  video: Video;
  className?: string;
  showStats?: boolean;
}) {
  const [playing, setPlaying] = useState(false);
  const src = embedUrl(video);
  const canPlay = Boolean(src);

  return (
    <div className={cn("relative aspect-[9/16] w-full overflow-hidden bg-surface-2", className)}>
      {playing && src ? (
        <iframe
          src={src}
          title={video.analysis?.hook ?? video.caption ?? "Video"}
          className="absolute inset-0 size-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
        />
      ) : (
        <button
          type="button"
          onClick={() => canPlay && setPlaying(true)}
          className="group absolute inset-0 size-full cursor-pointer"
          aria-label={canPlay ? "Play video" : "Open video on platform"}
        >
          {video.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={video.thumbnail_url}
              alt=""
              loading="lazy"
              // YouTube returns 16:9 thumbnails even for Shorts; cover-crop to
              // vertical so the grid stays uniform instead of letterboxing.
              className="size-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
            />
          ) : (
            <div className="flex size-full items-end p-3">
              <p className="line-clamp-4 text-left text-[12.5px] leading-snug text-ink-secondary">
                {video.analysis?.hook ?? video.caption ?? "No preview available"}
              </p>
            </div>
          )}

          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-canvas/90 via-canvas/10 to-canvas/30" />

          <span className="pointer-events-none absolute inset-0 grid place-items-center">
            <span className="grid size-12 place-items-center rounded-full border border-white/20 bg-canvas/60 backdrop-blur transition-transform duration-200 group-hover:scale-110">
              <Play className="size-5 translate-x-px fill-white text-white" />
            </span>
          </span>

          {showStats ? (
            <span className="pointer-events-none absolute inset-x-0 bottom-0 flex items-end justify-between gap-2 p-2.5">
              <span className="tabular text-[12px] font-semibold text-white drop-shadow">
                {compact(video.views)} views
              </span>
              {video.creator_lift && video.creator_lift >= 1.5 ? (
                <span
                  className="tabular rounded-md border px-1.5 py-0.5 text-[10.5px] font-medium backdrop-blur"
                  style={{
                    color: "var(--color-state-good)",
                    borderColor: "#0ca30c47",
                    background: "#0ca30c1f",
                  }}
                  title="Views as a multiple of this creator's typical performance"
                >
                  {video.creator_lift.toFixed(1)}× avg
                </span>
              ) : null}
            </span>
          ) : null}
        </button>
      )}

      {!canPlay ? (
        <a
          href={video.url}
          target="_blank"
          rel="noopener noreferrer"
          className="absolute right-2 top-2 grid size-7 place-items-center rounded-md bg-canvas/70 text-ink-secondary backdrop-blur transition-colors hover:text-ink"
          aria-label="Open on platform"
        >
          <ExternalLink className="size-3.5" />
        </a>
      ) : null}
    </div>
  );
}
