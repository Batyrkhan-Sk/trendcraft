export type Platform = "instagram" | "tiktok" | "youtube";
export type TrendStatus = "emerging" | "growing" | "viral" | "declining";
export type Level = "low" | "medium" | "high";

export interface Creator {
  id: string;
  platform: string;
  handle: string;
  display_name: string | null;
  avatar_url: string | null;
  followers: number;
  baseline_median_views: number;
}

export interface VideoAnalysis {
  hook: string | null;
  topic: string | null;
  content_format: string | null;
  narrative_structure: string[];
  speaking_style: string | null;
  visual_style: string | null;
  editing_patterns: string[];
  caption_style: string | null;
  call_to_action: string | null;
  emotional_tone: string | null;
  audio_style: string | null;
  target_audience: string | null;
  main_message: string | null;
  opening_frames: string | null;
  key_moments: { t: number; label: string; why: string }[];
  production_difficulty: string | null;
  extraction_model: string | null;
  is_fallback: boolean;
}

export interface Video {
  id: string;
  platform: string;
  external_id: string;
  url: string;
  thumbnail_url: string | null;
  caption: string | null;
  hashtags: string[];
  published_at: string;
  duration_sec: number;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
  engagement_rate: number;
  niche: string | null;
  language: string | null;
  country: string | null;
  sound_name: string | null;
  creator: Creator | null;
  analysis: VideoAnalysis | null;
  similarity: number | null;
  creator_lift: number | null;
}

export interface ScoreComponent {
  key: string;
  label: string;
  value: number;
  weight: number;
  contribution: number;
}

export interface ScoreBreakdown {
  trend_score?: { total: number; components: ScoreComponent[] };
  opportunity_score?: { total: number; components: ScoreComponent[] };
  inputs?: Record<string, number>;
}

export interface TrendSummary {
  id: string;
  slug: string;
  name: string;
  summary: string;
  format_pattern: string | null;
  status: TrendStatus;
  competition_level: Level;
  trend_score: number;
  opportunity_score: number;
  video_count: number;
  creator_count: number;
  avg_views: number;
  median_views: number;
  avg_engagement_rate: number;
  growth_24h: number;
  growth_7d: number;
  creator_normalized_lift: number;
  median_duration_sec: number;
  platforms: string[];
  niches: string[];
  countries: string[];
  languages: string[];
  content_types: string[];
  production_difficulty: Level;
  adaptability: Level;
  first_seen_at: string | null;
  last_computed_at: string | null;
  sparkline: number[];
  exemplars: Video[];
  relevance_score?: number | null;
  relevance_reasons?: string[] | null;
  feed_score?: number | null;
}

export interface TrendSnapshot {
  captured_at: string;
  video_count: number;
  creator_count: number;
  total_views: number;
  avg_engagement_rate: number;
  trend_score: number;
}

export interface WhyItWorks {
  principle: string;
  title: string;
  detail: string;
}

export interface FormatSegment {
  start: number;
  end: number;
  label: string;
  detail: string;
}

export interface TrendDetail extends TrendSummary {
  why_it_works: WhyItWorks[];
  format_structure: FormatSegment[];
  common_elements: string[];
  score_breakdown: ScoreBreakdown;
  opportunity_explanation: string[];
  snapshots: TrendSnapshot[];
  videos: Video[];
}

export interface TrendListResponse {
  items: TrendSummary[];
  total: number;
  facets: Record<string, string[]>;
}

export interface ScriptBeat {
  start: number;
  end: number;
  label: string;
  script: string;
  direction: string;
}

export interface Shot {
  index: number;
  label: string;
  start: number;
  end: number;
  shot_type: string;
  camera: string;
  action: string;
  spoken?: string | null;
  on_screen_text?: string | null;
  lighting?: string | null;
  editing: string;
  storyboard_frame: string;
}

export interface StoryboardFrame {
  frame: number;
  timecode: string;
  start: number;
  end: number;
  label: string;
  shot_type: string;
  description: string;
  on_screen_text: string;
}

export interface RecordingGuide {
  shots: Shot[];
  camera_setup: {
    talking_head?: string;
    screen_recording?: string;
    b_roll?: string[];
    lighting?: string;
    audio?: string;
    angles?: string[];
  };
  editing_blueprint: {
    cuts?: string;
    zooms?: string[];
    text_overlays?: string[];
    subtitles?: string;
    speed_changes?: string[];
    transitions?: string[];
    sound_design?: string;
  };
  gear: string[];
  common_mistakes: string[];
  estimated_shoot_minutes?: number | null;
  estimated_edit_minutes?: number | null;
  storyboard: StoryboardFrame[];
  generator_model?: string | null;
}

export interface Scenario {
  id: string | null;
  trend_id: string | null;
  trend_name: string | null;
  title: string;
  hook: string;
  concept: string;
  script_structure: ScriptBeat[];
  caption: string | null;
  hashtags: string[];
  call_to_action: string;
  suggested_duration_sec: number;
  suggested_audio: string | null;
  difficulty: Level;
  why_it_could_work: string[];
  derived_from: string | null;
  recording_guide: RecordingGuide | null;
  platform: string | null;
  niche: string | null;
  goal: string | null;
  kind: string;
  generator_model: string | null;
  created_at: string | null;
}

export interface Profile {
  id?: string | null;
  niche: string | null;
  sub_niches: string[];
  audience: string | null;
  audience_age: string | null;
  platforms: string[];
  content_types: string[];
  goal: string | null;
  languages: string[];
  country: string | null;
  preferred_style: string | null;
  production_capacity: Level | null;
  notes: string | null;
}

export interface SavedItem {
  id: number;
  entity_type: "trend" | "scenario" | "video";
  entity_id: string;
  note: string | null;
  created_at: string;
  trend: TrendSummary | null;
  scenario: Scenario | null;
}

export interface Dashboard {
  rising_fast: TrendSummary[];
  best_opportunities: TrendSummary[];
  in_your_niche: TrendSummary[];
  cross_platform: TrendSummary[];
  recommended_scenarios: Scenario[];
  recently_saved: SavedItem[];
  stats: {
    tracked_trends: number;
    videos_analyzed: number;
    creators_tracked: number;
    rising_count: number;
    viral_count: number;
    avg_opportunity: number;
    profile_complete: boolean;
  };
}

export interface Analytics {
  totals: Record<string, number>;
  by_platform: { platform: string; trends: number; videos: number }[];
  by_status: { status: TrendStatus; count: number }[];
  by_niche: { niche: string; trends: number; videos: number; avg_opportunity: number }[];
  top_movers: TrendSummary[];
  score_distribution: { bucket: string; count: number }[];
  adoption_timeline: { date: string; videos: number; creators: number }[];
}
