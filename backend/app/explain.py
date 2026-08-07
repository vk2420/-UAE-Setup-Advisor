"""
LLM explanation layer.

CRITICAL DESIGN RULE: the LLM only *explains* the deterministic engine's output.
It never decides eligibility, never invents costs, and never contradicts the
engine. Every factual claim it makes must trace back to a citation the engine
already produced. This is the core anti-hallucination pattern of the project.

The layer is fully optional and env-gated:
  - If ANTHROPIC_API_KEY is set, it calls the Anthropic API to produce a friendly,
    plain-language narrative grounded in the engine's reasons + citations.
  - If not (or if the SDK/call fails), it falls back to a DETERMINISTIC,
    template-based explanation built directly from the engine's own reasons.
    The app therefore works end-to-end with no API key and no network.

Configure via environment (see .env.example):
  ANTHROPIC_API_KEY   - enables the live LLM path
  ANTHROPIC_MODEL     - model id (default: claude-opus-5)
"""
from __future__ import annotations

import json
import os
from typing import Any

from .models import EligibilityResult, SetupType

DEFAULT_MODEL = "claude-opus-5"

# The system prompt encodes the guardrail: explain, never decide.
_SYSTEM_PROMPT = """\
You are an assistant that EXPLAINS the output of a deterministic UAE business-setup \
rules engine in clear, friendly language for an entrepreneur.

Hard rules — follow exactly:
1. The engine has already decided everything: mainland vs free zone, the ranked \
free-zone shortlist, costs, and visa assessment. You do NOT decide, re-rank, or \
second-guess any of it. Explain what the engine concluded and why.
2. Use ONLY the facts, numbers, and reasons present in the provided JSON. Never \
introduce a cost, rule, free zone, or eligibility claim that is not in the data. \
If a detail is not present, do not invent it.
3. When you state a reason, attribute it to the engine's rule (reference the \
rule_id in parentheses, e.g. "(rule: mainland_required_activity)").
4. Keep all cost figures exactly as given, and always call them approximate.
5. End by restating the disclaimers in your own words: this is directional \
guidance, not legal/tax advice, and figures must be confirmed with the relevant \
authority.

Write 3-6 short paragraphs of plain prose. Do not output JSON."""


def _fallback_explanation(data: dict[str, Any]) -> str:
    """Deterministic, no-LLM explanation assembled from the engine's own reasons.

    This is not a degraded stub — it is a faithful, fully-cited rendering of the
    engine output, and is what the app serves when no API key is configured.
    """
    lines: list[str] = []
    setup = str(data["setup_type"]).replace("_", " ")
    lines.append(f"**Recommendation: {setup.title()}** for “{data['activity_label']}”.")
    lines.append("")

    lines.append("**Why:**")
    for r in data.get("setup_type_reasons", []) + data.get("ownership_reasons", []):
        cit = r.get("citation", {})
        lines.append(f"- {r['text']} _(rule: {cit.get('rule_id', 'n/a')})_")
    lines.append("")

    shortlist = data.get("zone_shortlist", [])
    if shortlist:
        lines.append("**Ranked free zones (approximate 2025/2026 pricing):**")
        for i, z in enumerate(shortlist, 1):
            cost = z["cost"]["first_year_total_aed"]
            budget = ""
            if z.get("within_budget") is True:
                budget = " — within your budget"
            elif z.get("within_budget") is False:
                budget = " — likely over your budget"
            lines.append(
                f"{i}. **{z['name']}** ({z['emirate']}): estimated first-year "
                f"AED {cost[0]:,}–{cost[1]:,}{budget}."
            )
            lines.append(f"   - Visas: {z['visa']['notes']}")
        lines.append("")

    lines.append("**Please note:**")
    for d in data.get("disclaimers", []):
        lines.append(f"- {d}")

    return "\n".join(lines)


def _build_user_prompt(data: dict[str, Any]) -> str:
    return (
        "Here is the deterministic engine output as JSON. Explain it to the "
        "entrepreneur following your rules.\n\n```json\n"
        + json.dumps(data, indent=2)
        + "\n```"
    )


def explain(result: EligibilityResult, data: dict[str, Any]) -> dict[str, Any]:
    """Return an explanation payload.

    `data` is the already-serialized result dict (from serialize.result_to_dict).
    Returns {"text": str, "source": "llm"|"fallback", "model": str|None}.
    Never raises — any failure degrades gracefully to the deterministic fallback.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"text": _fallback_explanation(data), "source": "fallback", "model": None}

    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
    try:
        import anthropic  # imported lazily so the engine/tests never need the SDK

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(data)}],
        )
        # Guard against a safety refusal before reading content.
        if response.stop_reason == "refusal":
            return {
                "text": _fallback_explanation(data),
                "source": "fallback",
                "model": None,
            }
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            return {"text": _fallback_explanation(data), "source": "fallback", "model": None}
        return {"text": text, "source": "llm", "model": model}
    except Exception:
        # Missing SDK, network error, bad key, rate limit — degrade, never crash.
        return {"text": _fallback_explanation(data), "source": "fallback", "model": None}
