import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  ApiError,
  formatErrorPayload,
  getHealth,
  getMeta,
  postRecommendations,
} from "@/lib/api";
import type { HealthResponse, RecommendRequest, RecommendResponse } from "@/lib/types";

const MAX_ADDITIONAL = 4_000;

/** Hero background (Unsplash, stable URL). */
const HERO_FOOD_IMAGE =
  "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=2000&q=80";

function formatRatingDisplay(n: number | null): string {
  if (n == null) return "—";
  return n.toFixed(1);
}

function toMarkdown(data: RecommendResponse): string {
  let s = "# Recommendations\n\n";
  s += `Source: **${data.source}** · Matched: ${data.matched_count} · Sent to model: ${data.candidate_count}\n\n`;
  for (const r of data.rankings) {
    const d = r.restaurant;
    if (d) {
      s += `## ${r.rank}. ${d.name}\n\n`;
      s += `- **Why:** ${r.explanation}\n`;
      s += `- **Rating:** ${d.rating ?? "not rated"}\n\n`;
    } else {
      s += `## ${r.rank}.\n\n- **Why:** ${r.explanation}\n\n`;
    }
  }
  return s;
}

function inferBudgetBand(text: string): "" | "low" | "medium" | "high" {
  const t = text.trim().toLowerCase();
  if (!t) return "";
  if (/\blow\b|cheap|under\s*4|3\d{2}\b/.test(t)) return "low";
  if (/\bhigh\b|expensive|2000|2500|3\d{3}/.test(t)) return "high";
  const nums = t.match(/[\d,]+/g);
  if (nums?.length) {
    const a = parseInt(nums[0].replace(/,/g, ""), 10);
    const b = nums[1] ? parseInt(nums[1].replace(/,/g, ""), 10) : a;
    const m = (a + b) / 2;
    if (m < 500) return "low";
    if (m < 1_200) return "medium";
    return "high";
  }
  if (/\bmedium\b|mid/.test(t)) return "medium";
  return "";
}

type EmptyKind = "none" | "no_filter" | "no_picks";

function emptyKind(data: RecommendResponse | null): EmptyKind {
  if (!data) return "none";
  if (data.source === "no_candidates" || data.candidate_count === 0) {
    return "no_filter";
  }
  if (data.rankings.length === 0 && data.candidate_count > 0) return "no_picks";
  return "none";
}

function StarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 20 20"
      width="16"
      height="16"
      fill="#FFC107"
      aria-hidden
    >
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  );
}

export default function RecommendPage() {
  const [location, setLocation] = useState("");
  const [cuisinesText, setCuisinesText] = useState("");
  const [budgetText, setBudgetText] = useState("");
  /** Empty string = no minimum; otherwise star floor sent as `minimum_rating`. */
  const [minimumRating, setMinimumRating] = useState("");
  const [specificCravings, setSpecificCravings] = useState("");
  const [additionalPreferences, setAdditionalPreferences] = useState("");

  const [cities, setCities] = useState<string[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [copyOk, setCopyOk] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let attempt = 0;

    const load = async (): Promise<void> => {
      while (!cancelled) {
        try {
          const m = await getMeta(8_000, 500);
          if (!cancelled) setCities(m.cities);
          return;
        } catch {
          attempt += 1;
          if (cancelled || attempt >= 8) return;
          const delay = Math.min(2_000 * attempt, 10_000);
          await new Promise((r) => setTimeout(r, delay));
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [result]);

  const buildAdditionalText = useCallback((): string => {
    const parts: string[] = [];
    if (specificCravings.trim()) {
      parts.push(`Specific cravings: ${specificCravings.trim()}`);
    }
    if (budgetText.trim()) {
      parts.push(`Budget: ${budgetText.trim()}`);
    }
    if (additionalPreferences.trim()) {
      parts.push(additionalPreferences.trim());
    }
    return parts.join("\n\n");
  }, [specificCravings, budgetText, additionalPreferences]);

  const buildRequest = useCallback((): RecommendRequest => {
    const additional = buildAdditionalText();
    const body: RecommendRequest = {
      location: location.trim(),
      candidate_cap: 30,
      top_k: 5,
    };
    const band = inferBudgetBand(budgetText);
    if (band) body.budget = band;
    const parts = cuisinesText
      .split(/[,|]/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (parts.length) body.cuisines = parts;
    if (additional.length) body.additional_preferences = additional;
    if (minimumRating !== "") {
      const n = Number(minimumRating);
      if (!Number.isNaN(n)) body.minimum_rating = n;
    }
    return body;
  }, [location, budgetText, cuisinesText, minimumRating, buildAdditionalText]);

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setFormError(null);
      setCopyOk(false);
      if (buildAdditionalText().length > MAX_ADDITIONAL) {
        setFormError(
          `Preferences text must be at most ${MAX_ADDITIONAL} characters.`,
        );
        return;
      }
      if (!location.trim()) {
        setFormError("Location is required.");
        return;
      }
      setLoading(true);
      setResult(null);
      try {
        const data = await postRecommendations(buildRequest());
        setResult(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setFormError(formatErrorPayload(err.body));
        } else {
          setFormError(err instanceof Error ? err.message : "Request failed");
        }
      } finally {
        setLoading(false);
      }
    },
    [buildAdditionalText, buildRequest, location],
  );

  const empty = useMemo(() => emptyKind(result), [result]);

  const copyMd = useCallback(() => {
    if (!result) return;
    void navigator.clipboard.writeText(toMarkdown(result)).then(() => {
      setCopyOk(true);
      setTimeout(() => setCopyOk(false), 2_000);
    });
  }, [result]);

  const appendCuisine = useCallback((tag: string) => {
    setCuisinesText((s) => {
      const t = s.trim();
      if (!t) return tag;
      if (t.toLowerCase().includes(tag.toLowerCase())) return t;
      return `${t}, ${tag}`;
    });
  }, []);

  const appendSpecificCraving = useCallback((tag: string) => {
    setSpecificCravings((s) => {
      const t = s.trim();
      if (!t) return tag;
      if (t.toLowerCase().includes(tag.toLowerCase())) return t;
      return `${t}, ${tag}`;
    });
  }, []);

  const quickFilters: { label: string; apply: () => void }[] = [
    { label: "Italian", apply: () => appendCuisine("Italian") },
    { label: "Spicy", apply: () => appendSpecificCraving("Spicy") },
    { label: "Dessert", apply: () => appendCuisine("Dessert") },
  ];

  const combinedAdditionalPreferences = useMemo(
    () => buildAdditionalText(),
    [buildAdditionalText],
  );
  const combinedAdditionalOverLimit =
    combinedAdditionalPreferences.length > MAX_ADDITIONAL;

  return (
    <div className="min-h-screen font-zomato">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-center gap-2 px-4 py-3 md:px-6">
          <span className="text-2xl font-bold leading-none tracking-tight text-zomato-500">
            zomato
          </span>
          <span className="text-lg font-semibold text-stone-900">
            Zomato AI Recommendation
          </span>
        </div>
      </header>

      <section className="relative min-h-[520px] overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${HERO_FOOD_IMAGE})` }}
        />
        <div
          className="absolute inset-0 bg-gradient-to-b from-zomato-500/85 via-stone-900/55 to-stone-900/75"
          aria-hidden
        />

        <div className="relative z-10 mx-auto max-w-3xl px-4 py-12 md:py-16">
          <form
            onSubmit={onSubmit}
            className="rounded-2xl bg-white p-6 shadow-2xl md:p-8"
          >
            <h1 className="text-center text-xl font-bold text-stone-900 md:text-2xl">
              Find Your Perfect Meal with Zomato AI
            </h1>

            <div className="mt-6 flex flex-wrap justify-center gap-2">
              {quickFilters.map(({ label, apply }) => (
                <button
                  key={label}
                  type="button"
                  onClick={apply}
                  className="rounded-full border border-stone-200 bg-white px-4 py-1.5 text-sm text-stone-800 shadow-sm transition hover:border-zomato-500 hover:text-zomato-500"
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-stone-800" htmlFor="loc">
                  Location
                </label>
                <select
                  id="loc"
                  className="mt-1 w-full rounded-lg border-0 bg-stone-100 px-3 py-2.5 text-stone-900 focus:outline-none focus:ring-2 focus:ring-zomato-500/40"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  disabled={cities.length === 0}
                >
                  <option value="">
                    {cities.length === 0 ? "Loading locations…" : "Select a location"}
                  </option>
                  {cities.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-800" htmlFor="cui">
                  Cuisine
                </label>
                <input
                  id="cui"
                  className="mt-1 w-full rounded-lg border-0 bg-stone-100 px-3 py-2.5 text-stone-900 placeholder:text-stone-500 focus:outline-none focus:ring-2 focus:ring-zomato-500/40"
                  value={cuisinesText}
                  onChange={(e) => setCuisinesText(e.target.value)}
                  placeholder="e.g., North Indian"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-800" htmlFor="bud">
                  Budget
                </label>
                <input
                  id="bud"
                  className="mt-1 w-full rounded-lg border-0 bg-stone-100 px-3 py-2.5 text-stone-900 placeholder:text-stone-500 focus:outline-none focus:ring-2 focus:ring-zomato-500/40"
                  value={budgetText}
                  onChange={(e) => setBudgetText(e.target.value)}
                  placeholder="e.g., ₹500-₹1000"
                />
              </div>
              <div>
                <label
                  className="flex items-center gap-1.5 text-sm font-medium text-stone-800"
                  htmlFor="min-rating"
                >
                  <StarIcon className="shrink-0" />
                  Minimum rating
                </label>
                <select
                  id="min-rating"
                  className="mt-1 w-full rounded-lg border-0 bg-stone-100 px-3 py-2.5 text-stone-900 focus:outline-none focus:ring-2 focus:ring-zomato-500/40"
                  value={minimumRating}
                  onChange={(e) => setMinimumRating(e.target.value)}
                >
                  <option value="">Any rating</option>
                  <option value="3">3.0+ stars</option>
                  <option value="3.5">3.5+ stars</option>
                  <option value="4">4.0+ stars</option>
                  <option value="4.5">4.5+ stars</option>
                  <option value="5">5.0 stars</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-800" htmlFor="spec">
                  Specific Cravings
                </label>
                <input
                  id="spec"
                  className="mt-1 w-full rounded-lg border-0 bg-stone-100 px-3 py-2.5 text-stone-900 placeholder:text-stone-500 focus:outline-none focus:ring-2 focus:ring-zomato-500/40"
                  value={specificCravings}
                  onChange={(e) => setSpecificCravings(e.target.value)}
                  placeholder="e.g., Biryani, Butter Chicken"
                />
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-stone-800" htmlFor="add-pref">
                Additional preferences
              </label>
              <p className="mt-0.5 text-xs text-stone-500" id="add-pref-hint">
                Dietary needs, vibe, occasion, dishes to avoid—anything that helps narrow picks.
                Combined with cravings and budget notes: up to {MAX_ADDITIONAL.toLocaleString()}{" "}
                characters.
              </p>
              <textarea
                id="add-pref"
                className="mt-2 min-h-[100px] w-full resize-y rounded-lg border-0 bg-stone-100 px-3 py-2.5 text-stone-900 placeholder:text-stone-500 focus:outline-none focus:ring-2 focus:ring-zomato-500/40"
                value={additionalPreferences}
                onChange={(e) => setAdditionalPreferences(e.target.value)}
                placeholder="e.g., vegetarian only, quiet place for a date, no peanuts…"
                rows={4}
                aria-describedby="add-pref-hint add-pref-count"
              />
              <p
                id="add-pref-count"
                className={`mt-1 text-right text-xs ${
                  combinedAdditionalOverLimit
                    ? "font-medium text-rose-600"
                    : "text-stone-500"
                }`}
              >
                {combinedAdditionalPreferences.length.toLocaleString()} /{" "}
                {MAX_ADDITIONAL.toLocaleString()}
              </p>
            </div>

            {formError && (
              <p
                className="mt-4 whitespace-pre-wrap rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800"
                role="alert"
              >
                {formError}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || combinedAdditionalOverLimit}
              className="mt-6 w-full rounded-lg bg-zomato-500 py-3.5 text-sm font-semibold text-white shadow transition hover:bg-zomato-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Finding restaurants…" : "Get Recommendations"}
            </button>
          </form>
        </div>
      </section>

      {result && (
        <section className="mx-auto max-w-6xl px-4 py-10 md:px-6" aria-live="polite">
          {result.source === "fallback" && result.detail && (
            <p className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
              <strong>Automated fallback.</strong> The model could not return valid rankings;
              using deterministic order.
            </p>
          )}

          {empty === "no_filter" && (
            <div className="mb-6 rounded-2xl border border-stone-200 bg-white p-8 text-center shadow-sm">
              <h2 className="text-lg font-semibold text-stone-800">
                No restaurants match filters
              </h2>
              <p className="mt-2 text-sm text-stone-600">
                Try a different location, lower the minimum rating, or broaden budget / cuisines.
              </p>
            </div>
          )}

          {empty === "no_picks" && (
            <div className="mb-6 rounded-2xl border border-stone-200 bg-white p-8 text-center shadow-sm">
              <h2 className="text-lg font-semibold text-stone-800">
                Could not justify picks
              </h2>
              <p className="mt-2 text-sm text-stone-600">
                Restaurants matched your filters, but the model did not return picks from the
                candidate list.
              </p>
            </div>
          )}

          {result.rankings.length > 0 && (
            <div>
              <h2 className="text-lg font-bold text-stone-900 md:text-xl">
                Personalized Picks for You
              </h2>
              <div className="mb-6 mt-1 flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs text-stone-500">
                  Source: <code>{result.source}</code> · Matched: {result.matched_count} ·
                  Candidates: {result.candidate_count}
                  {result.latency_ms != null && (
                    <> · {result.latency_ms.toFixed(0)} ms</>
                  )}
                </p>
                <button
                  type="button"
                  onClick={copyMd}
                  className="text-sm font-medium text-zomato-600 hover:underline"
                >
                  {copyOk ? "Copied!" : "Copy as Markdown"}
                </button>
              </div>

              <ul className="grid gap-4 sm:grid-cols-2">
                {result.rankings.map((r) => {
                  const d = r.restaurant;
                  const title = d ? d.name : r.restaurant_id;
                  return (
                    <li
                      key={`${r.restaurant_id}-${r.rank}`}
                      className="rounded-2xl border border-stone-200/80 bg-white p-4 shadow-sm"
                    >
                      <h3 className="text-lg font-bold text-stone-900">{title}</h3>
                      <div className="mt-3 rounded-lg bg-zomato-100 p-3 text-sm text-stone-800">
                        <span className="font-semibold text-stone-900">Reason · </span>
                        {r.explanation}
                      </div>
                      <div className="mt-3 flex items-center gap-1.5 text-sm text-stone-800">
                        <StarIcon className="shrink-0" />
                        <span className="font-semibold text-stone-900">Rating · </span>
                        <span>
                          {d && d.rating != null
                            ? formatRatingDisplay(d.rating)
                            : "Not rated"}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </section>
      )}

      <footer className="mt-auto border-t border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center px-4 py-8 text-center md:px-6">
          <span className="text-xl font-bold text-zomato-500">zomato</span>
          <p className="mt-2 max-w-md text-xs leading-relaxed text-stone-500">
            © 2022 Zomato AI Legal | Zomato rsments, Inc. All rights reserved.
          </p>
          {health && (
            <p className="mt-2 text-xs text-stone-400">
              API: {health.status}
              {health.groq_configured ? " · Groq key configured" : " · Groq key missing"}
            </p>
          )}
          {!health && (
            <p className="mt-2 text-xs text-stone-400">API health unavailable (backend?)</p>
          )}
        </div>
      </footer>
    </div>
  );
}
