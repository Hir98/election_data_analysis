"""Reusable Streamlit + Plotly UI helpers."""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.express as px
import streamlit as st

# A clean palette used across the app
PALETTE = px.colors.qualitative.Set2

KPI_CSS = """
<style>
.kpi-card {
  background: linear-gradient(135deg,#1f2937 0%,#111827 100%);
  border-radius: 14px;
  padding: 18px 20px;
  color: #f9fafb;
  box-shadow: 0 4px 14px rgba(0,0,0,0.18);
  border: 1px solid rgba(255,255,255,0.06);
}
.kpi-card .label {font-size:0.85rem; opacity:0.75; text-transform:uppercase; letter-spacing:0.05em;}
.kpi-card .value {font-size:1.8rem; font-weight:700; margin-top:4px;}
.kpi-card .delta {font-size:0.8rem; margin-top:6px; opacity:0.85;}
.insight-card {
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  border-left: 6px solid #6366f1;
  background: #f8fafc;
  color: #0f172a;
}
.insight-card.warning {border-left-color: #f59e0b; background: #fffbeb;}
.insight-card.critical {border-left-color: #ef4444; background: #fef2f2;}
.insight-card .title {font-weight:700; margin-bottom:4px;}
.insight-card .cat {font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; opacity:0.6;}
</style>
"""


def inject_css() -> None:
    st.markdown(KPI_CSS, unsafe_allow_html=True)


def kpi(col, label: str, value: str, delta: str | None = None) -> None:
    delta_html = f'<div class="delta">{delta}</div>' if delta else ""
    col.markdown(
        f"""
        <div class="kpi-card">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
          {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(item: dict) -> None:
    sev = (item.get("severity") or "info").lower()
    cls = "insight-card"
    if sev in ("warning", "critical"):
        cls += f" {sev}"
    st.markdown(
        f"""
        <div class="{cls}">
          <div class="cat">{item.get('category', '')} • {sev}</div>
          <div class="title">{item.get('title', '')}</div>
          <div>{item.get('detail', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None,
              title: str = "", orientation: str = "v"):
    fig = px.bar(df, x=x, y=y, color=color, title=title,
                 orientation=orientation, color_discrete_sequence=PALETTE)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None,
               title: str = ""):
    fig = px.line(df, x=x, y=y, color=color, title=title, markers=True,
                  color_discrete_sequence=PALETTE)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
    return fig


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str = ""):
    fig = px.pie(df, names=names, values=values, title=title, hole=0.45,
                 color_discrete_sequence=PALETTE)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
    return fig


def heatmap(df: pd.DataFrame, x: str, y: str, z: str, title: str = ""):
    pivot = df.pivot_table(index=y, columns=x, values=z, aggfunc="mean")
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="Viridis",
                    title=title)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=420)
    return fig


def download_button(df: pd.DataFrame, label: str, filename: str) -> None:
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def sidebar_filters(records_constituencies: Iterable[dict],
                    records_parties: Iterable[str],
                    election_years: Iterable[int]) -> dict:
    """Render the common sidebar filters and return the selections."""
    st.sidebar.header("🔍 Filters")
    states = sorted({r["state"] for r in records_constituencies if r.get("state")})
    state = st.sidebar.selectbox("State", ["All"] + states, index=0)

    constituencies = sorted({
        r["constituency_name"] for r in records_constituencies
        if (state == "All" or r.get("state") == state)
    })
    constituency = st.sidebar.selectbox("Constituency", ["All"] + constituencies, index=0)

    parties = sorted({p for p in records_parties if p})
    party = st.sidebar.selectbox("Party", ["All"] + parties, index=0)

    years = sorted({int(y) for y in election_years if y})
    year_opts = ["All"] + [str(y) for y in years]
    year_sel = st.sidebar.selectbox("Election Year", year_opts, index=0)

    if st.sidebar.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

    return {
        "state": None if state == "All" else state,
        "constituency": None if constituency == "All" else constituency,
        "party": None if party == "All" else party,
        "election_year": None if year_sel == "All" else int(year_sel),
    }
