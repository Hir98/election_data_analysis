"""Helpers shared across analytics and routes."""
from __future__ import annotations

import math
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert a DataFrame to JSON-safe records (NaN -> None)."""
    safe = df.replace({np.nan: None})
    # Convert any Timestamp columns to ISO strings
    for col in safe.columns:
        if pd.api.types.is_datetime64_any_dtype(safe[col]):
            safe[col] = safe[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return safe.to_dict(orient="records")


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def filter_df(
    df: pd.DataFrame,
    state: str | None = None,
    party: str | None = None,
    constituency: str | None = None,
    election_year: int | None = None,
) -> pd.DataFrame:
    """Apply common filters if the relevant columns exist."""
    if state and "state" in df.columns:
        df = df[df["state"] == state]
    if party and "party" in df.columns:
        df = df[df["party"] == party]
    if constituency and "constituency" in df.columns:
        df = df[df["constituency"] == constituency]
    if constituency and "constituency_name" in df.columns:
        df = df[df["constituency_name"] == constituency]
    if election_year is not None and "election_year" in df.columns:
        df = df[df["election_year"] == election_year]
    return df
