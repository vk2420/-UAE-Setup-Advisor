import { useEffect, useState } from "react";
import IntakeForm from "./components/IntakeForm";
import Results from "./components/Results";
import {
  evaluate,
  getActivities,
  type ActivityOption,
  type EvaluateRequest,
  type EvaluateResult,
} from "./lib/api";

export default function App() {
  const [activities, setActivities] = useState<ActivityOption[]>([]);
  const [result, setResult] = useState<EvaluateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    getActivities()
      .then(setActivities)
      .catch((e) => setLoadError(String(e)));
  }, []);

  async function handleSubmit(req: EvaluateRequest) {
    setLoading(true);
    setError(null);
    try {
      const res = await evaluate(req);
      setResult(res);
    } catch (e) {
      setError(String(e));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-sand-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-5">
          <h1 className="text-xl font-bold text-gray-900">UAE Setup Advisor</h1>
          <p className="text-sm text-gray-500">
            Mainland vs free zone — decided by a deterministic rules engine,
            explained in plain language.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-[380px_1fr]">
          <div className="lg:sticky lg:top-8 lg:self-start">
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-gray-800">
                Tell us about your business
              </h2>
              {loadError ? (
                <p className="text-sm text-red-600">
                  Couldn't reach the API. Is the backend running on port 8000?
                  <br />
                  <span className="text-xs text-gray-400">{loadError}</span>
                </p>
              ) : (
                <IntakeForm
                  activities={activities}
                  loading={loading}
                  onSubmit={handleSubmit}
                />
              )}
            </div>
          </div>

          <div>
            {error && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}
            {result ? (
              <Results result={result} />
            ) : (
              !error && (
                <div className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white/50 p-8 text-center">
                  <p className="text-sm text-gray-400">
                    Fill in the form to see your mainland-vs-free-zone
                    recommendation, a ranked shortlist, and a cost breakdown.
                  </p>
                </div>
              )
            )}
          </div>
        </div>

        <footer className="mt-12 text-center text-xs text-gray-400">
          Directional guidance only — not legal or tax advice. Confirm details
          with the relevant authority.
        </footer>
      </main>
    </div>
  );
}
