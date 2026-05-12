# 🗳️ Election Insights & Monitoring System

A lightweight, platform that transforms raw (synthetic) election
data into intuitive insights, dashboards, and monitoring views.

**Tech stack**

| Layer            | Tool                          |
| ---------------- | ----------------------------- |
| Backend API      | FastAPI + Uvicorn             |
| Frontend UI      | Streamlit (multi-page)        |
| Data Processing  | Pandas, NumPy                 |
| Visualization    | Plotly                        |
| Storage          | Local CSV / JSON (no DB)      |
| Insights Engine  | Rule-based (no LLM)           |

> See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for a deep-dive into architecture,
> every API endpoint, and every Streamlit page.

---

## 📁 Project Structure

```
election_insights_system/
├── backend/
│   ├── app.py                    # FastAPI entry point
│   ├── routes/                   # health, data, analytics routers
│   ├── services/                 # Business-logic layer
│   ├── analytics/                # turnout, party, candidate, sentiment, anomalies, insights
│   ├── utils/                    # Shared helpers
│   ├── schemas/                  # Pydantic models
│   └── data_loader/              # Cached CSV loader
├── frontend/
│   ├── Home.py                   # Dashboard (entry page)
│   ├── pages/                    # Monitoring, Party, Constituency, Insights
│   ├── api/client.py             # Talks to FastAPI
│   └── components/ui.py          # KPI cards, charts, sidebar filters
├── data/sample_data/             # Generated CSV + JSON
├── scripts/
│   └── generate_sample_data.py   # Synthetic dataset generator
├── requirements.txt
├── run.sh                        # Convenience launcher (bash)
├── README.md                     # ← you are here
└── PROJECT_GUIDE.md              # Full explanation
```

---

## ✅ Prerequisites

- Python **3.10+** (tested on 3.12)
- pip
- (Optional) a virtual environment

---

## 🚀 Setup

### 1. Open the project

```powershell
cd d:\demoaiml\election_insights_system
```

### 2. (Recommended) Create a virtual environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🧪 Generate sample data

The repo ships **without** the CSV/JSON files. Generate them once:

```bash
python scripts/generate_sample_data.py
```

This writes to `data/sample_data/` and produces **5,000+** rows across:

| File                          | Rows  | Description                       |
| ----------------------------- | ----- | --------------------------------- |
| `constituencies.csv/json`     | 156   | Constituency master data          |
| `candidates.csv/json`         | 780   | Candidates per constituency       |
| `voting_data.csv/json`        | 5,460 | Booth-level voting (>= 5000)      |
| `party_performance.csv/json`  | 270   | Party seats / vote share by year  |
| `social_sentiment.csv/json`   | 540   | Daily party sentiment buzz        |

Re-run the script any time to refresh the data.

---

## ▶️ Run the system

You need **two** terminals (one for backend, one for frontend).

### Terminal 1 — Backend (FastAPI)

```bash
uvicorn backend.app:app --reload
```

- API base URL: **http://127.0.0.1:8000**
- Swagger UI:   **http://127.0.0.1:8000/docs**
- ReDoc:        **http://127.0.0.1:8000/redoc**

### Terminal 2 — Frontend (Streamlit)

```bash
streamlit run frontend/Home.py
```

- Opens in your browser at **http://localhost:8501**

> The Streamlit app calls the FastAPI backend at `http://127.0.0.1:8000`.
> Override with the `ELECTION_API_BASE` environment variable if needed.

---

## ⚡ One-shot launch (Linux/macOS or Git Bash)

```bash
bash run.sh
```

This regenerates data, starts the backend in the background, then
launches Streamlit in the foreground.

---

## 🔌 API quick reference

**Data**

- `GET /constituencies`
- `GET /candidates`
- `GET /voting-data`
- `GET /party-performance`

**Analytics**

- `GET /analytics/turnout`
- `GET /analytics/party-trends`
- `GET /analytics/top-candidates`
- `GET /analytics/anomalies`
- `GET /analytics/insights`
- `GET /analytics/sentiment`

**Health**

- `GET /health`

Most endpoints accept query filters (`state`, `party`, `constituency`,
`election_year`). See [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for full details.

---

## 🖥️ Streamlit pages

| Page                          | What it shows                                          |
| ----------------------------- | ------------------------------------------------------ |
| 🏠 **Home / Dashboard**       | KPIs, state turnout bar, vote-share pie, trend line, heatmap |
| 🚨 **Monitoring**             | Anomalies, NOTA hotspots, risk-score ranking           |
| 🏛️ **Party Analysis**         | Vote-share trends, seats, sentiment, candidate strength |
| 🗺️ **Constituency Analysis**  | Top/bottom turnout, booth trend, candidate roster      |
| 💡 **Insights**               | Rule-based narrative insights with severity filters    |

All pages share a sidebar with filters: **State**, **Party**,
**Constituency**, **Election Year**, plus a **Refresh** button.

---

## 🧯 Troubleshooting

| Issue                                              | Fix                                                                 |
| -------------------------------------------------- | ------------------------------------------------------------------- |
| `503 Missing dataset ...` from API                 | Run `python scripts/generate_sample_data.py`                        |
| Streamlit shows "Cannot reach API"                 | Make sure backend is running on port 8000                           |
| Stale data in UI after regenerating CSVs           | Click **🔄 Refresh data** in the sidebar (clears Streamlit cache)   |
| Port already in use                                | `uvicorn backend.app:app --reload --port 8001` and set `ELECTION_API_BASE=http://127.0.0.1:8001` |
| `ModuleNotFoundError: backend`                     | Run uvicorn from the project root (`election_insights_system/`)     |

---

## 🧩 Extending the project

- **Add a new metric** — write a Pandas function in `backend/analytics/`,
  wire it through `backend/services/election_service.py`, expose it in a
  route, and consume it via `frontend/api/client.py`.
- **Swap insights for an ML model** — replace `backend/analytics/insights.py`;
  the rest of the stack is agnostic.
- **Plug real data** — drop CSVs with the same schema into
  `data/sample_data/` and call `loader.reload()`.

---

## 📜 License

