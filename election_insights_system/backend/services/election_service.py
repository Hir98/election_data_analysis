"""Thin service layer wrapping data + analytics for routes."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.analytics import (
    anomalies as anomalies_an,
    candidate as candidate_an,
    insights as insights_engine,
    party as party_an,
    sentiment as sentiment_an,
    turnout as turnout_an,
)
from backend.data_loader import loader
from backend.utils.helpers import df_to_records, filter_df


# ---- Data services -----------------------------------------------------------
def list_constituencies(state: str | None = None) -> List[Dict[str, Any]]:
    df = loader.constituencies()
    df = filter_df(df, state=state)
    return df_to_records(df)


def list_candidates(party: str | None = None,
                    constituency: str | None = None) -> List[Dict[str, Any]]:
    df = loader.candidates()
    df = filter_df(df, party=party, constituency=constituency)
    return df_to_records(df)


def list_voting(constituency: str | None = None,
                limit: int = 500) -> List[Dict[str, Any]]:
    df = loader.voting_data()
    df = filter_df(df, constituency=constituency)
    df = df.head(limit)
    return df_to_records(df)


def list_party_performance(state: str | None = None,
                           party: str | None = None,
                           election_year: int | None = None) -> List[Dict[str, Any]]:
    df = loader.party_performance()
    df = filter_df(df, state=state, party=party, election_year=election_year)
    return df_to_records(df)


# ---- Analytics services ------------------------------------------------------
def turnout_analytics(state: str | None = None) -> Dict[str, Any]:
    return {
        "overview": turnout_an.overview(state=state),
        "top_states": turnout_an.top_states(),
        "low_turnout_regions": turnout_an.low_turnout_regions(),
        "by_constituency": turnout_an.constituency_turnout(),
    }


def party_trends(state: str | None = None,
                 election_year: int | None = None) -> Dict[str, Any]:
    return {
        "vote_share_trends": party_an.vote_share_trends(state=state),
        "seat_trends": party_an.seat_trends(state=state),
        "party_dominance": party_an.party_dominance(election_year=election_year),
        "leading_parties_by_state": party_an.leading_parties_by_state(
            election_year=election_year),
    }


def top_candidates(n: int = 10, party: str | None = None) -> Dict[str, Any]:
    return {
        "by_assets": candidate_an.top_candidates_by_assets(n=n, party=party),
        "criminal_summary": candidate_an.criminal_summary(),
        "age_distribution": candidate_an.age_distribution(),
        "party_strength": candidate_an.party_candidate_strength(),
    }


def anomalies() -> Dict[str, Any]:
    return {
        "anomalies": anomalies_an.detect_anomalies(),
        "risk_scores": anomalies_an.constituency_risk_score(),
    }


def insights() -> List[Dict[str, Any]]:
    return insights_engine.generate_insights()


def sentiment() -> Dict[str, Any]:
    return {
        "summary": sentiment_an.party_sentiment_summary(),
        "trending_topics": sentiment_an.trending_topics(),
    }
