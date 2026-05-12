"""Party Analysis page."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.client import (  # noqa: E402
    APIError, get_constituencies, get_party_performance, get_party_trends,
    get_sentiment, get_top_candidates,
)
from components.ui import (  # noqa: E402
    bar_chart, download_button, inject_css, kpi, line_chart, pie_chart,
    sidebar_filters,
)

st.set_page_config(page_title="Party Analysis", page_icon="🏛️", layout="wide")
inject_css()
st.title("🏛️ Party Analysis")

try:
    const = get_constituencies()["records"]
    pp = get_party_performance()["records"]
    filters = sidebar_filters(const, {r["party"] for r in pp},
                              {r["election_year"] for r in pp})
    trends = get_party_trends(state=filters["state"],
                              election_year=filters["election_year"])
    sentiment = get_sentiment()
    top_c = get_top_candidates(n=15, party=filters["party"])
except APIError as e:
    st.error(str(e))
    st.stop()

dominance = pd.DataFrame(trends["party_dominance"])
vs = pd.DataFrame(trends["vote_share_trends"])
seats = pd.DataFrame(trends["seat_trends"])
sent = pd.DataFrame(sentiment["summary"])

# KPIs
c1, c2, c3, c4 = st.columns(4)
if not dominance.empty:
    leader = dominance.iloc[0]
    kpi(c1, "Top Party (Seats)", leader["party"], f"{int(leader['total_seats'])} seats")
    kpi(c2, "Top Vote Share", f"{leader['avg_vote_share']:.1f}%")
else:
    kpi(c1, "Top Party (Seats)", "—")
    kpi(c2, "Top Vote Share", "—")
if not sent.empty:
    kpi(c3, "Most Positive (Social)", sent.iloc[0]["party"],
        f"{sent.iloc[0]['positive_pct']:.1f}% positive")
    kpi(c4, "Most Negative (Social)", sent.iloc[-1]["party"],
        f"{sent.iloc[-1]['negative_pct']:.1f}% negative")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Vote Share Trends", "🪑 Seat Trends", "💬 Sentiment", "👤 Candidates"]
)

with tab1:
    if vs.empty:
        st.info("No data.")
    else:
        if filters["party"]:
            vs = vs[vs["party"] == filters["party"]]
        st.plotly_chart(line_chart(vs, x="election_year", y="vote_share",
                                   color="party",
                                   title="Vote Share (%) Over Years"),
                        use_container_width=True)
        st.plotly_chart(pie_chart(dominance.head(8), names="party",
                                  values="avg_vote_share",
                                  title="Average Vote Share by Party"),
                        use_container_width=True)
        download_button(vs, "⬇️ Download vote-share trends", "vote_share.csv")

with tab2:
    if seats.empty:
        st.info("No data.")
    else:
        if filters["party"]:
            seats = seats[seats["party"] == filters["party"]]
        st.plotly_chart(bar_chart(seats, x="election_year", y="seats_won",
                                  color="party",
                                  title="Seats Won by Election Year"),
                        use_container_width=True)
        st.dataframe(seats, use_container_width=True, hide_index=True)

with tab3:
    if sent.empty:
        st.info("No sentiment data.")
    else:
        st.plotly_chart(bar_chart(sent, x="party", y="net_sentiment",
                                  color="party",
                                  title="Net Sentiment by Party"),
                        use_container_width=True)
        st.dataframe(sent, use_container_width=True, hide_index=True)
        topics = pd.DataFrame(sentiment["trending_topics"])
        if not topics.empty:
            st.subheader("Trending Topics")
            st.plotly_chart(bar_chart(topics, x="topic", y="count",
                                      title="Most-Mentioned Topics"),
                            use_container_width=True)

with tab4:
    strength = pd.DataFrame(top_c["party_strength"])
    if not strength.empty:
        st.subheader("Party-wise Candidate Strength")
        st.plotly_chart(bar_chart(strength, x="party", y="candidates",
                                  color="party",
                                  title="Number of Candidates per Party"),
                        use_container_width=True)
        st.dataframe(strength, use_container_width=True, hide_index=True)

    by_assets = pd.DataFrame(top_c["by_assets"])
    if not by_assets.empty:
        st.subheader("Wealthiest Candidates")
        by_assets["assets_cr"] = (by_assets["assets"] / 1e7).round(2)
        st.dataframe(
            by_assets[["candidate_name", "party", "constituency",
                       "age", "assets_cr", "criminal_cases"]]
            .rename(columns={"assets_cr": "assets (₹ Cr)"}),
            use_container_width=True, hide_index=True,
        )
