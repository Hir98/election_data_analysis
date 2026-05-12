"""Thin requests client to the FastAPI backend."""
from __future__ import annotations

import os
from typing import Any, Dict

import requests
import streamlit as st

BASE_URL = os.environ.get("ELECTION_API_BASE", "http://127.0.0.1:8000")
TIMEOUT = 30


class APIError(RuntimeError):
    pass


def _get(path: str, params: Dict[str, Any] | None = None) -> Any:
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise APIError(f"Cannot reach API at {url}. Is the backend running?\n{e}") from e
    if r.status_code >= 400:
        raise APIError(f"{r.status_code} from {url}: {r.text}")
    return r.json()


# Cache for the duration of the Streamlit session to keep UI snappy.
@st.cache_data(ttl=60, show_spinner=False)
def get_health() -> dict: return _get("/health")

@st.cache_data(ttl=60, show_spinner=False)
def get_constituencies(state: str | None = None) -> dict:
    return _get("/constituencies", {"state": state} if state else None)

@st.cache_data(ttl=60, show_spinner=False)
def get_candidates(party: str | None = None,
                   constituency: str | None = None) -> dict:
    p = {}
    if party: p["party"] = party
    if constituency: p["constituency"] = constituency
    return _get("/candidates", p or None)

@st.cache_data(ttl=60, show_spinner=False)
def get_voting(constituency: str | None = None, limit: int = 2000) -> dict:
    p: Dict[str, Any] = {"limit": limit}
    if constituency: p["constituency"] = constituency
    return _get("/voting-data", p)

@st.cache_data(ttl=60, show_spinner=False)
def get_party_performance(state: str | None = None,
                          party: str | None = None,
                          election_year: int | None = None) -> dict:
    p: Dict[str, Any] = {}
    if state: p["state"] = state
    if party: p["party"] = party
    if election_year: p["election_year"] = election_year
    return _get("/party-performance", p or None)

@st.cache_data(ttl=60, show_spinner=False)
def get_turnout(state: str | None = None) -> dict:
    return _get("/analytics/turnout", {"state": state} if state else None)

@st.cache_data(ttl=60, show_spinner=False)
def get_party_trends(state: str | None = None,
                     election_year: int | None = None) -> dict:
    p: Dict[str, Any] = {}
    if state: p["state"] = state
    if election_year: p["election_year"] = election_year
    return _get("/analytics/party-trends", p or None)

@st.cache_data(ttl=60, show_spinner=False)
def get_top_candidates(n: int = 10, party: str | None = None) -> dict:
    p: Dict[str, Any] = {"n": n}
    if party: p["party"] = party
    return _get("/analytics/top-candidates", p)

@st.cache_data(ttl=60, show_spinner=False)
def get_anomalies() -> dict: return _get("/analytics/anomalies")

@st.cache_data(ttl=60, show_spinner=False)
def get_insights() -> dict: return _get("/analytics/insights")

@st.cache_data(ttl=60, show_spinner=False)
def get_sentiment() -> dict: return _get("/analytics/sentiment")
