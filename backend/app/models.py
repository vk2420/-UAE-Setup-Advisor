"""
Domain models for the UAE Setup Advisor deterministic engine.

These are plain dataclasses / enums with NO third-party dependencies, so the
eligibility engine and its test suite run with nothing but the standard library
plus pytest. The FastAPI layer wraps these in Pydantic models separately.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TargetMarket(str, Enum):
    """Where the business primarily sells."""

    LOCAL_UAE = "local_uae"          # sells to the UAE onshore public / local clients
    INTERNATIONAL = "international"    # sells abroad / cross-border
    BOTH = "both"                     # a mix of local and international


class SetupType(str, Enum):
    MAINLAND = "mainland"
    FREE_ZONE = "free_zone"


@dataclass(frozen=True)
class BusinessProfile:
    """Structured intake object. In production the LLM intake layer produces this;
    for the engine and tests it is constructed directly."""

    activity_id: str
    target_market: TargetMarket = TargetMarket.INTERNATIONAL
    physical_office_needed: bool = False
    employee_visa_count: int = 0                 # visas needed, INCLUDING the owner if they want residency
    needs_100_percent_foreign_ownership: bool = True
    budget_aed: Optional[int] = None             # total first-year budget the user has in mind (optional)
    preferred_emirate: Optional[str] = None       # e.g. "Dubai" (soft preference, tie-breaker only)

    def __post_init__(self) -> None:
        if self.employee_visa_count < 0:
            raise ValueError("employee_visa_count cannot be negative")
        if self.budget_aed is not None and self.budget_aed < 0:
            raise ValueError("budget_aed cannot be negative")


@dataclass(frozen=True)
class Citation:
    """A traceable pointer back to the knowledge base entry that produced a claim.
    Every rule-driven statement carries one, so nothing in the output is freeform."""

    rule_id: str                     # stable id of the rule / decision, e.g. "mainland_required_activity"
    source_ref: str                  # data-file locator, e.g. "activities.json#retail_shop"
    source: str                      # human-readable authority / origin string from the data file


@dataclass(frozen=True)
class Reason:
    """A single explained factor in a decision, with its citation."""

    text: str
    citation: Citation


@dataclass
class CostBreakdown:
    """Approximate cost bands for a specific free zone given the profile."""

    zone_id: str
    setup_cost_aed: tuple[int, int]         # (min, max) first-year licence, no visas
    annual_renewal_aed: tuple[int, int]
    visa_cost_aed: tuple[int, int]          # (min, max) total for the requested visa count
    first_year_total_aed: tuple[int, int]   # setup + visas
    approximate: bool = True
    citation: Optional[Citation] = None


@dataclass
class VisaAssessment:
    """Whether the requested visa count is feasible and what it implies."""

    requested_visas: int
    flexi_desk_sufficient: bool             # can the requested count fit on a no-office flexi-desk package?
    dedicated_office_required: bool
    estimated_office_sqm: Optional[int]     # rough sqm needed if a dedicated office is required
    notes: str
    citation: Citation


@dataclass
class ZoneRecommendation:
    """One ranked free zone in the shortlist."""

    zone_id: str
    name: str
    emirate: str
    score: float
    match_reasons: list[Reason]
    cost: CostBreakdown
    visa: VisaAssessment
    within_budget: Optional[bool]           # None if no budget was provided
    pros: list[str]
    cons: list[str]
    url: str
    last_verified: Optional[str] = None     # e.g. "2026-08" — when the pricing was last checked


@dataclass
class EligibilityResult:
    """The complete deterministic output. The LLM explanation layer consumes this
    and MUST NOT change any decision — only narrate it."""

    activity_id: str
    activity_label: str
    setup_type: SetupType
    setup_type_reasons: list[Reason]
    ownership_reasons: list[Reason]
    zone_shortlist: list[ZoneRecommendation]         # empty when setup_type == MAINLAND
    disclaimers: list[str]
    # A flat, machine-readable trace of every citation used, for auditing.
    citations: list[Citation] = field(default_factory=list)
