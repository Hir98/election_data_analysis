"""Lightweight CSV loader with in-memory caching.

All datasets are loaded from data/sample_data/. Files are loaded once on
first access and cached. Call ``reload()`` to force a refresh.
"""
from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Dict

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "sample_data"

_FILES = {
    "constituencies": "constituencies.csv",
    "candidates": "candidates.csv",
    "voting_data": "voting_data.csv",
    "party_performance": "party_performance.csv",
    "social_sentiment": "social_sentiment.csv",
}

_cache: Dict[str, pd.DataFrame] = {}
_lock = Lock()


class DataNotFoundError(RuntimeError):
    """Raised when sample data has not been generated yet."""


def _load(name: str) -> pd.DataFrame:
    path = DATA_DIR / _FILES[name]
    if not path.exists():
        raise DataNotFoundError(
            f"Missing dataset '{name}' at {path}. "
            "Run: python scripts/generate_sample_data.py"
        )
    df = pd.read_csv(path)
    if name == "voting_data" and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if name == "social_sentiment" and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def get(name: str) -> pd.DataFrame:
    """Return a cached copy of the named dataset."""
    if name not in _FILES:
        raise KeyError(f"Unknown dataset: {name}")
    with _lock:
        if name not in _cache:
            _cache[name] = _load(name)
        # Return a shallow copy so callers can mutate without poisoning cache
        return _cache[name].copy()


def reload() -> None:
    """Drop all cached datasets."""
    with _lock:
        _cache.clear()


# Convenience accessors
def constituencies() -> pd.DataFrame: return get("constituencies")
def candidates() -> pd.DataFrame: return get("candidates")
def voting_data() -> pd.DataFrame: return get("voting_data")
def party_performance() -> pd.DataFrame: return get("party_performance")
def social_sentiment() -> pd.DataFrame: return get("social_sentiment")
