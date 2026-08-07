"""
Knowledge-base loader.

Reads the static JSON data files (activities, free zones, ownership rules) that
back the deterministic engine. Kept separate from engine logic so the data can be
edited, validated, or swapped (e.g. for a RAG store later) without touching rules.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> dict[str, Any]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_activities() -> dict[str, dict[str, Any]]:
    """Return a dict keyed by activity id."""
    raw = _load("activities.json")
    return {a["id"]: a for a in raw["activities"]}


@lru_cache(maxsize=1)
def load_free_zones() -> list[dict[str, Any]]:
    """Return the list of free zone records (order preserved from the file)."""
    return _load("free_zones.json")["free_zones"]


@lru_cache(maxsize=1)
def load_ownership_rules() -> dict[str, Any]:
    return _load("ownership_rules.json")["rules"]


def get_activity(activity_id: str) -> dict[str, Any]:
    activities = load_activities()
    if activity_id not in activities:
        raise KeyError(
            f"Unknown activity_id '{activity_id}'. "
            f"Known ids: {sorted(activities.keys())}"
        )
    return activities[activity_id]


def list_activity_ids() -> list[str]:
    return sorted(load_activities().keys())


def clear_cache() -> None:
    """Drop cached data (used in tests that patch the data files)."""
    load_activities.cache_clear()
    load_free_zones.cache_clear()
    load_ownership_rules.cache_clear()
