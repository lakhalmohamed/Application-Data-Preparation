"""
Module: api/models/dataset.py
Description: Pydantic models for dataset operations.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any


class DatasetMetadata(BaseModel):
    """Metadata for loaded dataset."""
    file_name: str
    file_path: str
    file_size_bytes: int
    file_size_formatted: str
    format: str
    extension: str
    encoding: str
    delimiter: str
    decimal: str
    rows: int
    cols: int
    columns: list
    dtypes: Dict[str, str]
    memory_bytes: int
    memory_formatted: str
    total_missing: int
    missing_pct: float
    duplicate_rows: int
    duplicate_pct: float


class DatasetPreviewRequest(BaseModel):
    """Request for dataset preview."""
    page: int = 0
    page_size: int = 50


class DatasetPreviewResponse(BaseModel):
    """Response for dataset preview."""
    data: list
    columns: list
    total_rows: int
    page: int
    page_size: int
    total_pages: int


class CSVParameters(BaseModel):
    """CSV loading parameters."""
    delimiter: Optional[str] = None
    encoding: Optional[str] = None
    decimal: Optional[str] = None


class TargetSelectionRequest(BaseModel):
    """Request for target variable selection."""
    target_column: str
    learning_mode: str = "supervised"  # supervised or unsupervised
