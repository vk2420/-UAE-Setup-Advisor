"""
Quick manual demo of the deterministic engine (no LLM, no server).

Run from backend/:  python demo.py
"""
from __future__ import annotations

from dataclasses import asdict

from app.engine import evaluate
from app.models import BusinessProfile, TargetMarket


def show(profile: BusinessProfile) -> None:
    r = evaluate(profile)
    print("=" * 78)
    print(f"Activity: {r.activity_label}")
    print(f"Recommendation: {r.setup_type.value.upper().replace('_', ' ')}")
    print("-- Why --")
    for reason in r.setup_type_reasons + r.ownership_reasons:
        print(f"  • {reason.text}")
        print(f"      [rule={reason.citation.rule_id} src={reason.citation.source_ref}]")
    if r.zone_shortlist:
        print("-- Ranked free zones --")
        for i, z in enumerate(r.zone_shortlist, 1):
            budget = "" if z.within_budget is None else (" ✓ within budget" if z.within_budget else " ✗ over budget")
            print(f"  {i}. {z.name} ({z.emirate})  score={z.score}{budget}")
            print(
                f"       first-year ~AED {z.cost.first_year_total_aed[0]:,}-"
                f"{z.cost.first_year_total_aed[1]:,} "
                f"(setup {z.cost.setup_cost_aed[0]:,}-{z.cost.setup_cost_aed[1]:,} + "
                f"{z.visa.requested_visas} visa(s))"
            )
            print(f"       visas: {z.visa.notes}")
    print("-- Disclaimers --")
    for d in r.disclaimers:
        print(f"  ! {d}")
    print()


if __name__ == "__main__":
    show(BusinessProfile(
        activity_id="commodities_trading",
        target_market=TargetMarket.INTERNATIONAL,
        employee_visa_count=2,
        budget_aed=50000,
    ))
    show(BusinessProfile(
        activity_id="freelance_creative",
        target_market=TargetMarket.INTERNATIONAL,
        employee_visa_count=1,
        budget_aed=10000,
    ))
    show(BusinessProfile(
        activity_id="restaurant_fnb",
        target_market=TargetMarket.LOCAL_UAE,
    ))
