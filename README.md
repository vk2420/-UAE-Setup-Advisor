# UAE Setup Advisor

An open-source advisory tool that helps entrepreneurs and freelancers decide between
**UAE mainland vs free zone** company setup — and, if a free zone fits, which specific
free zone to choose. It gives a ranked shortlist, an approximate cost breakdown, a
visa-quota assessment, and a citation for every claim.

> **Directional guidance, not legal/tax advice.** Always confirm final details with the
> relevant free zone authority, the emirate's Department of Economy (DED), or a licensed
> corporate services provider.

## The core idea: rules decide, the LLM only explains

The whole point of this project is a **hard separation** between decision-making and
narration:

```
                    ┌─────────────────────────────────────────┐
   BusinessProfile  │   DETERMINISTIC ELIGIBILITY ENGINE       │
  ───────────────▶  │   (pure Python, stdlib only, NO LLM)     │  ─────▶  EligibilityResult
  activity, market, │   • mainland vs free zone                │          (structured JSON,
  visas, budget,    │   • ranked free-zone shortlist           │           every claim carries
  ownership need    │   • cost bands + visa-quota assessment    │           a Citation)
                    │   • 100% foreign-ownership rules          │
                    └─────────────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────────┐
                    │   LLM EXPLANATION LAYER  (optional)       │
                    │   Turns the result into friendly prose.   │
                    │   MUST NOT change any decision — only     │
                    │   narrate what the engine already decided.│
                    │   No API key? A deterministic template    │
                    │   explanation is used instead.            │
                    └─────────────────────────────────────────┘
```

**Why this matters:** eligibility and cost claims are exactly where an LLM would
hallucinate. Here the LLM never decides anything — a deterministic, testable rules
engine produces every decision, and each decision is traceable via a `Citation` back to
a specific entry in an editable JSON knowledge base. The LLM's only job is to explain
that output in plain language, and the app works fully **without** an LLM at all.

## Project status

| Milestone | Status |
|-----------|--------|
| Deterministic eligibility engine | ✅ done |
| Test suite (48 tests: engine + API) | ✅ passing |
| Knowledge base (activities, free zones, ownership rules) | ✅ done |
| FastAPI endpoint | ✅ done |
| React + Tailwind intake form | ✅ done |
| LLM explanation layer (Anthropic API, env-gated) | ✅ done |
| Docker / docker-compose | ✅ done |

## Repository layout

```
backend/
├── app/
│   ├── models.py        # dataclasses/enums (engine domain model, zero deps)
│   ├── knowledge.py     # loads the JSON knowledge base
│   ├── engine.py        # ← the deterministic engine. No LLM. Fully traceable.
│   ├── serialize.py     # dataclass result → JSON-safe dict
│   ├── explain.py       # optional LLM explanation (env-gated + deterministic fallback)
│   ├── api.py           # FastAPI app
│   └── data/
│       ├── activities.json       # activity types → licensing rules
│       ├── free_zones.json       # free zones → specializations, cost bands, visa rules
│       └── ownership_rules.json  # post-2021 100% foreign-ownership rules
├── tests/                # engine + API tests
├── demo.py               # prints sample engine output (no server, no LLM)
├── requirements.txt      # API + LLM deps
└── requirements-dev.txt  # just pytest (the engine has no runtime deps)
frontend/                 # Vite + React + TypeScript + Tailwind single-page app
docker-compose.yml        # run the whole stack
.env.example              # configuration (copy to .env)
```

All rules and pricing live in `backend/app/data/*.json` — **edit those**, not the code,
when rules or costs change.

## Quick start

### 1. Backend (the engine + API)

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m pytest -q            # 48 tests
python3 demo.py                 # sample engine output, no server
uvicorn app.api:app --reload --port 8000
```

API is now at `http://localhost:8000` (`/api/health`, `/api/activities`, `/api/evaluate`).
Interactive docs at `http://localhost:8000/docs`.

### 2. Frontend (the intake form)

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

### 3. Everything at once (Docker)

```bash
cp .env.example .env            # optional: add ANTHROPIC_API_KEY for LLM prose
docker compose up --build
```

Frontend on `http://localhost:8080`, backend on `http://localhost:8000`.

## The LLM explanation layer

Entirely **optional** and **env-gated**:

- **No `ANTHROPIC_API_KEY`** → the app serves a deterministic, fully-cited explanation
  assembled directly from the engine's own reasons. Everything works offline.
- **With a key** → the Anthropic API turns the engine output into friendly prose. The
  system prompt forbids the model from deciding, re-ranking, or inventing costs — it may
  only explain what the engine already produced, citing rule ids.

Set it in `.env` (see [.env.example](.env.example)):

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-5
```

The response's `explanation.source` field is `"llm"` or `"fallback"` so you always know
which path produced the text.

## Design guarantees (enforced by tests)

- The engine imports **no** `anthropic` / `openai` / `requests` / `httpx` — verified by a test.
- **Every** reason in the output carries a citation with a real `source_ref`
  (e.g. `activities.json#restaurant_fnb`).
- Same input → same output (deterministic).
- All costs are flagged `approximate` and carry "verify with the authority" disclaimers.
- The API never crashes on LLM failure — it degrades to the deterministic explanation.

## Data accuracy

Free-zone costs and visa caps are **2026 public-package bands, cross-checked in August
2026** against multiple business-setup consultancies and (where published) the zone
authorities, with a dated `source` on every zone. They are still **approximate**: UAE
free-zone pricing moves constantly and is sold mostly through agents, so bands overlap
and promotions vary. Always confirm a live written quote with the zone authority before
relying on any figure. Corrections via PR are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most valuable contributions are
knowledge-base corrections (activities, free zones, pricing). Keep the
deterministic-engine-vs-LLM separation intact: **rules decide, the LLM explains.**

## License

[MIT](LICENSE)
