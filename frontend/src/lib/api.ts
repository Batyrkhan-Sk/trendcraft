import type {
  Analytics,
  Dashboard,
  Profile,
  SavedItem,
  Scenario,
  TrendDetail,
  TrendListResponse,
} from "./types";

/**
 * Server components talk to the API over the internal network (`API_URL`);
 * anything running in the browser uses the published origin. Keeping both means
 * the same helpers work in either context without a proxy hop.
 */
const SERVER_BASE = process.env.API_URL ?? "http://localhost:8010/api/v1";
const BROWSER_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010/api/v1";

export const apiBase = () => (typeof window === "undefined" ? SERVER_BASE : BROWSER_BASE);

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

type Options = RequestInit & { revalidate?: number };

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const { revalidate, ...init } = options;
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      // Single-tenant demo identity. Replace with a session token when auth lands.
      "X-User-Email": "demo@trendcraft.app",
      ...(init.headers ?? {}),
    },
    // Trend data changes on a pipeline cadence, not per request.
    next: revalidate === undefined ? { revalidate: 30 } : { revalidate },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(body || res.statusText, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** Swallows connection failures so a page can render an empty state instead of a crash. */
export async function apiSafe<T>(path: string, fallback: T, options?: Options): Promise<T> {
  try {
    return await api<T>(path, options);
  } catch {
    return fallback;
  }
}

export const EMPTY_TRENDS: TrendListResponse = { items: [], total: 0, facets: {} };

export const getTrends = (query = "") =>
  apiSafe<TrendListResponse>(`/trends${query}`, EMPTY_TRENDS);

export const getTrend = (ref: string) => api<TrendDetail>(`/trends/${ref}`);

export const getDashboard = () =>
  apiSafe<Dashboard>("/dashboard", {
    rising_fast: [],
    best_opportunities: [],
    in_your_niche: [],
    cross_platform: [],
    recommended_scenarios: [],
    recently_saved: [],
    stats: {
      tracked_trends: 0,
      videos_analyzed: 0,
      creators_tracked: 0,
      rising_count: 0,
      viral_count: 0,
      avg_opportunity: 0,
      profile_complete: false,
    },
  });

export const getFeed = () => apiSafe<TrendListResponse>("/feed", EMPTY_TRENDS);

export const getScenarios = (query = "") =>
  apiSafe<{ items: Scenario[]; total: number }>(`/scenarios${query}`, { items: [], total: 0 });

export const getScenario = (id: string) => api<Scenario>(`/scenarios/${id}`);

export const getSaved = () => apiSafe<SavedItem[]>("/saved", []);

export const getAnalytics = () =>
  apiSafe<Analytics>("/analytics", {
    totals: {},
    by_platform: [],
    by_status: [],
    by_niche: [],
    top_movers: [],
    score_distribution: [],
    adoption_timeline: [],
  });

export const getProfile = () =>
  apiSafe<{ profile: Profile | null }>("/me", { profile: null }).then((u) => u.profile);
