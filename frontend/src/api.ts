import type {
  Corridor,
  Health,
  Location,
  Mode,
  Plan,
  PlanRequest,
} from "./types";

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(
      "Cannot reach the routing service. Check that the Django server is running, then try again.",
    );
  }
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      "The routing service returned an unreadable response. Please try again.",
    );
  }
  if (!response.ok) {
    const error = data as { error?: { message?: string } };
    throw new Error(
      error.error?.message ||
        `The request failed (${response.status}). Please try again.`,
    );
  }
  return data as T;
}
export const api = {
  health: (signal?: AbortSignal) => request<Health>("/api/health", { signal }),
  locations: (q: string, mode: Mode, signal?: AbortSignal) =>
    request<{ locations: Location[] }>(
      `/api/locations?q=${encodeURIComponent(q)}&mode=${mode}`,
      { signal },
    ),
  plan: (input: PlanRequest, signal?: AbortSignal) =>
    request<Plan>("/api/plan", {
      method: "POST",
      body: JSON.stringify(input),
      signal,
    }),
  corridor: (planId: string, signal?: AbortSignal) =>
    request<Corridor>("/api/corridor", {
      method: "POST",
      body: JSON.stringify({ plan_id: planId }),
      signal,
    }),
};
