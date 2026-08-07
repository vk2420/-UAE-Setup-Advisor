# Contributing to UAE Setup Advisor

Thanks for helping! This project stays useful only if its knowledge base stays
accurate, so **corrections to the data are the most valuable contributions.**

## The one rule that must not break

**Rules decide; the LLM only explains.**

The deterministic engine (`backend/app/engine.py`) makes every eligibility, ranking,
cost, and visa decision. The LLM layer (`backend/app/explain.py`) may only narrate the
engine's output — it must never decide, re-rank, or introduce a fact that isn't already
in the engine result. A test (`test_engine_does_not_import_llm_or_network`) enforces that
the engine imports no LLM or network libraries. Keep it that way.

## Ways to contribute

### 1. Fix or add knowledge-base data (most impactful)

All rules and pricing live in `backend/app/data/`:

- `activities.json` — business activities and their licensing constraints
- `free_zones.json` — free zones, specializations, cost bands, visa rules
- `ownership_rules.json` — foreign-ownership rules

Edit the JSON, then run the tests. Guidelines:

- Costs are **approximate bands** (`{"min": ..., "max": ...}`). Keep them realistic and
  cite a `source`. Never present a number as exact.
- Every record needs a `source` field so the output stays traceable.
- If you add an activity or free zone, add or update a test asserting how the engine
  should route/rank it.

### 2. Improve the engine

- Keep it **pure and stdlib-only** — no third-party or network imports.
- Add a test for any new rule. The suite is the engine's contract.

### 3. API / frontend / LLM layer

- API changes: add a test in `backend/tests/test_api.py`.
- LLM layer: any change must preserve the graceful fallback (the app must work with no
  API key and no network).

## Development setup

```bash
# Backend
cd backend
python3 -m pip install -r requirements.txt      # runtime + API
python3 -m pip install -r requirements-dev.txt   # pytest
python3 -m pytest -q                             # must be green before you push

# Frontend
cd ../frontend
npm install
npm run build                                    # must typecheck + build cleanly
```

## Pull requests

- Keep PRs focused. One logical change per PR.
- Make sure `pytest` passes and `npm run build` succeeds.
- Describe **what** changed and **why**; for data changes, link the source you used.
- By contributing, you agree your work is licensed under the project's [MIT License](LICENSE).

## Reporting issues

Open an issue with: what you expected, what happened, and (for data issues) the
authoritative source that shows the correct value.
