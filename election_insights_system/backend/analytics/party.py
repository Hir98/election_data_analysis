"""Party analytics."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.data_loader import loader


def vote_share_trends(state: str | None = None) -> List[Dict[str, Any]]:
    df = loader.party_performance()
    if state:
        df = df[df["state"] == state]
    grp = (df.groupby(["election_year", "party"])["vote_share"]
             .mean().round(2).reset_index())
    return grp.to_dict(orient="records")


def seat_trends(state: str | None = None) -> List[Dict[str, Any]]:
    df = loader.party_performance()
    if state:
        df = df[df["state"] == state]
    grp = (df.groupby(["election_year", "party"])["seats_won"]
             .sum().reset_index())
    return grp.to_dict(orient="records")


def party_dominance(election_year: int | None = None) -> List[Dict[str, Any]]:
    df = loader.party_performance()
    if election_year:
        df = df[df["election_year"] == election_year]
    grp = (df.groupby("party")
             .agg(total_seats=("seats_won", "sum"),
                  avg_vote_share=("vote_share", "mean"))
             .round(2).reset_index()
             .sort_values("total_seats", ascending=False))
    return grp.to_dict(orient="records")


def leading_parties_by_state(election_year: int | None = None) -> List[Dict[str, Any]]:
    df = loader.party_performance()
    if election_year:
        df = df[df["election_year"] == election_year]
    idx = df.groupby("state")["seats_won"].idxmax()
    leaders = df.loc[idx, ["state", "party", "seats_won", "vote_share", "election_year"]]
    return leaders.to_dict(orient="records")
