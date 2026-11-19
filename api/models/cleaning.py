"""
Module: api/models/cleaning.py
Description: Pydantic models for cleaning operations.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ImputationRequest(BaseModel):
    """Request for missing value imputation."""
    column: str
    strategy: str  # mean, median, mode, constant, drop_rows, forward_fill, backward_fill, knn
    fill_value: Optional[Any] = None
    knn_neighbors: int = 5


class OutlierRequest(BaseModel):
    """Request for outlier treatment."""
    column: str
    method: str  # iqr, zscore
    action: str  # clip, nan, drop
    threshold: float = 1.5


class TextCleaningRequest(BaseModel):
    """Request for text cleaning."""
    column: str
    strip: bool = True
    casing: Optional[str] = "lower"  # lower, upper, title, None
    empty_to_nan: bool = True


class DuplicateRemovalRequest(BaseModel):
    """Request for duplicate removal."""
    subset: Optional[List[str]] = None
    keep: str = "first"


class ColumnDropRequest(BaseModel):
    """Request for column dropping."""
    columns: List[str]


class CleaningOperation(BaseModel):
    """Record of a cleaning operation."""
    timestamp: str = ""
    operation: str = ""
    column: str = "[Global]"
    strategy: str = ""
    details: str = ""
    params: Dict[str, Any] = {}


class CleaningHistoryResponse(BaseModel):
    """Response with cleaning history."""
    history: List[CleaningOperation]
    current_rows: int
    current_cols: int
