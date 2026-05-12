"""Raw data endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.data_loader.loader import DataNotFoundError
from backend.services import election_service as svc

router = APIRouter(tags=["data"])


def _wrap(records: list) -> dict:
    return {"count": len(records), "records": records}


@router.get("/constituencies")
def get_constituencies(state: str | None = Query(default=None)):
    try:
        return _wrap(svc.list_constituencies(state=state))
    except DataNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/candidates")
def get_candidates(
    party: str | None = Query(default=None),
    constituency: str | None = Query(default=None),
):
    try:
        return _wrap(svc.list_candidates(party=party, constituency=constituency))
    except DataNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/voting-data")
def get_voting_data(
    constituency: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=20000),
):
    try:
        return _wrap(svc.list_voting(constituency=constituency, limit=limit))
    except DataNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/party-performance")
def get_party_performance(
    state: str | None = Query(default=None),
    party: str | None = Query(default=None),
    election_year: int | None = Query(default=None),
):
    try:
        return _wrap(svc.list_party_performance(
            state=state, party=party, election_year=election_year))
    except DataNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
