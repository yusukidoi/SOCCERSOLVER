import type { PlayerComparison, PlayerProfile, PlayerSummary } from "../types";
import { cacheGet, cacheSet, comparisonCacheKey } from "./cache";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/** Thrown for non-2xx responses so callers can show a meaningful message. */
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, { signal });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // Response had no JSON body; keep the status text.
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export function searchPlayers(query: string, signal?: AbortSignal): Promise<PlayerSummary[]> {
  return request<PlayerSummary[]>(`/players/search?q=${encodeURIComponent(query)}`, signal);
}

export function getPlayerProfile(playerId: number, signal?: AbortSignal): Promise<PlayerProfile> {
  const key = `profile:${playerId}`;
  const cached = cacheGet<PlayerProfile>(key);
  if (cached) return Promise.resolve(cached);

  return request<PlayerProfile>(`/players/${playerId}/profile`, signal).then((profile) => {
    cacheSet(key, profile);
    return profile;
  });
}

export function comparePlayers(
  oneId: number,
  twoId: number,
  signal?: AbortSignal,
): Promise<PlayerComparison> {
  const key = comparisonCacheKey(oneId, twoId);
  const cached = cacheGet<PlayerComparison>(key);
  if (cached) return Promise.resolve(cached);

  return request<PlayerComparison>(`/comparison?one=${oneId}&two=${twoId}`, signal).then(
    (comparison) => {
      cacheSet(key, comparison);
      return comparison;
    },
  );
}
