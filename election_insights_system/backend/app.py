"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import analytics, data, health

app = FastAPI(
    title="Election Insights & Monitoring API",
    description="POC backend exposing election analytics and rule-based insights.",
    version="1.0.0",
)

# CORS — Streamlit on same machine, but keep permissive for local POC.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(data.router)
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "service": "Election Insights & Monitoring API",
        "docs": "/docs",
        "health": "/health",
    }
