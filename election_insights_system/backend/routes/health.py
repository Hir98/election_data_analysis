"""Health-check route."""
from __future__ import annotations

from fastapi import APIRouter

from backend.data_loader import loader

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    counts = {}
    status = "ok"
    for name in ("constituencies", "candidates", "voting_data",
                 "party_performance", "social_sentiment"):
        try:
            counts[name] = int(len(loader.get(name)))
        except Exception as e:  # data not generated yet
            counts[name] = 0
            status = "degraded"
            counts[f"{name}_error"] = str(e)  # type: ignore[assignment]
    return {"status": status, "datasets": counts}
