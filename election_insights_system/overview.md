# Election Monitoring & Analytics System

## Overview

This system is a Streamlit + FastAPI based Election Analytics Dashboard.

It transforms election-related data into:
- simple insights
- visual analytics
- monitoring dashboards
- constituency analysis
- party trends
- election risk indicators

The frontend is built using Streamlit and communicates with backend APIs built using FastAPI.

---

# 5.2 🚨 Monitoring Page

File:
`pages/1_🚨_Monitoring.py`

## Purpose

This page is used to monitor suspicious election activities and identify risky constituencies.

## API Used

- `/analytics/anomalies`

---

## Features

### KPI Cards

Displays quick statistics:
- Total anomalies
- Turnout spikes
- Turnout dips
- High NOTA booths

---

## Tabs

### 1. Anomalies Tab

Shows:
- suspicious turnout records
- unusual voting patterns
- anomaly tables

Features:
- sorting
- filtering
- CSV download

---

### 2. Risk Scores Tab

Displays:
- Top 20 risky constituencies
- Horizontal bar chart
- Risk score table
- CSV export

---

### 3. Highlights Tab

Provides short insight summaries:
- highest NOTA area
- biggest turnout spike
- riskiest constituency

---

## Filters

Client-side filters:
- state
- constituency

These filters are applied without recalling APIs.

---

# 5.3 🏛️ Party Analysis Page

File:
`pages/2_🏛️_Party_Analysis.py`

## Purpose

Analyzes political party performance, vote trends, sentiment, and candidates.

---

## APIs Used

- `/analytics/party-trends`
- `/analytics/sentiment`
- `/analytics/top-candidates`

---

## Features

### KPI Cards

Displays:
- top party by seats
- highest vote share
- most positive party
- most negative party

---

## Tabs

### 1. Vote Share Trends

Displays:
- line chart of vote share over years
- average vote share donut chart
- CSV export

Purpose:
Track party popularity trends.

---

### 2. Seat Trends

Displays:
- grouped bar chart
- seats won year-wise
- comparison tables

Purpose:
Compare election performance between parties.

---

### 3. Sentiment

Displays:
- sentiment scores
- positive vs negative party mentions
- trending political topics

Purpose:
Analyze public opinion about parties.

---

### 4. Candidates

Displays:
- candidate count by party
- wealthiest candidates
- assets shown in ₹ Crore

Purpose:
Analyze candidate strength and wealth.

---

# 5.4 🗺️ Constituency Analysis Page

File:
`pages/3_🗺️_Constituency_Analysis.py`

## Purpose

Provides detailed constituency-level election analysis.

---

## APIs Used

- `/analytics/turnout`
- `/voting-data`
- `/candidates`

---

## Features

### KPI Cards

Displays:
- constituency count
- average turnout
- total votes
- total NOTA votes

---

## Turnout Rankings

Displays:
- Top 10 turnout constituencies
- Bottom 10 turnout constituencies

Charts:
- horizontal bar charts

Purpose:
Identify high and low voter participation areas.

---

## Constituency Deep Dive

User selects a constituency.

The page then displays:

### Booth-Level Turnout Trend

Line chart showing turnout activity over time.

---

### Raw Booth Data

Inside an expandable section:
- booth-wise table
- CSV download

---

### Candidates Table

Displays all candidates from the selected constituency.

---

### Asset Distribution Donut

Shows party-wise asset distribution.

Purpose:
Compare financial strength of parties.

---

# 5.5 💡 Insights Page

File:
`pages/4_💡_Insights.py`

## Purpose

Displays AI-style election insights and alerts.

---

## API Used

- `/analytics/insights`

---

## Features

### Filters

Users can filter insights by:
- severity
- category

Severity levels:
- info
- warning
- critical

---

## Insight Cards

Displays insights using color-coded cards.

Colors:
- 🟦 Blue → Info
- 🟧 Orange → Warning
- 🟥 Red → Critical

Each card contains:
- title
- details
- metrics

---

## Raw JSON Expander

Displays raw API response for debugging.

---

## CSV Export

Allows downloading all insights.

---

# 6. Reusable Frontend Helpers

File:
`frontend/components/ui.py`

## Purpose

Contains reusable UI helper functions used across all Streamlit pages.

---

## Helper Functions

| Helper Function | Purpose |
|---|---|
| `inject_css()` | Adds custom styling |
| `kpi()` | Creates KPI cards |
| `insight_card()` | Renders styled insight cards |
| `bar_chart()` | Creates bar charts |
| `line_chart()` | Creates line charts |
| `pie_chart()` | Creates pie/donut charts |
| `heatmap()` | Creates heatmaps |
| `download_button()` | CSV download support |
| `sidebar_filters()` | Shared sidebar filters |

---

## Chart Palette

Uses:
`plotly.express.colors.qualitative.Set2`

Purpose:
Maintain consistent chart styling.

---

# 7. Bonus Features

## ✅ CSV Export

Available on:
- Monitoring page
- Party Analysis page
- Constituency page
- Insights page

---

## ✅ Election Risk Score

Risk scores are generated using:
`/analytics/anomalies`

---

## ✅ Constituency Ranking

Provides:
- top turnout areas
- low turnout areas
- risky constituencies

---

## ✅ Comparative Party Analysis

Supports:
- year-over-year vote-share comparison

---

## ✅ Trend Scoring

Calculates:
- sentiment score
- vote-share growth/decline

---

## ✅ Refresh Button

Frontend supports:
- manual refresh
- auto refresh every 60 seconds

---

# 8. Operational Notes

## Reproducibility

Random data generation uses:
`SEED = 42`

Purpose:
Generate consistent sample data.

---

## Backend Caching

`loader.get(name)`
- loads CSV once
- caches DataFrame

`loader.reload()`
- clears cache
- reloads updated CSV files

---

## Frontend Caching

Uses:
`@st.cache_data(ttl=60)`

Purpose:
Reduce unnecessary API calls.

---

## Concurrency

Uses:
`threading.Lock`

Purpose:
Avoid cache conflicts between threads.

---

## Error Handling

| Error | Response |
|---|---|
| Missing data | HTTP 503 |
| Other failures | HTTP 500 |

---

## Environment Override

Frontend backend URL can be changed using:

```bash
ELECTION_API_BASE=http://host:port
```

---

# 9. Extension Patterns

## Add New Analytics Endpoint

Steps:

1. Add analytics logic in:
```bash
backend/analytics/
```

2. Add service function:
```bash
backend/services/election_service.py
```

3. Add API route:
```bash
backend/routes/analytics.py
```

4. Add frontend API client:
```bash
frontend/api/client.py
```

5. Use it in Streamlit page:
```bash
frontend/pages/
```

---

# Replace Insights with ML Models

Current implementation:
- rule-based insights

Can be replaced with:
- anomaly detection
- clustering
- ML classifiers
- AI-generated insights

Important:
Frontend will continue working because the response structure remains the same.

Expected insight structure:
```json
{
  "category": "",
  "severity": "",
  "title": "",
  "detail": "",
  "metrics": {}
}
```

---

# Tech Stack

## Backend
- Python
- FastAPI
- Pandas

## Frontend
- Streamlit
- Plotly

## Data
- CSV-based sample datasets

---

# Key Advantages

- Lightweight architecture
- No database required
- Easy to extend
- Fast dashboard rendering
- Modular backend
- Reusable frontend components
- CSV export support
- AI-ready insight pipeline

---