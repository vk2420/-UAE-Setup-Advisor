"""
Test suite for the deterministic eligibility engine.

These tests are the contract for the engine and run with NO LLM and NO network.
Run from the backend/ directory with:  pytest -q
"""
from __future__ import annotations

import pytest

from app import knowledge
from app.engine import evaluate
from app.models import BusinessProfile, SetupType, TargetMarket


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #
def _zone_ids(result) -> list[str]:
    return [z.zone_id for z in result.zone_shortlist]


# --------------------------------------------------------------------------- #
# Knowledge base integrity
# --------------------------------------------------------------------------- #
class TestKnowledgeBase:
    def test_activities_load_and_have_required_fields(self):
        activities = knowledge.load_activities()
        assert len(activities) >= 10, "MVP should cover 10-15 activity types"
        required = {
            "id", "label", "categories", "mainland_required",
            "free_zone_eligible", "serves_local_market_directly", "regulated", "source",
        }
        for act in activities.values():
            assert required <= set(act.keys()), f"{act.get('id')} missing fields"

    def test_free_zones_load_and_have_required_fields(self):
        zones = knowledge.load_free_zones()
        assert len(zones) >= 8, "MVP should cover 8-10 major free zones"
        for z in zones:
            for key in (
                "id", "name", "emirate", "specializations", "cost_tier",
                "setup_cost_aed", "annual_renewal_aed", "per_visa_cost_aed",
                "visa_rules", "source", "url",
            ):
                assert key in z, f"zone {z.get('id')} missing '{key}'"
            for band in ("setup_cost_aed", "annual_renewal_aed", "per_visa_cost_aed"):
                assert z[band]["min"] <= z[band]["max"], f"{z['id']} {band} min>max"
            assert {"flexi_desk_max_visas", "sqm_per_visa"} <= set(z["visa_rules"])

    def test_expected_marquee_zones_present(self):
        ids = {z["id"] for z in knowledge.load_free_zones()}
        for expected in ("ifza", "dmcc", "difc", "adgm", "dic", "shams", "meydan", "rakez", "dafza", "dubai_south"):
            assert expected in ids, f"expected zone '{expected}' missing"

    def test_unknown_activity_raises(self):
        with pytest.raises(KeyError):
            knowledge.get_activity("does_not_exist")

    def test_all_zones_have_last_verified(self):
        # data-freshness field, surfaced in the UI, so visitors can judge staleness
        for z in knowledge.load_free_zones():
            assert z.get("last_verified"), f"zone {z['id']} missing last_verified"


class TestDataFreshness:
    def test_shortlist_carries_last_verified(self):
        result = evaluate(BusinessProfile(activity_id="commodities_trading"))
        assert result.zone_shortlist  # non-empty
        for z in result.zone_shortlist:
            assert z.last_verified, f"{z.zone_id} recommendation missing last_verified"


# --------------------------------------------------------------------------- #
# Mainland vs Free Zone decision
# --------------------------------------------------------------------------- #
class TestSetupTypeDecision:
    @pytest.mark.parametrize(
        "activity_id",
        ["retail_shop", "restaurant_fnb", "real_estate_brokerage",
         "construction_contracting", "healthcare_clinic", "legal_services"],
    )
    def test_mainland_required_activities_route_to_mainland(self, activity_id):
        result = evaluate(BusinessProfile(activity_id=activity_id))
        assert result.setup_type == SetupType.MAINLAND
        assert result.zone_shortlist == []
        # decision must be traceable to the activity rule
        assert any(
            r.citation.rule_id == "mainland_required_activity"
            for r in result.setup_type_reasons
        )

    def test_international_free_zone_activity_routes_to_free_zone(self):
        result = evaluate(
            BusinessProfile(activity_id="it_software", target_market=TargetMarket.INTERNATIONAL)
        )
        assert result.setup_type == SetupType.FREE_ZONE
        assert 3 <= len(result.zone_shortlist) <= 5

    def test_local_market_routes_to_mainland_even_if_free_zone_eligible(self):
        # general_trading IS free-zone eligible, but a purely local focus favours mainland
        result = evaluate(
            BusinessProfile(activity_id="general_trading", target_market=TargetMarket.LOCAL_UAE)
        )
        assert result.setup_type == SetupType.MAINLAND
        assert any(
            r.citation.rule_id == "local_market_favours_mainland"
            for r in result.setup_type_reasons
        )

    def test_both_markets_free_zone_with_distributor_caveat(self):
        result = evaluate(
            BusinessProfile(activity_id="general_trading", target_market=TargetMarket.BOTH)
        )
        assert result.setup_type == SetupType.FREE_ZONE
        assert any(
            r.citation.rule_id == "both_markets_need_distributor"
            for r in result.setup_type_reasons
        )


# --------------------------------------------------------------------------- #
# Free zone ranking / specialization matching
# --------------------------------------------------------------------------- #
class TestZoneRanking:
    def test_commodities_ranks_dmcc_top(self):
        result = evaluate(
            BusinessProfile(activity_id="commodities_trading", target_market=TargetMarket.INTERNATIONAL)
        )
        assert result.zone_shortlist[0].zone_id == "dmcc"

    def test_financial_services_shortlists_regulated_finance_zones(self):
        result = evaluate(
            BusinessProfile(activity_id="financial_services", target_market=TargetMarket.INTERNATIONAL)
        )
        ids = _zone_ids(result)
        assert "difc" in ids and "adgm" in ids
        # a finance-focused zone should top the list
        assert result.zone_shortlist[0].zone_id in {"difc", "adgm", "dmcc"}

    def test_tech_shortlists_dubai_internet_city(self):
        result = evaluate(
            BusinessProfile(activity_id="it_software", target_market=TargetMarket.INTERNATIONAL)
        )
        assert "dic" in _zone_ids(result)

    def test_logistics_shortlists_logistics_zones(self):
        result = evaluate(
            BusinessProfile(activity_id="logistics_freight", target_market=TargetMarket.INTERNATIONAL)
        )
        ids = set(_zone_ids(result))
        assert ids & {"dafza", "dubai_south"}

    def test_freelancer_low_budget_favours_cheap_zone(self):
        result = evaluate(
            BusinessProfile(
                activity_id="freelance_creative",
                target_market=TargetMarket.INTERNATIONAL,
                budget_aed=8000,
            )
        )
        # SHAMS is the cheapest and freelance-focused; it should rank at or near the top
        assert result.zone_shortlist[0].zone_id in {"shams", "rakez"}

    def test_shortlist_only_contains_relevant_zones(self):
        # every shortlisted zone must actually specialize in a matching category
        result = evaluate(BusinessProfile(activity_id="commodities_trading"))
        activity = knowledge.get_activity("commodities_trading")
        cats = set(activity["categories"])
        for zone_rec in result.zone_shortlist:
            zone = next(z for z in knowledge.load_free_zones() if z["id"] == zone_rec.zone_id)
            assert cats & set(zone["specializations"])

    def test_emirate_preference_boosts_matching_zone(self):
        base = evaluate(BusinessProfile(activity_id="consulting_professional"))
        pref = evaluate(
            BusinessProfile(activity_id="consulting_professional", preferred_emirate="Sharjah")
        )
        shams_base = next((z.score for z in base.zone_shortlist if z.zone_id == "shams"), None)
        shams_pref = next((z.score for z in pref.zone_shortlist if z.zone_id == "shams"), None)
        if shams_base is not None and shams_pref is not None:
            assert shams_pref > shams_base


# --------------------------------------------------------------------------- #
# Visa assessment
# --------------------------------------------------------------------------- #
class TestVisaAssessment:
    def test_zero_visas_flexi_desk_sufficient(self):
        result = evaluate(
            BusinessProfile(activity_id="consulting_professional", employee_visa_count=0)
        )
        top = result.zone_shortlist[0]
        assert top.visa.flexi_desk_sufficient is True
        assert top.visa.dedicated_office_required is False

    def test_visa_count_over_cap_requires_office(self):
        result = evaluate(
            BusinessProfile(activity_id="general_trading", employee_visa_count=10)
        )
        top = result.zone_shortlist[0]
        assert top.visa.dedicated_office_required is True
        assert top.visa.estimated_office_sqm is not None
        assert top.visa.estimated_office_sqm >= 10 * 9

    def test_physical_office_requested_forces_dedicated_office(self):
        result = evaluate(
            BusinessProfile(
                activity_id="general_trading",
                employee_visa_count=1,
                physical_office_needed=True,
            )
        )
        top = result.zone_shortlist[0]
        assert top.visa.dedicated_office_required is True
        assert top.visa.flexi_desk_sufficient is False


# --------------------------------------------------------------------------- #
# Cost breakdown
# --------------------------------------------------------------------------- #
class TestCostBreakdown:
    def test_visa_cost_scales_with_count(self):
        one = evaluate(BusinessProfile(activity_id="general_trading", employee_visa_count=1))
        three = evaluate(BusinessProfile(activity_id="general_trading", employee_visa_count=3))
        z1 = next(z for z in one.zone_shortlist if z.zone_id == "ifza")
        z3 = next(z for z in three.zone_shortlist if z.zone_id == "ifza")
        assert z3.cost.visa_cost_aed[0] == 3 * z1.cost.visa_cost_aed[0] if z1.cost.visa_cost_aed[0] else True
        assert z3.cost.visa_cost_aed[1] > z1.cost.visa_cost_aed[1]

    def test_first_year_total_is_setup_plus_visas(self):
        result = evaluate(BusinessProfile(activity_id="general_trading", employee_visa_count=2))
        for z in result.zone_shortlist:
            assert z.cost.first_year_total_aed[0] == z.cost.setup_cost_aed[0] + z.cost.visa_cost_aed[0]
            assert z.cost.first_year_total_aed[1] == z.cost.setup_cost_aed[1] + z.cost.visa_cost_aed[1]

    def test_all_costs_flagged_approximate(self):
        result = evaluate(BusinessProfile(activity_id="general_trading"))
        assert all(z.cost.approximate for z in result.zone_shortlist)

    def test_budget_flag_reflects_affordability(self):
        result = evaluate(
            BusinessProfile(activity_id="general_trading", budget_aed=10000)
        )
        for z in result.zone_shortlist:
            expected = 10000 >= z.cost.first_year_total_aed[0]
            assert z.within_budget == expected

    def test_no_budget_leaves_within_budget_none(self):
        result = evaluate(BusinessProfile(activity_id="general_trading"))
        assert all(z.within_budget is None for z in result.zone_shortlist)


# --------------------------------------------------------------------------- #
# Ownership
# --------------------------------------------------------------------------- #
class TestOwnership:
    def test_free_zone_always_100_percent(self):
        result = evaluate(BusinessProfile(activity_id="it_software"))
        assert any(
            r.citation.rule_id == "free_zone_always_100_percent"
            for r in result.ownership_reasons
        )

    def test_mainland_cites_2021_reform(self):
        result = evaluate(BusinessProfile(activity_id="retail_shop"))
        assert any(
            r.citation.rule_id == "mainland_default_since_2021"
            for r in result.ownership_reasons
        )


# --------------------------------------------------------------------------- #
# Traceability / no-hallucination guarantees
# --------------------------------------------------------------------------- #
class TestTraceability:
    def test_every_reason_has_a_citation_with_source(self):
        result = evaluate(
            BusinessProfile(activity_id="general_trading", employee_visa_count=2, budget_aed=30000)
        )
        all_reasons = list(result.setup_type_reasons) + list(result.ownership_reasons)
        for z in result.zone_shortlist:
            all_reasons += z.match_reasons
        for r in all_reasons:
            assert r.citation is not None
            assert r.citation.rule_id
            assert r.citation.source_ref
            assert r.citation.source

    def test_citations_reference_real_data_files(self):
        result = evaluate(BusinessProfile(activity_id="it_software"))
        valid_files = {"activities.json", "free_zones.json", "ownership_rules.json"}
        for cit in result.citations:
            file_part = cit.source_ref.split("#", 1)[0]
            assert file_part in valid_files

    def test_citation_trace_is_deduplicated(self):
        result = evaluate(BusinessProfile(activity_id="general_trading"))
        keys = [(c.rule_id, c.source_ref) for c in result.citations]
        assert len(keys) == len(set(keys))

    def test_disclaimers_always_present(self):
        result = evaluate(BusinessProfile(activity_id="it_software"))
        assert len(result.disclaimers) >= 3
        assert any("not legal" in d.lower() for d in result.disclaimers)

    def test_regulated_activity_adds_regulator_disclaimer(self):
        result = evaluate(BusinessProfile(activity_id="financial_services"))
        assert any("regulated activity" in d.lower() for d in result.disclaimers)


# --------------------------------------------------------------------------- #
# Determinism & input validation
# --------------------------------------------------------------------------- #
class TestDeterminismAndValidation:
    def test_same_input_same_output(self):
        p = BusinessProfile(activity_id="general_trading", employee_visa_count=2, budget_aed=25000)
        r1 = evaluate(p)
        r2 = evaluate(p)
        assert r1.setup_type == r2.setup_type
        assert _zone_ids(r1) == _zone_ids(r2)
        assert [z.score for z in r1.zone_shortlist] == [z.score for z in r2.zone_shortlist]

    def test_engine_does_not_import_llm_or_network(self):
        # The eligibility engine must be pure: no anthropic / requests / httpx imports.
        import app.engine as engine_mod
        import inspect

        src = inspect.getsource(engine_mod)
        for forbidden in ("anthropic", "openai", "requests", "httpx", "urllib.request"):
            assert forbidden not in src, f"engine must not depend on '{forbidden}'"

    def test_negative_visa_count_rejected(self):
        with pytest.raises(ValueError):
            BusinessProfile(activity_id="general_trading", employee_visa_count=-1)

    def test_negative_budget_rejected(self):
        with pytest.raises(ValueError):
            BusinessProfile(activity_id="general_trading", budget_aed=-5)
