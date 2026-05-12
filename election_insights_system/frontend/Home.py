"""Election Insights & Monitoring — Streamlit Home (Dashboard).

Run:
    streamlit run frontend/Home.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Make sibling packages importable when running `streamlit run frontend/Home.py`
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.client import (  # noqa: E402
    APIError, get_constituencies, get_health, get_party_performance,
    get_party_trends, get_turnout,
)
from components.ui import (  # noqa: E402
    bar_chart, heatmap, inject_css, kpi, line_chart, pie_chart,
    sidebar_filters,
)

st.set_page_config(page_title="Election Insights", page_icon="🗳️",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except APIError as e:
        st.error(str(e))
        st.stop()


def _filter_options():
    const = safe_call(get_constituencies)["records"]
    pp = safe_call(get_party_performance)["records"]
    parties = {r["party"] for r in pp}
    years = {r["election_year"] for r in pp}
    return const, parties, years


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='margin-bottom:0'>🗳️ Election Insights & Monitoring</h1>"
    "<p style='color:#6b7280;margin-top:4px'>"
    "Transforming raw election data into intuitive insights.</p>",
    unsafe_allow_html=True,
)

# Health badge
health = safe_call(get_health)
badge = "🟢 Online" if health.get("status") == "ok" else "🟠 Degraded"
st.caption(f"Backend: {badge} • datasets: {health.get('datasets', {})}")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
const_records, parties, years = _filter_options()
filters = sidebar_filters(const_records, parties, years)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
turnout = safe_call(get_turnout, state=filters["state"])
trends = safe_call(get_party_trends, state=filters["state"],
                   election_year=filters["election_year"])

const_df = pd.DataFrame(const_records)
if filters["state"]:
    const_df = const_df[const_df["state"] == filters["state"]]

dominance = pd.DataFrame(trends["party_dominance"])
total_seats = int(dominance["total_seats"].sum()) if not dominance.empty else 0

k1, k2, k3, k4, k5 = st.columns(5)
kpi(k1, "Constituencies", f"{len(const_df):,}")
kpi(k2, "Total Voters", f"{int(const_df['total_voters'].sum()):,}")
kpi(k3, "Avg Turnout", f"{turnout['overview'].get('avg_turnout', 0):.1f}%")
kpi(k4, "Polling Booths", f"{turnout['overview'].get('n_booths', 0):,}")
leader = dominance.iloc[0]["party"] if not dominance.empty else "—"
kpi(k5, "Leading Party", leader, delta=f"{total_seats} seats")

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
left, right = st.columns([3, 2])

with left:
    by_state = pd.DataFrame(turnout["overview"]["by_state"])
    if not by_state.empty:
        st.subheader("📊 State-wise Turnout")
        st.plotly_chart(bar_chart(by_state, x="state", y="avg_turnout",
                                  title="Average Turnout (%) by State"),
                        use_container_width=True)

with right:
    if not dominance.empty:
        st.subheader("🏛️ Party Vote Share")
        st.plotly_chart(pie_chart(dominance.head(8), names="party",
                                  values="avg_vote_share",
                                  title="Average Vote Share (%)"),
                        use_container_width=True)

# Trend lines
vs = pd.DataFrame(trends["vote_share_trends"])
if not vs.empty:
    st.subheader("📈 Vote Share Trends Across Election Years")
    st.plotly_chart(line_chart(vs, x="election_year", y="vote_share",
                               color="party",
                               title="Vote Share (%) by Party Over Years"),
                    use_container_width=True)

# Heatmap: seats per state per party
seat_trends = pd.DataFrame(trends["seat_trends"])
if not seat_trends.empty:
    st.subheader("🗺️ Seats Won — Heatmap (Year × Party)")
    st.plotly_chart(heatmap(seat_trends, x="election_year", y="party",
                            z="seats_won",
                            title="Seats Won by Party Across Years"),
                    use_container_width=True)

# Leading parties table
leaders = pd.DataFrame(trends["leading_parties_by_state"])
if not leaders.empty:
    st.subheader("🥇 Leading Party in Each State")
    st.dataframe(leaders, use_container_width=True, hide_index=True)

st.caption("Tip: use the sidebar to filter by State / Party / Year. "
           "Navigate to other pages from the left for Monitoring, "
           "Party Analysis, Constituency Analysis and Insights.")
