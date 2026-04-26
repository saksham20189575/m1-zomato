/**
 * DTOs aligned with Phase 6 `phase6_api/schemas.py`.
 */

export type RecommendSource = "llm" | "fallback" | "no_candidates";

export interface RestaurantDTO {
  id: string;
  name: string;
  city: string;
  cuisines: string[];
  rating: number | null;
  approx_cost_two_inr: number | null;
  budget_band: string;
}

export interface RankingDTO {
  rank: number;
  restaurant_id: string;
  explanation: string;
  restaurant: RestaurantDTO | null;
}

export interface RecommendRequest {
  location: string;
  budget?: string | null;
  cuisines?: string[] | null;
  minimum_rating?: number | null;
  additional_preferences?: string | null;
  load_limit?: number | null;
  candidate_cap?: number;
  top_k?: number;
  model?: string | null;
  temperature?: number;
  max_tokens?: number;
  timeout?: number;
}

export interface RecommendResponse {
  source: RecommendSource;
  matched_count: number;
  candidate_count: number;
  latency_ms: number | null;
  usage: Record<string, number> | null;
  detail: string | null;
  model: string;
  rankings: RankingDTO[];
}

export interface HealthResponse {
  status: string;
  groq_configured: boolean;
}

export interface MetaResponse {
  cities: string[];
  truncated: boolean;
  load_limit_used: number;
  cities_cap: number;
}
