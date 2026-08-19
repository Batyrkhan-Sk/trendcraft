"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Hero background loop.
 *
 * The source clip is deliberately louder than the product UI, so three things
 * tame it rather than letting it fight the page:
 *
 * 1. **Saturation and hue pulled toward brand** — the raw magenta/orange sits far
 *    from the violet/cyan the rest of the app uses.
 * 2. **Low opacity plus a gradient fade** into the canvas colour, so the video
 *    dissolves into the page instead of ending on a hard edge.
 * 3. **A hard stop for reduced-motion users** — a full-bleed looping animation is
 *    exactly the case `prefers-reduced-motion` exists for. Those users get the
 *    static poster frame.
 */
export function HeroVideo() {
  const ref = useRef<HTMLVideoElement>(null);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => {
      setReduced(query.matches);
      if (query.matches) ref.current?.pause();
      else void ref.current?.play().catch(() => undefined);
    };
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      <video
        ref={ref}
        // muted + playsInline + autoplay is the only combination browsers will
        // start without a user gesture.
        autoPlay={!reduced}
        muted
        loop
        playsInline
        preload="metadata"
        className="size-full object-cover"
        style={{
          filter: "saturate(2.62) hue-rotate(-32deg) brightness(0.78) contrast(7.05)",
          opacity: 0.5,
        }}
      >
        <source src="/hero-portal.mp4" type="video/mp4" />
      </video>

      {/* Fade the clip into the page background on every edge. */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(120% 90% at 50% 40%, transparent 15%, var(--color-canvas) 78%)",
        }}
      />
      <div
        className="absolute inset-x-0 bottom-0 h-56"
        style={{
          background: "linear-gradient(180deg, transparent, var(--color-canvas))",
        }}
      />
    </div>
  );
}
