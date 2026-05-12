"""Turnout analytics."""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from backend.data_loader import loader


def _voting_with_state() -> pd.DataFrame:
    voting = loader.voting_data()
    const = loader.constituencies()[["constituency_name", "state", "district",
                                     "urban_percentage", "rural_percentage",
                                     "total_voters"]]
    return voting.merge(const, left_on="constituency",
                        right_on="constituency_name", how="left")


def overview(state: str | None = None) -> Dict[str, Any]:
    df = _voting_with_state()
    if state:
        df = df[df["state"] == state]
    if df.empty:
        return {"avg_turnout": 0, "median_turnout": 0, "n_booths": 0, "by_state": []}

    by_state = (
        df.groupby("state")["turnout_percentage"]
        .mean().round(2).reset_index()
        .rename(columns={"turnout_percentage": "avg_turnout"})
        .sort_values("avg_turnout", ascending=False)
    )
    return {
        "avg_turnout": round(df["turnout_percentage"].mean(), 2),
        "median_turnout": round(df["turnout_percentage"].median(), 2),
        "min_turnout": round(df["turnout_percentage"].min(), 2),
        "max_turnout": round(df["turnout_percentage"].max(), 2),
        "n_booths": int(len(df)),
        "by_state": by_state.to_dict(orient="records"),
    }


def top_states(n: int = 5) -> list[dict]:
    df = _voting_with_state()
    grp = (df.groupby("state")["turnout_percentage"].mean()
             .round(2).sort_values(ascending=False).head(n))
    return [{"state": s, "avg_turnout": v} for s, v in grp.items()]


def low_turnout_regions(threshold: float = 50.0) -> list[dict]:
    df = _voting_with_state()
    by_const = (df.groupby(["constituency", "state"])["turnout_percentage"]
                  .mean().round(2).reset_index()
                  .rename(columns={"turnout_percentage": "avg_turnout"}))
    low = by_const[by_const["avg_turnout"] < threshold].sort_values("avg_turnout")
    return low.to_dict(orient="records")


def constituency_turnout() -> list[dict]:
    df = _voting_with_state()
    by_const = (df.groupby(["constituency", "state"])
                  .agg(avg_turnout=("turnout_percentage", "mean"),
                       total_votes=("votes_cast", "sum"),
                       total_nota=("NOTA_votes", "sum"))
                  .round(2).reset_index())
    return by_const.to_dict(orient="records")
