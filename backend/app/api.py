"""
FastAPI application for UAE Setup Advisor.

Thin web layer over the deterministic engine:
  GET  /api/health      -> liveness + whether the LLM layer is enabled
  GET  /api/activities  -> activity options for the intake form
  GET  /api/free-zones  -> the free-zone knowledge base (for reference/UI)
  POST /api/evaluate    -> run the engine, optionally add an LLM explanation

The engine makes every decision; this layer only validates input, serializes
output, and (optionally) attaches a plain-language explanation.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from . import knowledge
from .engine import evaluate
from .explain import explain
from .models import BusinessProfile, TargetMarket
from .serialize import result_to_dict

app = FastAPI(
    title="UAE Setup Advisor API",
    version="0.1.0",
    description=(
        "Deterministic mainland-vs-free-zone advisor. The engine decides; the "
        "LLM only explains. Directional guidance, not legal or tax advice."
    ),
)

# CORS: allow the local Vite dev server (and configurable extra origins).
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra = os.getenv("CORS_ORIGINS", "")
_origins = _default_origins + [o.strip() for o in _extra.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Request / response schemas
# --------------------------------------------------------------------------- #
class EvaluateRequest(BaseModel):
    activity_id: str = Field(..., description="Activity id from GET /api/activities")
    target_market: TargetMarket = TargetMarket.INTERNATIONAL
    physical_office_needed: bool = False
    employee_visa_count: int = Field(0, ge=0, le=200)
    needs_100_percent_foreign_ownership: bool = True
    budget_aed: Optional[int] = Field(None, ge=0)
    preferred_emirate: Optional[str] = None
    explain: bool = Field(True, description="Attach a plain-language explanation")

    @field_validator("activity_id")
    @classmethod
    def _known_activity(cls, v: str) -> str:
        if v not in knowledge.load_activities():
            raise ValueError(
                f"Unknown activity_id '{v}'. See GET /api/activities for valid ids."
            )
        return v


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
        "activities": len(knowledge.load_activities()),
        "free_zones": len(knowledge.load_free_zones()),
    }


@app.get("/api/activities")
def activities() -> dict:
    """Activity options for the intake form."""
    acts = knowledge.load_activities()
    return {
        "activities": [
            {
                "id": a["id"],
                "label": a["label"],
                "categories": a["categories"],
                "mainland_required": a["mainland_required"],
                "regulated": a["regulated"],
            }
            for a in acts.values()
        ]
    }


@app.get("/api/free-zones")
def free_zones() -> dict:
    """The free-zone knowledge base (reference data for the UI)."""
    return {"free_zones": knowledge.load_free_zones()}


@app.post("/api/evaluate")
def evaluate_endpoint(req: EvaluateRequest) -> dict:
    """Run the deterministic engine; optionally attach an LLM explanation."""
    profile = BusinessProfile(
        activity_id=req.activity_id,
        target_market=req.target_market,
        physical_office_needed=req.physical_office_needed,
        employee_visa_count=req.employee_visa_count,
        needs_100_percent_foreign_ownership=req.needs_100_percent_foreign_ownership,
        budget_aed=req.budget_aed,
        preferred_emirate=req.preferred_emirate,
    )
    try:
        result = evaluate(profile)
    except KeyError as exc:  # unknown activity slipped past validation
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    data = result_to_dict(result)
    if req.explain:
        data["explanation"] = explain(result, data)
    return data
