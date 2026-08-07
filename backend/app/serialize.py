"""
Serialization helpers: turn the engine's dataclass result into JSON-safe dicts
for the API layer. Kept separate so the engine stays free of web concerns.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from .models import EligibilityResult


def _clean(obj: Any) -> Any:
    """Recursively convert dataclasses, enums, and tuples to JSON-safe values."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _clean(v) for k, v in asdict(obj).items()}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


def result_to_dict(result: EligibilityResult) -> dict[str, Any]:
    """Convert an EligibilityResult to a plain, JSON-serializable dict.

    Cost bands are (min, max) tuples in the dataclass; they become 2-element
    lists here, which the frontend renders as ranges.
    """
    return _clean(result)
