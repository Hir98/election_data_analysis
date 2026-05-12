"""Pydantic response models (kept loose for POC flexibility)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    datasets: Dict[str, int]


class InsightItem(BaseModel):
    category: str
    severity: str  # info | warning | critical
    title: str
    detail: str
    metrics: Optional[Dict[str, Any]] = None


class AnomalyItem(BaseModel):
    type: str
    constituency: Optional[str] = None
    state: Optional[str] = None
    value: float
    threshold: float
    detail: str


class GenericRecords(BaseModel):
    count: int
    records: List[Dict[str, Any]]
