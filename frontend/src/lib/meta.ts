import {
  Activity,
  Flame,
  Sparkles,
  TrendingDown,
  type LucideIcon,
} from "lucide-react";
import type { Level, TrendStatus } from "./types";

/**
 * Trend lifecycle presentation.
 *
 * These use the reserved status colours from the data-viz palette. Green and red
 * are not separable under deuteranopia, so every status is rendered as an
 * icon + text pill — colour never carries the meaning on its own.
 */
export const STATUS_META: Record<
  TrendStatus,
  { label: string; icon: LucideIcon; color: string; tint: string; ring: string; blurb: string }
> = {
  emerging: {
    label: "Emerging",
    icon: Sparkles,
    color: "var(--color-state-new)",
    tint: "#3987e51f",
    ring: "#3987e547",
    blurb: "Early adoption, low saturation. The widest window to enter.",
  },
  growing: {
    label: "Growing",
    icon: Activity,
    color: "var(--color-state-good)",
    tint: "#0ca30c1f",
    ring: "#0ca30c47",
    blurb: "Creator adoption is accelerating and reach is still climbing.",
  },
  viral: {
    label: "Viral",
    icon: Flame,
    color: "var(--color-state-warning)",
    tint: "#fab2191f",
    ring: "#fab21947",
    blurb: "Peak reach, but crowded. Differentiation matters more than speed.",
  },
  declining: {
    label: "Declining",
    icon: TrendingDown,
    color: "var(--color-state-critical)",
    tint: "#d03b3b1f",
    ring: "#d03b3b47",
    blurb: "Adoption has turned over. Reach per video lags the numbers shown.",
  },
};

export const LEVEL_META: Record<Level, { label: string; dots: number; color: string }> = {
  low: { label: "Low", dots: 1, color: "var(--color-state-good)" },
  medium: { label: "Medium", dots: 2, color: "var(--color-state-warning)" },
  high: { label: "High", dots: 3, color: "var(--color-state-critical)" },
};

export const PLATFORM_META: Record<string, { label: string; short: string }> = {
  tiktok: { label: "TikTok", short: "TT" },
  instagram: { label: "Instagram", short: "IG" },
  youtube: { label: "YouTube", short: "YT" },
};

export const platformLabel = (p: string) => PLATFORM_META[p]?.label ?? p;

/** Categorical series colours, assigned in fixed order and never cycled. */
export const SERIES = [
  "var(--color-series-1)",
  "var(--color-series-2)",
  "var(--color-series-3)",
] as const;

export const GOALS = [
  { value: "audience_growth", label: "Grow my audience" },
  { value: "brand_growth", label: "Build a personal brand" },
  { value: "sales", label: "Drive sales or signups" },
  { value: "authority", label: "Become a known authority" },
  { value: "community", label: "Build a community" },
];

export const CONTENT_TYPES = [
  "tutorial",
  "experiment",
  "commentary",
  "vlog",
  "transformation",
  "listicle",
  "breakdown",
  "review",
];

export const NICHES = [
  "ai",
  "technology",
  "productivity",
  "business",
  "startups",
  "marketing",
  "finance",
  "education",
  "fitness",
  "health",
  "food",
  "beauty",
  "fashion",
  "design",
  "gaming",
  "travel",
  "lifestyle",
];

export const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "de", label: "German" },
  { value: "fr", label: "French" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "pl", label: "Polish" },
];
