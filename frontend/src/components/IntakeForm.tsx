import { useState } from "react";
import type {
  ActivityOption,
  EvaluateRequest,
  TargetMarket,
} from "../lib/api";

interface Props {
  activities: ActivityOption[];
  loading: boolean;
  onSubmit: (req: EvaluateRequest) => void;
}

const MARKETS: { value: TargetMarket; label: string }[] = [
  { value: "international", label: "Mostly international / cross-border" },
  { value: "both", label: "A mix of international and UAE" },
  { value: "local_uae", label: "Mostly the UAE local market" },
];

const EMIRATES = ["", "Dubai", "Abu Dhabi", "Sharjah", "Ras Al Khaimah"];

export default function IntakeForm({ activities, loading, onSubmit }: Props) {
  const [activityId, setActivityId] = useState("");
  const [targetMarket, setTargetMarket] = useState<TargetMarket>("international");
  const [visas, setVisas] = useState(1);
  const [office, setOffice] = useState(false);
  const [ownership, setOwnership] = useState(true);
  const [budget, setBudget] = useState<string>("");
  const [emirate, setEmirate] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!activityId) return;
    onSubmit({
      activity_id: activityId,
      target_market: targetMarket,
      physical_office_needed: office,
      employee_visa_count: visas,
      needs_100_percent_foreign_ownership: ownership,
      budget_aed: budget ? parseInt(budget, 10) : null,
      preferred_emirate: emirate || null,
      explain: true,
    });
  }

  const labelCls = "block text-sm font-medium text-gray-700 mb-1";
  const fieldCls =
    "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-desert-600 focus:ring-1 focus:ring-desert-600 outline-none";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className={labelCls} htmlFor="activity">
          What is your business activity?
        </label>
        <select
          id="activity"
          className={fieldCls}
          value={activityId}
          onChange={(e) => setActivityId(e.target.value)}
          required
        >
          <option value="" disabled>
            Select an activity…
          </option>
          {activities.map((a) => (
            <option key={a.id} value={a.id}>
              {a.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={labelCls} htmlFor="market">
          Who are your customers?
        </label>
        <select
          id="market"
          className={fieldCls}
          value={targetMarket}
          onChange={(e) => setTargetMarket(e.target.value as TargetMarket)}
        >
          {MARKETS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelCls} htmlFor="visas">
            Visas needed
          </label>
          <input
            id="visas"
            type="number"
            min={0}
            max={200}
            className={fieldCls}
            value={visas}
            onChange={(e) => setVisas(Math.max(0, parseInt(e.target.value || "0", 10)))}
          />
        </div>
        <div>
          <label className={labelCls} htmlFor="budget">
            First-year budget (AED, optional)
          </label>
          <input
            id="budget"
            type="number"
            min={0}
            placeholder="e.g. 25000"
            className={fieldCls}
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className={labelCls} htmlFor="emirate">
          Preferred emirate (optional)
        </label>
        <select
          id="emirate"
          className={fieldCls}
          value={emirate}
          onChange={(e) => setEmirate(e.target.value)}
        >
          {EMIRATES.map((em) => (
            <option key={em} value={em}>
              {em || "No preference"}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={office}
            onChange={(e) => setOffice(e.target.checked)}
            className="rounded border-gray-300 text-desert-600 focus:ring-desert-600"
          />
          I need a physical office (not just a flexi-desk)
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={ownership}
            onChange={(e) => setOwnership(e.target.checked)}
            className="rounded border-gray-300 text-desert-600 focus:ring-desert-600"
          />
          I want 100% foreign ownership
        </label>
      </div>

      <button
        type="submit"
        disabled={loading || !activityId}
        className="w-full rounded-lg bg-desert-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-desert-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Analyzing…" : "Get my recommendation"}
      </button>
    </form>
  );
}
