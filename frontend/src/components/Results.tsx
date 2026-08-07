import type { EvaluateResult, Reason, ZoneRecommendation } from "../lib/api";

const aed = (n: number) => `AED ${n.toLocaleString()}`;

// "2026-08" -> "Aug 2026"
function fmtVerified(s: string | null): string | null {
  if (!s) return null;
  const [y, m] = s.split("-").map(Number);
  if (!y || !m) return s;
  const month = new Date(y, m - 1, 1).toLocaleString("en", { month: "short" });
  return `${month} ${y}`;
}

function ReasonList({ reasons }: { reasons: Reason[] }) {
  return (
    <ul className="space-y-2">
      {reasons.map((r, i) => (
        <li key={i} className="text-sm text-gray-700">
          <span>{r.text}</span>{" "}
          <span
            className="text-xs text-gray-400"
            title={`${r.citation.source_ref} — ${r.citation.source}`}
          >
            (rule: {r.citation.rule_id})
          </span>
        </li>
      ))}
    </ul>
  );
}

function ZoneCard({ zone, rank }: { zone: ZoneRecommendation; rank: number }) {
  const [minT, maxT] = zone.cost.first_year_total_aed;
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-gray-900">
            <span className="mr-2 text-desert-600">#{rank}</span>
            {zone.name}
          </h4>
          <p className="text-xs text-gray-500">{zone.emirate}</p>
        </div>
        {zone.within_budget !== null && (
          <span
            className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${
              zone.within_budget
                ? "bg-green-100 text-green-700"
                : "bg-amber-100 text-amber-700"
            }`}
          >
            {zone.within_budget ? "Within budget" : "Over budget"}
          </span>
        )}
      </div>

      <table className="mt-3 w-full text-sm">
        <tbody className="divide-y divide-gray-100">
          <tr>
            <td className="py-1.5 text-gray-500">Setup (year 1, no visas)</td>
            <td className="py-1.5 text-right font-medium text-gray-900">
              {aed(zone.cost.setup_cost_aed[0])}–{aed(zone.cost.setup_cost_aed[1])}
            </td>
          </tr>
          <tr>
            <td className="py-1.5 text-gray-500">
              Visas ×{zone.visa.requested_visas}
            </td>
            <td className="py-1.5 text-right font-medium text-gray-900">
              {aed(zone.cost.visa_cost_aed[0])}–{aed(zone.cost.visa_cost_aed[1])}
            </td>
          </tr>
          <tr>
            <td className="py-1.5 text-gray-500">Annual renewal</td>
            <td className="py-1.5 text-right font-medium text-gray-900">
              {aed(zone.cost.annual_renewal_aed[0])}–
              {aed(zone.cost.annual_renewal_aed[1])}
            </td>
          </tr>
          <tr className="font-semibold text-gray-900">
            <td className="py-1.5">Est. first-year total</td>
            <td className="py-1.5 text-right">
              {aed(minT)}–{aed(maxT)}
            </td>
          </tr>
        </tbody>
      </table>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
          ≈ Estimate
        </span>
        {fmtVerified(zone.last_verified) && (
          <span className="text-[10px] text-gray-400">
            pricing verified {fmtVerified(zone.last_verified)} · confirm with the
            authority
          </span>
        )}
      </div>

      <p className="mt-3 text-xs text-gray-600">
        <span className="font-medium text-gray-700">Visas: </span>
        {zone.visa.notes}
      </p>

      {zone.match_reasons.length > 0 && (
        <div className="mt-3">
          <ReasonList reasons={zone.match_reasons} />
        </div>
      )}

      <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="mb-1 font-medium text-green-700">Pros</p>
          <ul className="list-disc space-y-0.5 pl-4 text-gray-600">
            {zone.pros.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium text-amber-700">Cons</p>
          <ul className="list-disc space-y-0.5 pl-4 text-gray-600">
            {zone.cons.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      </div>

      {zone.url && (
        <a
          href={zone.url}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-block text-xs font-medium text-desert-700 hover:underline"
        >
          Visit zone authority →
        </a>
      )}
    </div>
  );
}

export default function Results({ result }: { result: EvaluateResult }) {
  const isFreeZone = result.setup_type === "free_zone";
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <p className="text-xs uppercase tracking-wide text-gray-400">
          Recommendation
        </p>
        <h2 className="mt-1 text-2xl font-bold text-gray-900">
          {isFreeZone ? "Free Zone" : "Mainland"}
        </h2>
        <p className="mt-1 text-sm text-gray-600">{result.activity_label}</p>

        <div className="mt-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">Why</h3>
          <ReasonList
            reasons={[...result.setup_type_reasons, ...result.ownership_reasons]}
          />
        </div>
      </div>

      {result.explanation && (
        <div className="rounded-xl border border-sand-100 bg-sand-50 p-5">
          <div className="mb-2 flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-800">In plain language</h3>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-gray-500">
              {result.explanation.source === "llm"
                ? `AI-written · ${result.explanation.model}`
                : "template (no API key)"}
            </span>
          </div>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
            {result.explanation.text}
          </div>
        </div>
      )}

      {isFreeZone && result.zone_shortlist.length > 0 && (
        <div>
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-gray-800">
              Ranked free zones
            </h3>
            <p className="text-xs text-gray-400">
              Costs are approximate 2026 bands, not live quotes — always confirm a
              written quote with the zone authority.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {result.zone_shortlist.map((z, i) => (
              <ZoneCard key={z.zone_id} zone={z} rank={i + 1} />
            ))}
          </div>
        </div>
      )}

      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
          Please note
        </h3>
        <ul className="list-disc space-y-1 pl-4 text-xs text-gray-600">
          {result.disclaimers.map((d, i) => (
            <li key={i}>{d}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
