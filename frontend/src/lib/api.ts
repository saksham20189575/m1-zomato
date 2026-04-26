import type {
  HealthResponse,
  MetaResponse,
  RecommendRequest,
  RecommendResponse,
} from "./types";

export function apiBase(): string {
  const v = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
  return v && v.length > 0 ? v : "http://127.0.0.1:8000";
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`HTTP ${status}`);
    this.name = "ApiError";
  }
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${apiBase()}/health`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body);
  }
  return res.json();
}

export async function getMeta(
  loadLimit: number = 8_000,
  citiesCap: number = 500,
): Promise<MetaResponse> {
  const p = new URLSearchParams({
    load_limit: String(loadLimit),
    cities_cap: String(citiesCap),
  });
  const res = await fetch(`${apiBase()}/api/v1/meta?${p}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body);
  }
  return res.json();
}

export async function postRecommendations(
  body: RecommendRequest,
): Promise<RecommendResponse> {
  const res = await fetch(`${apiBase()}/api/v1/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(res.status, data);
  }
  return data as RecommendResponse;
}

export function formatErrorPayload(body: unknown): string {
  if (!body || typeof body !== "object") return "Request failed";
  const o = body as Record<string, unknown>;
  const detail = o.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const d = detail as { errors?: { field: string; message: string }[] };
    if (Array.isArray(d.errors)) {
      return d.errors.map((e) => `${e.field}: ${e.message}`).join("\n");
    }
  }
  if (Array.isArray(detail)) {
    return (detail as { msg?: string }[])
      .map((e) => e.msg ?? JSON.stringify(e))
      .join(" ");
  }
  if (typeof o.message === "string") return o.message;
  return JSON.stringify(body);
}
