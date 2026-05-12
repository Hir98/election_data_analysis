"""Analytics endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.data_loader.loader import DataNotFoundError
from backend.services import election_service as svc

router = APIRouter()


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except DataNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/turnout")
def turnout(state: str | None = Query(default=None)):
    return _safe(svc.turnout_analytics, state=state)


@router.get("/party-trends")
def party_trends(
    state: str | None = Query(default=None),
    election_year: int | None = Query(default=None),
):
    return _safe(svc.party_trends, state=state, election_year=election_year)


@router.get("/top-candidates")
def top_candidates(
    n: int = Query(default=10, ge=1, le=100),
    party: str | None = Query(default=None),
):
    return _safe(svc.top_candidates, n=n, party=party)


@router.get("/anomalies")
def anomalies():
    return _safe(svc.anomalies)


@router.get("/insights")
def insights():
    return {"insights": _safe(svc.insights)}


@router.get("/sentiment")
def sentiment():
    return _safe(svc.sentiment)
