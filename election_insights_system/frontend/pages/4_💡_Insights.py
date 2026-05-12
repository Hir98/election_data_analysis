"""Insights page — rule-based narrative insights."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.client import APIError, get_insights  # noqa: E402
from components.ui import inject_css, insight_card  # noqa: E402

st.set_page_config(page_title="Insights", page_icon="💡", layout="wide")
inject_css()
st.title("💡 AI-like Insights")
st.caption("Rule-based narrative insights derived from the data.")

try:
    payload = get_insights()
except APIError as e:
    st.error(str(e))
    st.stop()

items = payload.get("insights", [])
if not items:
    st.info("No insights available. Try regenerating sample data.")
    st.stop()

# Filter by severity
sev_filter = st.multiselect(
    "Filter by severity",
    options=["info", "warning", "critical"],
    default=["info", "warning", "critical"],
)
cat_filter = st.multiselect(
    "Filter by category",
    options=sorted({i["category"] for i in items}),
    default=sorted({i["category"] for i in items}),
)
filtered = [i for i in items
            if i.get("severity") in sev_filter
            and i.get("category") in cat_filter]

st.metric("Insights shown", len(filtered))

for item in filtered:
    insight_card(item)

with st.expander("🔎 Raw insights JSON"):
    st.json(items)

# CSV export
df = pd.DataFrame(items)
if not df.empty:
    st.download_button(
        "⬇️ Download insights CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="insights.csv",
        mime="text/csv",
    )
