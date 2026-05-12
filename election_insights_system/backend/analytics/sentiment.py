"""Social-sentiment analytics."""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

import pandas as pd

from backend.data_loader import loader


def party_sentiment_summary() -> List[Dict[str, Any]]:
    df = loader.social_sentiment()
    grp = (df.groupby("party")
             .agg(positive=("positive_mentions", "sum"),
                  negative=("negative_mentions", "sum"),
                  neutral=("neutral_mentions", "sum"))
             .reset_index())
    total = grp["positive"] + grp["negative"] + grp["neutral"]
    grp["positive_pct"] = (grp["positive"] / total * 100).round(2)
    grp["negative_pct"] = (grp["negative"] / total * 100).round(2)
    grp["net_sentiment"] = (grp["positive"] - grp["negative"]).astype(int)
    return grp.sort_values("net_sentiment", ascending=False).to_dict(orient="records")


def daily_sentiment(party: str | None = None) -> List[Dict[str, Any]]:
    df = loader.social_sentiment()
    if party:
        df = df[df["party"] == party]
    grp = (df.groupby([df["date"].dt.strftime("%Y-%m-%d"), "party"])
             [["positive_mentions", "negative_mentions", "neutral_mentions"]]
             .sum().reset_index().rename(columns={"date": "date"}))
    return grp.to_dict(orient="records")


def trending_topics(top_n: int = 10) -> List[Dict[str, Any]]:
    df = loader.social_sentiment()
    counter: Counter = Counter()
    for topics in df["trending_topics"].dropna():
        for t in str(topics).split(","):
            t = t.strip()
            if t:
                counter[t] += 1
    return [{"topic": k, "count": v} for k, v in counter.most_common(top_n)]
