"""Rule-based insight engine.

Produces short, human-friendly narrative insights from the underlying data.
Pure Pandas + thresholds — no LLMs.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.analytics import party as party_an
from backend.analytics import sentiment as sent_an
from backend.analytics import turnout as turnout_an
from backend.data_loader import loader


def _push(out: List[Dict[str, Any]], *, category: str, severity: str,
          title: str, detail: str, metrics: Dict[str, Any] | None = None) -> None:
    out.append({
        "category": category,
        "severity": severity,
        "title": title,
        "detail": detail,
        "metrics": metrics or {},
    })


def generate_insights() -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []

    # ----- Turnout -----
    voting = loader.voting_data()
    const = loader.constituencies()[["constituency_name", "state", "urban_percentage"]]
    v = voting.merge(const, left_on="constituency",
                     right_on="constituency_name", how="left")

    overall_avg = v["turnout_percentage"].mean()
    by_state = v.groupby("state")["turnout_percentage"].mean().sort_values(ascending=False)
    if len(by_state):
        top_state, top_val = by_state.index[0], by_state.iloc[0]
        diff = top_val - overall_avg
        _push(insights, category="Turnout", severity="info",
              title=f"{top_state} leads voter turnout",
              detail=(f"{top_state} averages {top_val:.1f}% turnout — "
                      f"{diff:.1f} points above the overall average ({overall_avg:.1f}%)."),
              metrics={"state": top_state, "avg_turnout": round(top_val, 2)})

        bot_state, bot_val = by_state.index[-1], by_state.iloc[-1]
        if overall_avg - bot_val > 5:
            _push(insights, category="Turnout", severity="warning",
                  title=f"Low participation in {bot_state}",
                  detail=(f"{bot_state} averages just {bot_val:.1f}% turnout, "
                          f"{overall_avg - bot_val:.1f} points below the national average."),
                  metrics={"state": bot_state, "avg_turnout": round(bot_val, 2)})

    # District / urban-bias insight
    urban_v = v[v["urban_percentage"] >= 70]
    rural_v = v[v["urban_percentage"] < 30]
    if len(urban_v) and len(rural_v):
        u = urban_v["turnout_percentage"].mean()
        r = rural_v["turnout_percentage"].mean()
        if abs(u - r) > 3:
            higher = "rural" if r > u else "urban"
            _push(insights, category="Turnout", severity="info",
                  title=f"{higher.title()} constituencies show stronger turnout",
                  detail=(f"Average turnout: urban {u:.1f}% vs rural {r:.1f}% "
                          f"— {higher} regions lead by {abs(u - r):.1f} points."),
                  metrics={"urban": round(u, 2), "rural": round(r, 2)})

    # ----- NOTA hotspots -----
    nota = v.assign(nota_share=v["NOTA_votes"] / v["votes_cast"].replace(0, np.nan) * 100)
    by_const_nota = (nota.groupby(["constituency", "state"])["nota_share"]
                         .mean().reset_index()
                         .sort_values("nota_share", ascending=False))
    if len(by_const_nota):
        top = by_const_nota.iloc[0]
        if top["nota_share"] > 3:
            _push(insights, category="NOTA", severity="warning",
                  title=f"High NOTA voting in {top['constituency']}",
                  detail=(f"Constituency {top['constituency']} ({top['state']}) "
                          f"shows unusually high NOTA share of {top['nota_share']:.2f}%."),
                  metrics={"constituency": top["constituency"],
                           "nota_share": round(top["nota_share"], 2)})

    # ----- Party momentum (vote share trend across years) -----
    pp = loader.party_performance()
    trends = (pp.groupby(["election_year", "party"])["vote_share"]
                .mean().reset_index())
    pivot = trends.pivot(index="party", columns="election_year", values="vote_share")
    years = sorted(pivot.columns)
    if len(years) >= 2:
        latest, prev = years[-1], years[-2]
        pivot["delta"] = pivot[latest] - pivot[prev]
        gainers = pivot.sort_values("delta", ascending=False).head(2)
        for party, row in gainers.iterrows():
            if row["delta"] > 1:
                _push(insights, category="Party", severity="info",
                      title=f"{party} is gaining momentum",
                      detail=(f"{party} vote share rose from {row[prev]:.1f}% in {prev} "
                              f"to {row[latest]:.1f}% in {latest} (+{row['delta']:.1f} pts)."),
                      metrics={"party": party, "delta": round(row["delta"], 2)})
        losers = pivot.sort_values("delta").head(1)
        for party, row in losers.iterrows():
            if row["delta"] < -1:
                _push(insights, category="Party", severity="warning",
                      title=f"{party} losing ground",
                      detail=(f"{party} vote share fell from {row[prev]:.1f}% to "
                              f"{row[latest]:.1f}% ({row['delta']:.1f} pts)."),
                      metrics={"party": party, "delta": round(row["delta"], 2)})

    # ----- Sentiment -----
    sent = sent_an.party_sentiment_summary()
    if sent:
        top = sent[0]
        bot = sent[-1]
        _push(insights, category="Sentiment", severity="info",
              title=f"{top['party']} leads social sentiment",
              detail=(f"{top['party']} has the highest net positive sentiment "
                      f"({top['positive_pct']:.1f}% positive mentions)."),
              metrics={"party": top["party"], "positive_pct": top["positive_pct"]})
        if bot["negative_pct"] > 40:
            _push(insights, category="Sentiment", severity="warning",
                  title=f"Negative sentiment around {bot['party']}",
                  detail=(f"{bot['party']} sees {bot['negative_pct']:.1f}% negative "
                          "mentions across the period."),
                  metrics={"party": bot["party"], "negative_pct": bot["negative_pct"]})

    # ----- Candidate concentration: very high asset candidate -----
    cand = loader.candidates()
    if len(cand):
        rich = cand.nlargest(1, "assets").iloc[0]
        if rich["assets"] > 5e8:
            _push(insights, category="Candidate", severity="info",
                  title="Notably wealthy candidate detected",
                  detail=(f"{rich['candidate_name']} ({rich['party']}, "
                          f"{rich['constituency']}) declares ₹{rich['assets']/1e7:.2f} Cr in assets."),
                  metrics={"candidate": rich["candidate_name"],
                           "assets": int(rich["assets"])})

        high_crime = cand[cand["criminal_cases"] >= 5]
        if len(high_crime) > 0:
            _push(insights, category="Candidate", severity="critical",
                  title="Candidates with multiple criminal cases",
                  detail=(f"{len(high_crime)} candidates declared 5 or more "
                          "criminal cases against them."),
                  metrics={"count": int(len(high_crime))})

    return insights
