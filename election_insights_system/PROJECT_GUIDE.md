# 📘 Project Guide — Election Insights & Monitoring System

This document explains **what** the project does, **how** it is built, and
**every** API endpoint and Streamlit feature it ships with.

> For setup / run instructions, see [README.md](README.md).

---

## 1. Goals

The platform turns raw election-related data into intuitive insights so a
non-technical analyst can:

1. Browse election KPIs at a glance (turnout, voters, leading parties).
2. Monitor anomalies in real time (turnout spikes, NOTA hotspots).
3. Compare parties across years and states.
4. Drill into a single constituency.
5. Read short, plain-language insights generated from the data.

It is intentionally **lightweight**: no database, no Docker, no auth, no
external APIs — just Python, Pandas, FastAPI and Streamlit on local files.

---

## 2. Architecture

```
                ┌─────────────────────────┐
                │   Streamlit UI (8501)   │
                │  Home + 4 sub-pages     │
                └──────────┬──────────────┘
                           │ HTTP (requests)
                           ▼
                ┌─────────────────────────┐
                │  FastAPI Backend (8000) │
                │   routes → services →   │
                │       analytics         │
                └──────────┬──────────────┘
                           │ Pandas
                           ▼
                ┌─────────────────────────┐
                │  data/sample_data/*.csv │
                │     (+ *.json copies)   │
                └─────────────────────────┘
```

**Layered backend:**

- **routes/** — HTTP layer (`health`, `data`, `analytics`). Only parses
  query params and returns JSON.
- **services/** — Orchestrates analytics calls (single source of truth
  used by routes).
- **analytics/** — Pure Pandas/NumPy modules per domain
  (`turnout`, `party`, `candidate`, `sentiment`, `anomalies`, `insights`).
- **data_loader/** — Reads CSVs once and caches them in memory.
- **utils/** — Filter helpers, JSON-safe converters.
- **schemas/** — Pydantic response models.

**Frontend:**

- **Home.py** — Dashboard.
- **pages/** — Streamlit auto-discovers files prefixed with a number,
  creating left-nav entries (Monitoring, Party, Constituency, Insights).
- **api/client.py** — Cached `requests` calls to FastAPI.
- **components/ui.py** — Reusable Plotly charts, KPI cards, CSS, sidebar.

---

## 3. Synthetic data

`scripts/generate_sample_data.py` builds five datasets with realistic
random distributions (seeded for reproducibility, `seed=42`).

### 3.1 `constituencies.csv` (156 rows)

| Column               | Type   | Notes                                   |
| -------------------- | ------ | --------------------------------------- |
| `constituency_id`    | str    | `C0001`…                                |
| `constituency_name`  | str    | `<District>-<n>`                        |
| `state`, `district`  | str    | 10 states × 3–5 districts each          |
| `total_voters`       | int    | ~Normal(1.5M, 350k)                     |
| `male_voters`        | int    | ~48–53% of total                        |
| `female_voters`      | int    | remainder                               |
| `urban_percentage`   | float  | 20–95%                                  |
| `rural_percentage`   | float  | 100 − urban                             |

### 3.2 `candidates.csv` (780 rows)

| Column            | Type | Notes                                    |
| ----------------- | ---- | ---------------------------------------- |
| `candidate_id`    | str  | `K00001`…                                |
| `candidate_name`  | str  | random first + last name                 |
| `party`           | str  | 5 per constituency, from 9-party pool    |
| `constituency`    | str  | matches `constituency_name`              |
| `age`             | int  | ~Normal(52, 11) clipped to [25, 85]      |
| `education`       | str  | weighted across 5 levels                 |
| `criminal_cases`  | int  | skewed; ~45% have 0                      |
| `assets`          | int  | lognormal, ₹1L – ₹100Cr                  |
| `incumbency`      | bool | ~18% true                                |

### 3.3 `voting_data.csv` (5,460 rows)

35 polling booths per constituency. Each row:

| Column                 | Notes                                                        |
| ---------------------- | ------------------------------------------------------------ |
| `constituency`         | matches `constituency_name`                                  |
| `polling_booth`        | `C0001-B001`…                                                |
| `votes_cast`           | int                                                          |
| `turnout_percentage`   | float — baseline per-constituency with engineered spikes/dips for anomaly detection |
| `NOTA_votes`           | int (0.5%–6% of votes_cast)                                  |
| `timestamp`            | ISO datetime within polling day                              |

### 3.4 `party_performance.csv` (270 rows)

| Column          | Notes                                |
| --------------- | ------------------------------------ |
| `party`         | 9-party pool                         |
| `seats_won`     | Dirichlet-distributed across parties |
| `vote_share`    | matches seat distribution            |
| `state`         | 10 states                            |
| `election_year` | 2014, 2019, 2024                     |

### 3.5 `social_sentiment.csv` (540 rows)

60 days × 9 parties.

| Column                | Notes                                  |
| --------------------- | -------------------------------------- |
| `date`                | YYYY-MM-DD                             |
| `party`               | 9-party pool                           |
| `positive_mentions`   | int                                    |
| `negative_mentions`   | int                                    |
| `neutral_mentions`    | int                                    |
| `trending_topics`     | comma-separated tags                   |

---

## 4. FastAPI Backend — every endpoint

Base URL: `http://127.0.0.1:8000`
Interactive docs: `/docs` (Swagger) and `/redoc`.

### 4.1 Health

#### `GET /health`
Reports backend status and row counts per dataset.

```json
{
  "status": "ok",
  "datasets": {
    "constituencies": 156,
    "candidates": 780,
    "voting_data": 5460,
    "party_performance": 270,
    "social_sentiment": 540
  }
}
```

If a CSV is missing, status becomes `"degraded"` and the count is `0`.

### 4.2 Data endpoints

All data endpoints respond with:

```json
{ "count": <int>, "records": [ {...}, ... ] }
```

#### `GET /constituencies`
Returns the constituency master list.

**Query:** `state` (optional).

#### `GET /candidates`
Returns candidates.

**Query:** `party`, `constituency` (both optional).

#### `GET /voting-data`
Returns booth-level voting rows.

**Query:**
- `constituency` (optional)
- `limit` — default 500, max 20 000

#### `GET /party-performance`
Returns party seats & vote share per state/year.

**Query:** `state`, `party`, `election_year` (all optional).

### 4.3 Analytics endpoints — `/analytics/*`

#### `GET /analytics/turnout`
**Query:** `state` (optional).

Returns four sections:
- `overview`: avg / median / min / max turnout, booth count, and a per-state breakdown.
- `top_states`: top-5 states by average turnout.
- `low_turnout_regions`: constituencies below 50% threshold.
- `by_constituency`: avg turnout, total votes, total NOTA per constituency.

#### `GET /analytics/party-trends`
**Query:** `state`, `election_year` (optional).

Returns:
- `vote_share_trends` — list of `{election_year, party, vote_share}`.
- `seat_trends` — same shape but with `seats_won`.
- `party_dominance` — total seats and avg vote share per party.
- `leading_parties_by_state` — top-seat party per state.

#### `GET /analytics/top-candidates`
**Query:** `n` (1–100, default 10), `party` (optional).

Returns:
- `by_assets` — top-N richest candidates.
- `criminal_summary` — per-party totals and % with cases.
- `age_distribution` — buckets `<30, 30-40, …, 70+`.
- `party_strength` — candidate count / avg age / avg assets per party.

#### `GET /analytics/anomalies`
No query parameters.

Returns:
- `anomalies`: each item has `type` ∈ {`turnout_spike`, `turnout_dip`, `high_nota`},
  `constituency`, `state`, `value`, `threshold`, `detail`.
  Spikes/dips use **µ ± 2σ** within each constituency. High NOTA is > 5%.
- `risk_scores`: per-constituency composite risk (0–100) combining
  low turnout + turnout volatility + NOTA share.

#### `GET /analytics/insights`
Returns rule-based narrative insights:

```json
{
  "insights": [
    {
      "category": "Turnout",
      "severity": "info" | "warning" | "critical",
      "title": "...",
      "detail": "...",
      "metrics": { ... }
    }
  ]
}
```

Categories produced: **Turnout**, **NOTA**, **Party**, **Sentiment**, **Candidate**.

Rules (high level):

- State turnout leader / laggard vs national average.
- Urban vs rural turnout gap.
- Highest-NOTA constituency.
- Party gainers / losers between the two most recent election years.
- Sentiment leader / heavy-negative party.
- Wealthiest candidate; candidates with ≥ 5 criminal cases.

#### `GET /analytics/sentiment`
Returns:
- `summary` — per-party totals, positive %, negative %, net sentiment.
- `trending_topics` — top topics with counts.

### 4.4 Error contract

- **503** — sample data not generated yet (the loader raises `DataNotFoundError`).
- **422** — invalid query params (FastAPI default validation).
- **200** — normal response.

---

## 5. Streamlit Frontend — every page

Sidebar (shared across all pages):
- **State**, **Constituency**, **Party**, **Election Year** dropdowns.
- **🔄 Refresh data** button — clears the Streamlit cache and reruns.

API responses are cached for 60 seconds per query via `@st.cache_data`.

### 5.1 🏠 Home / Dashboard — `frontend/Home.py`

**Sections:**

1. **Header & health badge** — shows whether the backend is reachable.
2. **KPI row (5 cards):** Constituencies · Total Voters · Avg Turnout ·
   Polling Booths · Leading Party (with seat count).
3. **State-wise turnout bar chart** (Plotly).
4. **Party vote-share donut** (top 8 parties).
5. **Vote-share line chart** by party across election years.
6. **Heatmap** of seats won (year × party).
7. **Table** of the leading party in each state.

### 5.2 🚨 Monitoring — `pages/1_🚨_Monitoring.py`

Pulls `/analytics/anomalies`.

**Sections:**

1. **KPI row:** Total Anomalies · Turnout Spikes · Turnout Dips · High-NOTA Booths.
2. **Tabs:**
   - **Anomalies** — full sortable table with CSV download.
   - **Risk Scores** — horizontal bar of top-20 risky constituencies + table + CSV download.
   - **Highlights** — short narrative call-outs (sharpest spike, highest NOTA, riskiest constituency).

Filters (`state`, `constituency`) are applied client-side to the anomaly / risk frames.

### 5.3 🏛️ Party Analysis — `pages/2_🏛️_Party_Analysis.py`

Pulls `/analytics/party-trends`, `/analytics/sentiment`, `/analytics/top-candidates`.

**Sections:**

1. **KPI row:** top party by seats, top vote share, most-positive party, most-negative party.
2. **Tabs:**
   - **Vote Share Trends** — line chart over years + donut of avg share + CSV download.
   - **Seat Trends** — grouped bar by year + table.
   - **Sentiment** — net-sentiment bar + raw table + trending-topics bar.
   - **Candidates** — candidate count by party + wealthiest candidates (assets shown in ₹ Crore).

### 5.4 🗺️ Constituency Analysis — `pages/3_🗺️_Constituency_Analysis.py`

Pulls `/analytics/turnout`, `/voting-data`, `/candidates`.

**Sections:**

1. **KPI row:** count · avg turnout · total votes · total NOTA (filtered).
2. **Top 10 / Bottom 10 turnout** horizontal bars side-by-side.
3. **Deep dive** for the selected constituency (defaults to first row):
   - **Booth-level turnout trend** (line chart by timestamp).
   - **Expander** with raw booth data + CSV download.
   - **Candidates table** for that constituency.
   - **Asset distribution donut** by party.

### 5.5 💡 Insights — `pages/4_💡_Insights.py`

Pulls `/analytics/insights`.

**Sections:**

1. **Multiselect filters:** severity (info/warning/critical) and category.
2. **Insight cards** with colour-coded left borders:
   - 🟦 blue / info
   - 🟧 orange / warning
   - 🟥 red / critical
3. **Raw JSON** expander for debugging.
4. **CSV download** of all insights.

---

## 6. Reusable frontend helpers — `frontend/components/ui.py`

| Helper                       | Purpose                                              |
| ---------------------------- | ---------------------------------------------------- |
| `inject_css()`               | Adds custom KPI + insight-card CSS                   |
| `kpi(col, label, value, …)`  | Renders a coloured KPI card in a Streamlit column    |
| `insight_card(item)`         | Renders a single insight with severity styling       |
| `bar_chart`, `line_chart`,   | Thin Plotly wrappers with a consistent palette &     |
| `pie_chart`, `heatmap`       | margins                                              |
| `download_button(df, …)`     | Streamlit CSV download                               |
| `sidebar_filters(...)`       | Shared filter widget that returns a dict             |

Palette: `plotly.express.colors.qualitative.Set2`.

---

## 7. Bonus features delivered

- ✅ **CSV export** on Monitoring, Party, Constituency, and Insights pages.
- ✅ **Election risk score** (`/analytics/anomalies` → `risk_scores`).
- ✅ **Constituency ranking** (turnout top/bottom, risk-score top-20).
- ✅ **Comparative party analysis** (year-over-year vote-share deltas in insights).
- ✅ **Trend scoring** (sentiment net score, vote-share delta).
- ✅ **Refresh button** (manual auto-refresh, plus 60 s cache TTL).

---

## 8. Operational notes

- **Reproducibility:** RNG is seeded (`SEED=42`) in the data generator.
- **Caching:**
  - Backend: `loader.get(name)` caches a DataFrame the first time it’s read; call `loader.reload()` to drop the cache (e.g. after regenerating CSVs while the server is running).
  - Frontend: each `client.*` function uses `@st.cache_data(ttl=60)`; the sidebar Refresh button clears it.
- **Concurrency:** loader is guarded with a `threading.Lock`.
- **Errors:** `DataNotFoundError` → HTTP 503; everything else propagates as 500.
- **Environment override:** set `ELECTION_API_BASE=http://host:port` to point the frontend at a different backend.

---

## 9. Extending — patterns

### Add a new analytics endpoint

1. Add a Pandas function in `backend/analytics/<domain>.py`.
2. Expose it through `backend/services/election_service.py`.
3. Add a route in `backend/routes/analytics.py`.
4. Add a cached client function in `frontend/api/client.py`.
5. Consume it from a page in `frontend/pages/`.

### Swap insights for ML

`backend/analytics/insights.py` returns a list of dict items. Replace its
internals (e.g. clustering, anomaly model, classifier) — the contract
(`category`, `severity`, `title`, `detail`, `metrics`) stays the same, so
no frontend changes are needed.

### Use real data

Drop real CSVs into `data/sample_data/` matching the schemas in
section 3, then restart the backend (or call `loader.reload()`).

---

## 10. File-by-file map

| File                                            | Role                                       |
| ----------------------------------------------- | ------------------------------------------ |
| `scripts/generate_sample_data.py`               | Build all CSV + JSON datasets              |
| `backend/app.py`                                | FastAPI app + CORS + router registration   |
| `backend/routes/health.py`                      | `/health`                                  |
| `backend/routes/data.py`                        | `/constituencies`, `/candidates`, `/voting-data`, `/party-performance` |
| `backend/routes/analytics.py`                   | All `/analytics/*` endpoints               |
| `backend/services/election_service.py`          | Orchestrates analytics + data calls        |
| `backend/analytics/turnout.py`                  | Turnout aggregates                         |
| `backend/analytics/party.py`                    | Vote-share / seat trends                   |
| `backend/analytics/candidate.py`                | Candidate stats                            |
| `backend/analytics/sentiment.py`                | Social sentiment aggregates                |
| `backend/analytics/anomalies.py`                | µ±2σ anomalies + risk score                |
| `backend/analytics/insights.py`                 | Rule-based narrative generator             |
| `backend/data_loader/loader.py`                 | Cached CSV loader                          |
| `backend/utils/helpers.py`                      | `df_to_records`, `filter_df`               |
| `backend/schemas/models.py`                     | Pydantic response models                   |
| `frontend/Home.py`                              | Dashboard                                  |
| `frontend/pages/1_🚨_Monitoring.py`             | Monitoring page                            |
| `frontend/pages/2_🏛️_Party_Analysis.py`         | Party analysis page                        |
| `frontend/pages/3_🗺️_Constituency_Analysis.py`  | Constituency analysis page                 |
| `frontend/pages/4_💡_Insights.py`               | Insights page                              |
| `frontend/api/client.py`                        | Cached HTTP client to FastAPI              |
| `frontend/components/ui.py`                     | KPI cards, charts, sidebar, CSS            |

---

## 11. Testing the backend manually

```bash
# Health
curl http://127.0.0.1:8000/health

# Filtered data
curl "http://127.0.0.1:8000/candidates?party=BJP"
curl "http://127.0.0.1:8000/voting-data?limit=5"

# Analytics
curl "http://127.0.0.1:8000/analytics/turnout?state=Karnataka"
curl "http://127.0.0.1:8000/analytics/party-trends?election_year=2024"
curl "http://127.0.0.1:8000/analytics/top-candidates?n=5"
curl "http://127.0.0.1:8000/analytics/anomalies"
curl "http://127.0.0.1:8000/analytics/insights"
curl "http://127.0.0.1:8000/analytics/sentiment"
```

Or just open **http://127.0.0.1:8000/docs** and click through Swagger.

---

That’s the whole system end-to-end. Happy exploring! 🗳️
