# UAE Setup Advisor

An open-source advisory tool that helps entrepreneurs and freelancers decide between
**UAE mainland vs free zone** company setup — and, if a free zone fits, which specific
free zone to choose.

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
                    │   LLM EXPLANATION LAYER  (added later)    │
                    │   Turns the result into friendly prose.   │
                    │   MUST NOT change any decision — only     │
                    │   narrate what the engine already decided.│
                    └─────────────────────────────────────────┘
```

**Why this matters:** eligibility and cost claims are exactly where an LLM would
hallucinate. Here the LLM never decides anything — a deterministic, testable rules
engine produces every decision, and each decision is traceable via a `Citation` back to
a specific entry in an editable JSON knowledge base. The LLM's only job is to explain
that output in plain language.

## Project status

| Milestone | Status |
|-----------|--------|
| Deterministic eligibility engine | ✅ done |
| Test suite (39 tests) | ✅ passing |
| Knowledge base (activities, free zones, ownership rules) | ✅ done |
| FastAPI endpoint | ⏳ next |
| React + Tailwind intake form | ⏳ planned |
| LLM explanation layer (Anthropic API) | ⏳ planned |

## Repository layout

```
backend/
├── app/
│   ├── models.py        # BusinessProfile, EligibilityResult, Citation, … (dataclasses, zero deps)
│   ├── knowledge.py     # loads the JSON knowledge base
│   ├── engine.py        # ← the deterministic engine. No LLM. Fully traceable.
│   └── data/
│       ├── activities.json       # activity types → licensing rules
│       ├── free_zones.json       # free zones → specializations, cost bands, visa rules
│       └── ownership_rules.json  # post-2021 100% foreign-ownership rules
├── tests/test_eligibility.py     # the engine's contract
├── demo.py              # prints sample engine output (no server, no LLM)
└── requirements-dev.txt
```

All rules and pricing live in the `data/*.json` files — **edit those**, not the code,
when rules or costs change.

## Quick start

```bash
cd backend
python3 -m pip install -r requirements-dev.txt   # only pytest; the engine itself has no runtime deps
python3 -m pytest -q                              # run the 39-test suite
python3 demo.py                                   # see sample recommendations
```

## Design guarantees (enforced by tests)

- The engine imports **no** `anthropic` / `openai` / `requests` / `httpx` — verified by a test.
- **Every** reason in the output carries a citation with a real `source_ref`
  (e.g. `activities.json#restaurant_fnb`).
- Same input → same output (deterministic).
- All costs are flagged `approximate` and carry "verify with the authority" disclaimers.

## Data accuracy

Free-zone costs and visa caps are realistic **2025/2026 public-package bands** and are
clearly marked approximate. They change often — verify against a live quote from the zone
authority before relying on any figure. Corrections via PR are welcome.

## Contributing

This is an early-stage MVP. Contributions are welcome — especially knowledge-base
corrections (activities, free zones, pricing). Keep the deterministic-engine-vs-LLM
separation intact: **rules decide, the LLM explains.**

## License

[MIT](LICENSE)
