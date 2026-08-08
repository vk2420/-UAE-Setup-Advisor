"""
Vercel serverless entry point.

Vercel's Python runtime serves the module-level ASGI ``app``. We reuse the exact
same FastAPI app as local/Docker (backend/app/api.py) — no forked logic. All
``/api/*`` requests are rewritten to this function (see vercel.json), and Vercel
forwards the original request path to the ASGI app, so the app's existing
``/api/...`` routes match unchanged.

The engine's JSON knowledge base is bundled via ``includeFiles`` in vercel.json.
"""
import os
import sys

# Make the backend package importable as `app` (backend/app/...).
_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, _BACKEND)

from app.api import app  # noqa: E402  — re-exported for the Vercel Python runtime

# `app` is what Vercel looks for. Nothing else to do.
__all__ = ["app"]
