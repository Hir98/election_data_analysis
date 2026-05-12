"""Monitoring page — anomalies, NOTA hotspots, risk scores."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.client import APIError, get_anomalies, get_constituencies, get_party_performance  # noqa: E402
from components.ui import bar_chart, download_button, inject_css, kpi, sidebar_filters  # noqa: E402

st.set_page_config(page_title="Monitoring", page_icon="🚨", layout="wide")
inject_css()
st.title("🚨 Election Monitoring")

try:
    const = get_constituencies()["records"]
    pp = get_party_performance()["records"]
    filters = sidebar_filters(const, {r["party"] for r in pp},
                              {r["election_year"] for r in pp})
    data = get_anomalies()
except APIError as e:
    st.error(str(e))
    st.stop()

anomalies = pd.DataFrame(data["anomalies"])
risk = pd.DataFrame(data["risk_scores"])

if filters["state"] and not anomalies.empty:
    anomalies = anomalies[anomalies["state"] == filters["state"]]
if filters["state"] and not risk.empty:
    risk = risk[risk["state"] == filters["state"]]
if filters["constituency"] and not anomalies.empty:
    anomalies = anomalies[anomalies["constituency"] == filters["constituency"]]
if filters["constituency"] and not risk.empty:
    risk = risk[risk["constituency"] == filters["constituency"]]

# KPIs
c1, c2, c3, c4 = st.columns(4)
counts = anomalies["type"].value_counts() if not anomalies.empty else pd.Series(dtype=int)
kpi(c1, "Total Anomalies", f"{len(anomalies):,}")
kpi(c2, "Turnout Spikes", f"{int(counts.get('turnout_spike', 0)):,}")
kpi(c3, "Turnout Dips", f"{int(counts.get('turnout_dip', 0)):,}")
kpi(c4, "High-NOTA Booths", f"{int(counts.get('high_nota', 0)):,}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["⚠️ Anomalies", "📊 Risk Scores", "🧭 Highlights"])

with tab1:
    if anomalies.empty:
        st.info("No anomalies detected for current filters.")
    else:
        st.dataframe(anomalies, use_container_width=True, hide_index=True)
        download_button(anomalies, "⬇️ Download anomalies CSV", "anomalies.csv")

with tab2:
    if risk.empty:
        st.info("No risk data available.")
    else:
        top_risk = risk.head(20)
        st.plotly_chart(
            bar_chart(top_risk, x="risk_score", y="constituency",
                      color="state", title="Top 20 High-Risk Constituencies",
                      orientation="h"),
            use_container_width=True,
        )
        st.dataframe(risk, use_container_width=True, hide_index=True)
        download_button(risk, "⬇️ Download risk scores", "risk_scores.csv")

with tab3:
    st.subheader("Quick Highlights")
    if not anomalies.empty:
        worst_spike = anomalies[anomalies["type"] == "turnout_spike"].nlargest(1, "value")
        if not worst_spike.empty:
            r = worst_spike.iloc[0]
            st.warning(f"🔺 Sharpest spike: **{r['constituency']}** ({r['state']}) "
                       f"— booth turnout {r['value']:.1f}% (threshold {r['threshold']:.1f}%).")
        worst_nota = anomalies[anomalies["type"] == "high_nota"].nlargest(1, "value")
        if not worst_nota.empty:
            r = worst_nota.iloc[0]
            st.warning(f"📢 Highest NOTA: **{r['constituency']}** ({r['state']}) "
                       f"— {r['value']:.2f}% NOTA share.")
    if not risk.empty:
        r = risk.iloc[0]
        st.error(f"🚩 Riskiest constituency: **{r['constituency']}** "
                 f"(score {r['risk_score']:.1f}) — low turnout / NOTA driven.")
