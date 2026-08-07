// Typed client for the UAE Setup Advisor API.

const BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export type TargetMarket = "international" | "local_uae" | "both";

export interface ActivityOption {
  id: string;
  label: string;
  categories: string[];
  mainland_required: boolean;
  regulated: boolean;
}

export interface Citation {
  rule_id: string;
  source_ref: string;
  source: string;
}

export interface Reason {
  text: string;
  citation: Citation;
}

export interface CostBreakdown {
  zone_id: string;
  setup_cost_aed: [number, number];
  annual_renewal_aed: [number, number];
  visa_cost_aed: [number, number];
  first_year_total_aed: [number, number];
  approximate: boolean;
}

export interface VisaAssessment {
  requested_visas: number;
  flexi_desk_sufficient: boolean;
  dedicated_office_required: boolean;
  estimated_office_sqm: number | null;
  notes: string;
}

export interface ZoneRecommendation {
  zone_id: string;
  name: string;
  emirate: string;
  score: number;
  match_reasons: Reason[];
  cost: CostBreakdown;
  visa: VisaAssessment;
  within_budget: boolean | null;
  pros: string[];
  cons: string[];
  url: string;
}

export interface Explanation {
  text: string;
  source: "llm" | "fallback";
  model: string | null;
}

export interface EvaluateResult {
  activity_id: string;
  activity_label: string;
  setup_type: "mainland" | "free_zone";
  setup_type_reasons: Reason[];
  ownership_reasons: Reason[];
  zone_shortlist: ZoneRecommendation[];
  disclaimers: string[];
  citations: Citation[];
  explanation?: Explanation;
}

export interface EvaluateRequest {
  activity_id: string;
  target_market: TargetMarket;
  physical_office_needed: boolean;
  employee_visa_count: number;
  needs_100_percent_foreign_ownership: boolean;
  budget_aed: number | null;
  preferred_emirate: string | null;
  explain: boolean;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = JSON.stringify(body.detail ?? body);
    } catch {
      /* ignore */
    }
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function getActivities(): Promise<ActivityOption[]> {
  const res = await fetch(`${BASE_URL}/api/activities`);
  const body = await json<{ activities: ActivityOption[] }>(res);
  return body.activities;
}

export async function evaluate(req: EvaluateRequest): Promise<EvaluateResult> {
  const res = await fetch(`${BASE_URL}/api/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return json<EvaluateResult>(res);
}
