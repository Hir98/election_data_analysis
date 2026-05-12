"""Candidate analytics."""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.data_loader import loader


def top_candidates_by_assets(n: int = 10, party: str | None = None) -> List[Dict[str, Any]]:
    df = loader.candidates()
    if party:
        df = df[df["party"] == party]
    df = df.sort_values("assets", ascending=False).head(n)
    return df.to_dict(orient="records")


def criminal_summary() -> Dict[str, Any]:
    df = loader.candidates()
    by_party = (df.groupby("party")
                  .agg(total=("candidate_id", "count"),
                       with_cases=("criminal_cases", lambda s: int((s > 0).sum())),
                       avg_cases=("criminal_cases", "mean"))
                  .round(2).reset_index())
    by_party["pct_with_cases"] = (by_party["with_cases"] / by_party["total"] * 100).round(2)
    return {
        "total_candidates": int(len(df)),
        "total_with_cases": int((df["criminal_cases"] > 0).sum()),
        "by_party": by_party.to_dict(orient="records"),
    }


def age_distribution() -> List[Dict[str, Any]]:
    df = loader.candidates().copy()
    bins = [0, 30, 40, 50, 60, 70, 100]
    labels = ["<30", "30-40", "40-50", "50-60", "60-70", "70+"]
    df["age_group"] = pd.cut(df["age"], bins=bins, labels=labels, right=False)
    grp = df.groupby("age_group", observed=True)["candidate_id"].count().reset_index()
    grp = grp.rename(columns={"candidate_id": "count"})
    grp["age_group"] = grp["age_group"].astype(str)
    return grp.to_dict(orient="records")


def party_candidate_strength() -> List[Dict[str, Any]]:
    df = loader.candidates()
    grp = (df.groupby("party")
             .agg(candidates=("candidate_id", "count"),
                  avg_age=("age", "mean"),
                  avg_assets=("assets", "mean"))
             .round(2).reset_index()
             .sort_values("candidates", ascending=False))
    return grp.to_dict(orient="records")
