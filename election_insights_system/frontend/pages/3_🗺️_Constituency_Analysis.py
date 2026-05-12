"""Constituency Analysis page."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.client import (  # noqa: E402
    APIError, get_candidates, get_constituencies, get_party_performance,
    get_turnout, get_voting,
)
from components.ui import (  # noqa: E402
    bar_chart, download_button, inject_css, kpi, line_chart, pie_chart,
    sidebar_filters,
)

st.set_page_config(page_title="Constituency Analysis", page_icon="🗺️", layout="wide")
inject_css()
st.title("🗺️ Constituency Analysis")

try:
    const = get_constituencies()["records"]
    pp = get_party_performance()["records"]
    filters = sidebar_filters(const, {r["party"] for r in pp},
                              {r["election_year"] for r in pp})
    turnout = get_turnout(state=filters["state"])
except APIError as e:
    st.error(str(e))
    st.stop()

by_const = pd.DataFrame(turnout["by_constituency"])
if filters["state"]:
    by_const = by_const[by_const["state"] == filters["state"]]

# KPIs
c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Constituencies", f"{len(by_const):,}")
if not by_const.empty:
    kpi(c2, "Avg Turnout", f"{by_const['avg_turnout'].mean():.1f}%")
    kpi(c3, "Total Votes", f"{int(by_const['total_votes'].sum()):,}")
    kpi(c4, "Total NOTA", f"{int(by_const['total_nota'].sum()):,}")
else:
    kpi(c2, "Avg Turnout", "—")
    kpi(c3, "Total Votes", "—")
    kpi(c4, "Total NOTA", "—")

st.markdown("---")

if not by_const.empty:
    st.subheader("🏆 Top & Bottom Constituencies by Turnout")
    cc1, cc2 = st.columns(2)
    top = by_const.nlargest(10, "avg_turnout")
    bot = by_const.nsmallest(10, "avg_turnout")
    cc1.plotly_chart(bar_chart(top, x="avg_turnout", y="constituency",
                               color="state", orientation="h",
                               title="Top 10 Turnout"),
                     use_container_width=True)
    cc2.plotly_chart(bar_chart(bot, x="avg_turnout", y="constituency",
                               color="state", orientation="h",
                               title="Bottom 10 Turnout"),
                     use_container_width=True)

# Deep-dive on a single constituency
st.subheader("🔍 Deep Dive")
target = filters["constituency"]
if not target and not by_const.empty:
    target = by_const.iloc[0]["constituency"]

if target:
    try:
        voting = pd.DataFrame(get_voting(constituency=target, limit=5000)["records"])
        cands = pd.DataFrame(get_candidates(constituency=target)["records"])
    except APIError as e:
        st.error(str(e))
        st.stop()

    st.markdown(f"**Constituency:** `{target}`")
    if not voting.empty:
        voting["timestamp"] = pd.to_datetime(voting["timestamp"], errors="coerce")
        voting = voting.sort_values("timestamp")
        st.plotly_chart(line_chart(voting, x="timestamp", y="turnout_percentage",
                                   title=f"Booth-level Turnout Trend — {target}"),
                        use_container_width=True)
        with st.expander("📋 Raw booth data"):
            st.dataframe(voting, use_container_width=True, hide_index=True)
            download_button(voting, "⬇️ Download booth data",
                            f"{target}_voting.csv")

    if not cands.empty:
        st.subheader("Candidates")
        st.dataframe(
            cands[["candidate_name", "party", "age", "education",
                   "criminal_cases", "assets", "incumbency"]],
            use_container_width=True, hide_index=True,
        )
        st.plotly_chart(pie_chart(cands, names="party", values="assets",
                                  title="Asset Distribution by Party"),
                        use_container_width=True)
