"""Anomaly detection — statistical thresholds on voting + NOTA."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.data_loader import loader


def detect_anomalies() -> List[Dict[str, Any]]:
    """Detect:
    - Sudden booth-level turnout spikes (>= mean + 2*std for its constituency)
    - Booth-level turnout dips (<= mean - 2*std)
    - High NOTA booths (NOTA share > 5%)
    """
    df = loader.voting_data().copy()
    const = loader.constituencies()[["constituency_name", "state"]]
    df = df.merge(const, left_on="constituency", right_on="constituency_name", how="left")
    df["nota_share"] = (df["NOTA_votes"] / df["votes_cast"].replace(0, np.nan)) * 100

    results: List[Dict[str, Any]] = []

    stats = (df.groupby("constituency")["turnout_percentage"]
               .agg(["mean", "std"]).reset_index())
    df = df.merge(stats, on="constituency", how="left")
    df["upper"] = df["mean"] + 2 * df["std"].fillna(0)
    df["lower"] = df["mean"] - 2 * df["std"].fillna(0)

    spikes = df[df["turnout_percentage"] > df["upper"]]
    for _, r in spikes.head(50).iterrows():
        results.append({
            "type": "turnout_spike",
            "constituency": r["constituency"],
            "state": r["state"],
            "value": float(round(r["turnout_percentage"], 2)),
            "threshold": float(round(r["upper"], 2)),
            "detail": (f"Booth {r['polling_booth']} turnout {r['turnout_percentage']:.1f}% "
                       f"exceeds constituency upper bound {r['upper']:.1f}%."),
        })

    dips = df[df["turnout_percentage"] < df["lower"]]
    for _, r in dips.head(50).iterrows():
        results.append({
            "type": "turnout_dip",
            "constituency": r["constituency"],
            "state": r["state"],
            "value": float(round(r["turnout_percentage"], 2)),
            "threshold": float(round(r["lower"], 2)),
            "detail": (f"Booth {r['polling_booth']} turnout {r['turnout_percentage']:.1f}% "
                       f"below constituency lower bound {r['lower']:.1f}%."),
        })

    high_nota = df[df["nota_share"] > 5]
    for _, r in high_nota.head(50).iterrows():
        results.append({
            "type": "high_nota",
            "constituency": r["constituency"],
            "state": r["state"],
            "value": float(round(r["nota_share"], 2)),
            "threshold": 5.0,
            "detail": f"Booth {r['polling_booth']} NOTA share {r['nota_share']:.1f}%.",
        })

    return results


def constituency_risk_score() -> List[Dict[str, Any]]:
    """Bonus: composite per-constituency risk score (0-100)."""
    df = loader.voting_data().copy()
    const = loader.constituencies()[["constituency_name", "state"]]
    df["nota_share"] = (df["NOTA_votes"] / df["votes_cast"].replace(0, np.nan)) * 100

    agg = (df.groupby("constituency")
             .agg(avg_turnout=("turnout_percentage", "mean"),
                  turnout_std=("turnout_percentage", "std"),
                  avg_nota=("nota_share", "mean"))
             .reset_index())
    # Lower turnout, higher std, higher NOTA -> higher risk
    agg["low_turnout_component"] = np.clip((60 - agg["avg_turnout"]) * 1.5, 0, 60)
    agg["volatility_component"] = np.clip(agg["turnout_std"].fillna(0) * 2, 0, 20)
    agg["nota_component"] = np.clip(agg["avg_nota"] * 4, 0, 20)
    agg["risk_score"] = (agg["low_turnout_component"]
                         + agg["volatility_component"]
                         + agg["nota_component"]).round(2)
    agg = agg.merge(const, left_on="constituency",
                    right_on="constituency_name", how="left")
    return (agg[["constituency", "state", "avg_turnout", "avg_nota", "risk_score"]]
            .sort_values("risk_score", ascending=False)
            .round(2)
            .to_dict(orient="records"))
