"""
Module: api/models/analysis.py
Description: Pydantic models for analysis operations.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ComparisonRequest(BaseModel):
    """Request for before/after comparison."""
    column: Optional[str] = None  # If None, compare entire dataset


class ColumnProfile(BaseModel):
    """Profile of a single column."""
    name: str
    pandas_dtype: str
    detected_type: str
    confidence: str
    confidence_score: float
    meta: Dict[str, Any]
    stats: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    is_candidate_drop: bool
    candidate_drop_reason: Optional[str]


class GlobalIssue(BaseModel):
    """Global quality issue."""
    variable: str
    issue: str
    affected_count: int
    affected_pct: float
    severity: str
    action: str
    strategy: str
    justification: str
    status: str


class AnalysisSummary(BaseModel):
    """Summary of dataset analysis."""
    rows: int
    cols: int
    total_cells: int
    total_duplicates: int
    duplicate_pct: float
    total_missing_cells: int
    type_counts: Dict[str, int]
    candidate_drop_columns: List[str]


class AnalysisResults(BaseModel):
    """Complete analysis results."""
    summary: AnalysisSummary
    profiles: Dict[str, ColumnProfile]
    global_issues: List[GlobalIssue]
    correlations: Dict[str, Dict[str, float]]
